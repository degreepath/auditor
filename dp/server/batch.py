from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, Set, Dict, Tuple, cast
from pathlib import Path
import argparse
import json
import os

import tqdm  # type: ignore
import urllib3  # type: ignore
import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
import sentry_sdk  # type: ignore

from dp.dotenv import load as load_dotenv
from dp.bin.expand import expand_student

# always resolve to the local .env file
dotenv_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(filepath=dotenv_path)

if os.environ.get("SENTRY_DSN", None):
    sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))

http = urllib3.PoolManager()
DISABLED: Set[Tuple[str, str]] = set()

BATCH_URL = os.getenv("DP_BATCH_URL")
SINGLE_URL = os.getenv("DP_SINGLE_URL")


def fetch(stnum: str) -> Tuple[Dict, str]:
    r = http.request("GET", SINGLE_URL, fields={"stnum": stnum})
    text = r.data.decode("utf-8")
    return cast(Dict, json.loads(text)), text


def batch() -> Iterator[Tuple[Dict, str]]:
    print("fetching student ids to audit")
    r = http.request("GET", BATCH_URL)

    student_ids = set(r.data.decode("utf-8").split())
    student_ids.add("122932")

    try:
        worker_count = len(os.sched_getaffinity(0))
    except AttributeError:
        worker_count = cast(int, os.cpu_count())

    print(f"fetching data for {len(student_ids):,} student ids with {worker_count} threads")

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        future_to_stnum = {pool.submit(fetch, stnum): stnum for stnum in student_ids}

        for future in tqdm.tqdm(as_completed(future_to_stnum), total=len(future_to_stnum), disable=None):
            stnum = future_to_stnum[future]

            try:
                yield future.result()
            except Exception as exc:
                print(f"fetching {stnum} generated an exception: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, nargs="?")
    parser.add_argument("--code", type=str, nargs="?")
    args = parser.parse_args()

    assert SINGLE_URL
    assert BATCH_URL

    conn = psycopg2.connect(
        "",  # empty string means "use the environment variables"
        application_name="degreepath-batch",
        cursor_factory=psycopg2.extras.DictCursor,
    )

    run = args.run
    if args.run is None:
        with conn.cursor() as curs:
            curs.execute("SELECT max(run) + 1 FROM result")
            row = curs.fetchone()
            run = row[0]

    count = 0

    with conn.cursor() as curs:
        print("fetching queued audits")
        curs.execute("""
            SELECT student_id, area_code, ts at time zone 'America/Winnipeg' as ts
            FROM queue
        """)
        queued_items: Set[Tuple[str, str]] = set()
        for record in curs:
            print(f"> {record['student_id']} : {record['area_code']} has been queued since {record['ts']} CT and will be skipped")
            queued_items.add((record['student_id'], record['area_code']))


        for student, data in batch():
            for stnum, catalog, code in expand_student(student=student):
                # skip already-queued items in this loop to avoid postgres deadlocks
                if (stnum, code) in queued_items:
                    continue

                if (stnum, code) in DISABLED:
                    print("skipping", stnum, code, "as it is blocked")
                    continue

                # allow filtering batches of audits
                if args.code is not None and args.code != code:
                    continue

                count += 1

                curs.execute("""
                    INSERT INTO queue (priority, student_id, area_catalog, area_code, input_data, run)
                    VALUES (1, %(stnum)s, %(catalog)s, %(code)s, cast(%(data)s as jsonb), %(run)s)
                    ON CONFLICT DO NOTHING
                """, {"stnum": stnum, "catalog": catalog, "code": code, "data": data, "run": run})

    print(f"queued {count:,} audits in the database")

    conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
