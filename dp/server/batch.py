from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Iterator, Dict, Tuple, cast
from pathlib import Path
import argparse
import json
import os

import tqdm  # type: ignore
import urllib3  # type: ignore
import psycopg2  # type: ignore
import sentry_sdk  # type: ignore
import dotenv

from dp.bin.expand import expand_student

# always resolve to the local .env file
dotenv_path = Path(__file__).parent.parent.parent / '.env'
dotenv.load_dotenv(verbose=True, dotenv_path=dotenv_path)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))

http = urllib3.PoolManager()
DISABLED = {('161932', '456'), ('163749', '456')}

BATCH_URL = os.getenv('DP_BATCH_URL')
SINGLE_URL = os.getenv('DP_SINGLE_URL')


def fetch(stnum: str) -> Tuple[Dict, str]:
    r = http.request('GET', SINGLE_URL, fields={'stnum': stnum})
    text = r.data.decode('utf-8')
    return cast(Dict, json.loads(text)), text


def batch() -> Iterator[Tuple[Dict, str]]:
    print('fetching stnums to audit')
    r = http.request('GET', BATCH_URL)

    student_ids = set(r.data.decode('utf-8').splitlines())
    student_ids.add('122932')

    print(f'fetched {len(student_ids):,} stnums to audit')

    with ProcessPoolExecutor() as pool:
        future_to_stnum = {pool.submit(fetch, stnum): stnum for stnum in student_ids}

        for future in tqdm.tqdm(as_completed(future_to_stnum), total=len(future_to_stnum), disable=None):
            stnum = future_to_stnum[future]

            try:
                yield future.result()
            except Exception as exc:
                print(f'fetching {stnum} generated an exception: {exc}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=int, nargs='?')
    args = parser.parse_args()

    assert SINGLE_URL
    assert BATCH_URL

    conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
    )

    run = args.run
    if args.run is None:
        with conn, conn.cursor() as curs:
            curs.execute('SELECT max(run) + 1 FROM result')
            row = curs.fetchone()
            run = row[0]

    with conn, conn.cursor() as curs:
        for student, data in batch():
            for stnum, catalog, code in expand_student(student=student):
                if (stnum, code) in DISABLED:
                    continue

                curs.execute('''
                    INSERT INTO queue (priority, student_id, area_catalog, area_code, input_data, run)
                    VALUES (1, %(stnum)s, %(catalog)s, %(code)s, cast(%(data)s as jsonb), %(run)s)
                ''', {'stnum': stnum, 'catalog': catalog, 'code': code, 'data': data, 'run': run})


if __name__ == '__main__':
    main()
