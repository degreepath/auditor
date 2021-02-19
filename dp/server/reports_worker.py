import subprocess
import logging
import pathlib
import select

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore

logger = logging.getLogger(__name__)


def reports_wrapper(*, binary_path: pathlib.Path) -> None:
    try:
        worker(binary_path=binary_path)
    except KeyboardInterrupt:
        pass


def worker(*, binary_path: pathlib.Path) -> None:
    logger.info('connect')

    # empty string means "use the environment variables"
    conn = psycopg2.connect('', application_name='degreepath-reports-wrapper')
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    logger.info('connected')

    with conn.cursor() as curs:
        # process any already-existing items
        process_queue(curs=curs, binary_path=binary_path)

    with conn.cursor() as curs:
        channel = 'dp_report_queue_update'
        curs.execute(f"LISTEN {channel};")
        logger.info(f"LISTEN {channel};")

        while True:
            # this was taken from the psycopg2 documentation. I believe that
            # the output is the items from the input that have data, and that
            # the timeout is how long it will wait for there to be data... and
            # that if data shows up beforehand, it will return as soon as
            # there is data.
            if select.select([conn], [], [], 5) == ([], [], []):
                continue

            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                logger.info(f"NOTIFY: {notify.pid}, channel={notify.channel}, payload={notify.payload!r}")

                process_queue(curs=curs, binary_path=binary_path)


def process_queue(*, curs: psycopg2.extensions.cursor, binary_path: pathlib.Path) -> None:
    # loop until the queue is empty
    while True:
        curs.execute('BEGIN;')

        curs.execute('''
            DELETE
            FROM public.queue
            WHERE id = (
                SELECT id
                FROM public.queue_reports
                ORDER BY ts
                    FOR UPDATE
                        SKIP LOCKED
                LIMIT 1
            )
        ''')

        # fetch the next available queued item
        try:
            subprocess.run([binary_path, 'batch', '--to-database'], check=True)

        except Exception as exc:
            # log the exception
            logger.error('error running reports: %s', exc)
