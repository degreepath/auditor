# mypy: warn_unreachable = False

from pathlib import Path
import multiprocessing
import argparse
import logging
import select
import math
import json
import sys
import os

import dotenv
import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

try:
    from setproctitle import setproctitle, getproctitle  # type: ignore
except ImportError:
    def setproctitle(title: str) -> None:
        pass

    def getproctitle(title: str) -> None:
        pass


# always resolve to the local .env file
dotenv_path = Path(__file__).parent.parent.parent / '.env'
dotenv.load_dotenv(verbose=True, dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))
else:
    logger.warning('SENTRY_DSN not set; skipping')

# we need to import this after dotenv and sentry have loaded
from .audit import main as single  # noqa: F402

PROCTITLE = getproctitle()


def worker(*, area_root: str) -> None:
    pid = os.getpid()
    print(f'[pid={pid}] connect', file=sys.stderr)

    PGHOST = os.environ.get("PGHOST")
    PGDATABASE = os.environ.get("PGDATABASE")
    PGUSER = os.environ.get("PGUSER")

    conn = psycopg2.connect(host=PGHOST, database=PGDATABASE, user=PGUSER)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    print(f'[pid={pid}] connected', file=sys.stderr)

    with conn.cursor() as curs:
        # process any already-existing items
        process_queue(curs=curs, pid=pid, area_root=area_root)

    print(f'[pid={pid}] initial queue emptied', file=sys.stderr)

    with conn.cursor() as curs:
        channel = 'dp_queue_update'
        curs.execute(f"LISTEN {channel};")
        print(f"LISTEN {channel};", file=sys.stderr)
        setproctitle(f'{PROCTITLE} LISTEN')

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
                print(f"NOTIFY: {notify.pid}, channel={notify.channel}, payload={notify.payload!r}", file=sys.stderr)

                process_queue(curs=curs, pid=pid, area_root=area_root)


def process_queue(*, curs: psycopg2.extensions.cursor, pid: int, area_root: str) -> None:
    # loop until the queue is empty
    while True:
        curs.execute('BEGIN;')
        setproctitle(f'{PROCTITLE} BEGIN')

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

        # fetch the next available queued item
        row = curs.fetchone()

        # if there are no more, return to waiting
        if row is None:
            curs.execute('COMMIT;')
            break

        try:
            queue_id, run_id, student_id, area_catalog, area_code, input_data = row
            area_id = area_catalog + '/' + area_code
            area_path = os.path.join(area_root, area_catalog, area_code + '.yaml')

            setproctitle(f'{PROCTITLE} RUN stnum={student_id} code={area_code} catalog={area_catalog}')
            print(f'[pid={pid}, q={queue_id}] begin  {student_id}::{area_id}', file=sys.stderr)

            # run the audit
            single(student_data=json.loads(input_data), area_file=area_path, run_id=run_id)

            # once the audit is done, commit the queue's DELETE
            curs.execute('COMMIT;')

            print(f'[pid={pid}, q={queue_id}] commit {student_id}::{area_id}', file=sys.stderr)

        except Exception as exc:
            # commit the deletion, just so it doesn't endlessly re-run itself
            curs.execute('COMMIT;')

            # record the exception in Sentry for debugging
            sentry_sdk.capture_exception(exc)

            # update the process title
            setproctitle(f'{PROCTITLE} ERROR stnum={student_id} code={area_code} catalog={area_catalog}')

            # log the exception
            print(f'[pid={pid}, q={queue_id}] error  {student_id}::{area_id}', file=sys.stderr)


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

    processes = []
    for _ in range(worker_count):
        p = multiprocessing.Process(target=worker, daemon=True, kwargs=dict(area_root=area_root))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
