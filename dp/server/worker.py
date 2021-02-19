import logging
import pathlib
import select
import json

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore

from dp.run import find_area, load_area
from dp.server.audit import audit

logger = logging.getLogger(__name__)


def wrapper(*, area_root: str) -> None:
    try:
        worker(area_root=pathlib.Path(area_root))
    except KeyboardInterrupt:
        pass


def worker(*, area_root: pathlib.Path) -> None:
    logger.info('connect')

    # empty string means "use the environment variables"
    conn = psycopg2.connect('', application_name='degreepath')
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    logger.info('connected')

    with conn.cursor() as curs:
        # process any already-existing items
        process_queue(curs=curs, area_root=area_root)

    with conn.cursor() as curs:
        channel = 'dp_queue_update'
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

                process_queue(curs=curs, area_root=area_root)


def process_queue(*, curs: psycopg2.extensions.cursor, area_root: pathlib.Path) -> None:
    # loop until the queue is empty
    while True:
        curs.execute('BEGIN;')

        curs.execute('''
            DELETE
            FROM public.queue
            WHERE id = (
                SELECT id
                FROM public.queue
                ORDER BY priority DESC, ts
                    FOR UPDATE
                        SKIP LOCKED
                LIMIT 1
            )
            RETURNING id, run, student_id, area_catalog, area_code, input_data::text, expires_at, link_only;
        ''')

        # fetch the next available queued item
        row = curs.fetchone()

        # if there are no more, return to waiting
        if row is None:
            curs.execute('COMMIT;')
            break

        try:
            queue_id, run_id, student_id, area_catalog, area_code, input_data, expires_at, link_only = row
        except ValueError as exc:
            curs.execute('COMMIT;')
            logger.exception('unexpected exception: wrong number of items in tuple from queue table - %s', exc)
            break

        area_id = area_catalog + '/' + area_code
        try:
            logger.info(f'[q={queue_id}] begin  {student_id}::{area_id}')

            catalog_int = int(area_catalog.split('-')[0])

            area_file = find_area(root=area_root, area_catalog=catalog_int, area_code=area_code)
            if not area_file:
                logger.error('could not find area spec for %s at or below catalog %s (%s), under %s', area_code, area_catalog, catalog_int, area_root)
                continue

            area_spec = load_area(area_file)

            # run the audit
            audit(
                curs=curs,
                student=json.loads(input_data),
                area_spec=area_spec,
                area_catalog=area_catalog,
                area_code=area_code,
                run_id=run_id,
                expires_at=expires_at,
                link_only=link_only,
            )

            # once the audit is done, commit the queue's DELETE
            curs.execute('COMMIT;')

            logger.info(f'[q={queue_id}] commit {student_id}::{area_id}')

        except Exception as exc:
            # commit the deletion, just so it doesn't endlessly re-run itself
            curs.execute('COMMIT;')

            # log the exception
            logger.error(f'[q={queue_id}] error  {student_id}::{area_id}; %s', exc)

    logger.info('queue is empty')
