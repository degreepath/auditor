# mypy: warn_unreachable = False

import os
import json
from pathlib import Path
import select

import dotenv
import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore

# always resolve to the local .env file
dotenv_path = Path(__file__).parent / '.env'
dotenv.load_dotenv(verbose=True, dotenv_path=dotenv_path)


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
        process_queue(curs)

    with conn.cursor() as curs:
        curs.execute("LISTEN dp_queue_update;")
        print("Waiting for notifications on channel 'dp_queue_update'")

        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue

            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                print(f"NOTIFY: ${notify.pid}, channel={notify.channel}, payload={notify.payload!r}")

                process_queue(curs)


def process_queue(curs: psycopg2.extensions.cursor) -> None:
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
            RETURNING id, student_id, area_catalog, area_code, input_data::text;
        ''')

        row = curs.fetchone()
        print(row)

        # when error, curs.execute('ROLLBACK;')

        if row is None:
            curs.execute('COMMIT;')
            break

        curs.execute('COMMIT;')


def main() -> None:
    import multiprocessing

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
