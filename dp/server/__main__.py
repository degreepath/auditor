# mypy: warn_unreachable = False

from pathlib import Path
import multiprocessing
import argparse
import logging
import select
import math
import json
import os

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

from dp.dotenv import load as load_dotenv
from dp.run import load_area

# always resolve to the local .env file
dotenv_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(filepath=dotenv_path)

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'), traces_sample_rate=0.5)
else:
    logger.warning('SENTRY_DSN not set; skipping')

# we need to import this after dotenv and sentry have loaded
from .audit import audit  # noqa: E402

logformat = "%(asctime)s %(name)s [pid=%(process)d] %(processName)s [%(levelname)s] %(message)s"
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter(logformat))
logger.addHandler(ch)


def wrapper(*, area_root: str) -> None:
    try:
        worker(area_root=area_root)
    except KeyboardInterrupt:
        pass


def worker(*, area_root: str) -> None:
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


def process_queue(*, curs: psycopg2.extensions.cursor, area_root: str) -> None:
    # loop until the queue is empty
    while True:
        with sentry_sdk.start_transaction(op="audit", name="audit") as transaction:
            curs.execute('BEGIN;')

            with transaction.start_child(op="db", description="DELETE FROM queue"):
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
            except Exception:
                curs.execute('COMMIT;')
                break

            area_id = area_catalog + '/' + area_code
            area_path = os.path.join(area_root, area_catalog, area_code + '.yaml')
            try:
                logger.info(f'[q={queue_id}] begin  {student_id}::{area_id}')

                area_spec = load_area(area_path)

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
                    sentry_transaction=transaction,
                )

                # once the audit is done, commit the queue's DELETE
                curs.execute('COMMIT;')

                logger.info(f'[q={queue_id}] commit {student_id}::{area_id}')

            except Exception as exc:
                # commit the deletion, just so it doesn't endlessly re-run itself
                curs.execute('COMMIT;')

                # record the exception in Sentry for debugging
                sentry_sdk.capture_exception(exc)

                # log the exception
                logger.error(f'[q={queue_id}] error  {student_id}::{area_id}')

    logger.info('queue is empty')


def main() -> None:
    area_root = os.getenv('AREA_ROOT')
    assert area_root is not None, "The AREA_ROOT environment variable is required"

    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", "-w", type=int, help="the number of worker processes to spawn")
    args = parser.parse_args()

    if args.workers:
        worker_count = args.workers
    else:
        try:
            # only available on linux
            worker_count = len(os.sched_getaffinity(0))
        except AttributeError:
            worker_count = multiprocessing.cpu_count()

        worker_count = math.floor(worker_count * 0.75)

    logger.info(f"spawning {worker_count:,} worker thread{'s' if worker_count != 1 else ''}")

    processes = []
    for _ in range(worker_count):
        p = multiprocessing.Process(target=wrapper, kwargs=dict(area_root=area_root))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
