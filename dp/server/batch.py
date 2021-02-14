from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Set, Dict, Tuple, cast
import argparse
import json
import os

import tqdm  # type: ignore
import urllib3  # type: ignore
import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
import psycopg2.extensions  # type: ignore

from dp.dotenv import load as load_dotenv
from dp.bin.expand import expand_student

http = urllib3.PoolManager()
BATCH_URL = os.getenv("DP_BATCH_URL")
SINGLE_URL = os.getenv("DP_SINGLE_URL")

Item = Tuple[str, str]


def get_student(student_id: str) -> Tuple[Dict, str]:
    r = http.request("GET", SINGLE_URL, fields={"stnum": student_id})
    text = r.data.decode("utf-8")
    return cast(Dict, json.loads(text)), text


def fetch_and_queue(
    *,
    conn: psycopg2.extensions.connection,
    student_id: str,
    run: int,
    queued_items: Set[Item],
    blocked_items: Set[Item],
    area_code_filter: Optional[str] = None
) -> int:
    parsed_student, unparsed_json = get_student(student_id)

    count = 0

    with conn.cursor() as curs:
        for stnum, catalog, code in expand_student(student=parsed_student):
            # skip already-queued items in this loop to avoid postgres deadlocks
            if (stnum, code) in queued_items:
                continue

            # skip audits that have been blocked
            if (stnum, code) in blocked_items:
                continue

            # allow filtering batches of audits
            if area_code_filter is not None and area_code_filter != code:
                continue

            count += 1

            curs.execute("""
                INSERT INTO queue (priority, student_id, area_catalog, area_code, input_data, run)
                VALUES (1, %(stnum)s, %(catalog)s, %(code)s, cast(%(data)s as jsonb), %(run)s)
            """, {"stnum": stnum, "catalog": catalog, "code": code, "data": unparsed_json, "run": run})

        conn.commit()

    return count


def get_student_ids() -> Set[str]:
    print("fetching student ids to audit")
    r = http.request("GET", BATCH_URL)

    student_ids = set(r.data.decode("utf-8").split())
    student_ids.add("122932")

    return student_ids


def fetch_queued_audits(conn: psycopg2.extensions.connection) -> Set[Item]:
    print("fetching queued audits")
    items: Set[Item] = set()

    with conn.cursor() as curs:
        curs.execute("""
            SELECT student_id, area_code, ts at time zone 'America/Winnipeg' as ts
            FROM queue
        """)

        for record in curs:
            print(f"> ({record['student_id']}, {record['area_code']}) has been queued since {record['ts']} CT and will be skipped")
            items.add((record['student_id'], record['area_code']))

    if not items:
        print("> no audits are currently queued")

    return items


def fetch_blocked_audits(conn: psycopg2.extensions.connection) -> Set[Item]:
    print("fetching blocked audits")
    items: Set[Item] = set()

    with conn.cursor() as curs:
        curs.execute("""
            SELECT student_id, area_code, added_by, added_at at time zone 'America/Winnipeg' as added_at
            FROM queue_block
        """)

        for record in curs:
            print(f"> ({record['student_id']}, {record['area_code']}) has been blocked since {record['added_at']} CT by {record['added_by']} and will be skipped")
            items.add((record['student_id'], record['area_code']))

    if not items:
        print("> no audits are currently blocked")

    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, nargs="?")
    parser.add_argument("--code", type=str, nargs="?")
    args = parser.parse_args()

    try:
        worker_count = len(os.sched_getaffinity(0))
    except AttributeError:
        worker_count = cast(int, os.cpu_count())

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

    total_count = 0

    queued_items = fetch_queued_audits(conn=conn)
    blocked_items = fetch_blocked_audits(conn=conn)

    student_ids = get_student_ids()
    remaining_student_ids = list(student_ids)

    print(f"fetching and queueing data for {len(student_ids):,} student ids with {worker_count} threads")
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        future_to_student_id = {
            pool.submit(
                fetch_and_queue,
                conn=conn,
                student_id=student_id,
                run=run,
                queued_items=queued_items,
                blocked_items=blocked_items,
                area_code_filter=args.code,
            ): student_id
            for student_id in student_ids
        }

        pbar = tqdm.tqdm(as_completed(future_to_student_id), total=len(future_to_student_id), disable=None)

        for future in pbar:
            student_id = future_to_student_id[future]

            try:
                remaining_student_ids.remove(student_id)
            except ValueError:
                pass
            upcoming = remaining_student_ids[:worker_count]

            try:
                inserted_item_count = future.result()
                total_count += inserted_item_count

                pbar.set_description(', '.join(upcoming))
                # print(f"> fetched and queued {inserted_item_count} audits for {student_id}")

            except Exception as exc:
                print(f"> processing {student_id} generated an exception: {exc}")

    print(f"queued {total_count:,} audits")

    conn.close()


if __name__ == "__main__":
    load_dotenv()

    try:
        main()
    except KeyboardInterrupt:
        pass
