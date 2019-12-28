# mypy: warn_unreachable = False

from pathlib import Path
import multiprocessing
import argparse
import logging
import select
import os

import dotenv
import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

# always resolve to the local .env file
dotenv_path = Path(__file__).parent.parent.parent / '.env'
dotenv.load_dotenv(verbose=True, dotenv_path=dotenv_path)

from .audit import main as single

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))
else:
    logger.warning('SENTRY_DSN not set; skipping')

AREA_ROOT = os.getenv('AREA_ROOT')


def worker() -> None:
    pid = os.getpid()
    print('starting connection', pid)

    conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    with conn.cursor() as curs:
        # process any already-existing items
        process_queue(curs, pid)

    with conn.cursor() as curs:
        # language=PostgreSQL
        curs.execute("LISTEN dp_queue_update;")
        print("Waiting for notifications on channel 'dp_queue_update'")

        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue

            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                print(f"NOTIFY: ${notify.pid}, channel={notify.channel}, payload={notify.payload!r}")

                process_queue(curs, pid)


def process_queue(curs: psycopg2.extensions.cursor, pid: int) -> None:
    while True:
        # language=PostgreSQL
        curs.execute('BEGIN;')

        # language=PostgreSQL
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
            RETURNING id, run, student_id, area_catalog, area_code, input_data::text;
        ''')

        row = curs.fetchone()

        if row is None:
            # language=PostgreSQL
            curs.execute('COMMIT;')
            break

        queue_id, run_id, student_id, area_catalog, area_code, input_data = row

        try:
            assert AREA_ROOT is not None, "The AREA_ROOT environment variable is required"
            area_path = os.path.join(AREA_ROOT, area_catalog, area_code + '.yaml')

            print(f'auditing #{queue_id}, stnum {student_id} against {area_path} with {pid}')
            single(student_data=input_data, run_id=run_id, area_file=area_path)
            # language=PostgreSQL
            curs.execute('COMMIT;')

            print(f'completed #{queue_id}, stnum {student_id} against {area_path} with {pid}')
        except Exception as exc:
            # language=PostgreSQL
            curs.execute('ROLLBACK;')

            sentry_sdk.capture_exception(exc)
            print(f'error during #{queue_id}, stnum {student_id} against {area_catalog}/{area_code} with {pid}')


def main() -> None:
    assert AREA_ROOT is not None, "The AREA_ROOT environment variable is required"

    parser = argparse.ArgumentParser()
    parser.parse_args()

    try:
        worker_count = len(os.sched_getaffinity(0))
    except AttributeError:
        worker_count = multiprocessing.cpu_count()

    processes = []
    for _ in range(worker_count):
        p = multiprocessing.Process(target=worker, daemon=True)
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


if __name__ == '__main__':
    main()
