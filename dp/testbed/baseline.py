from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import sqlite3

import tqdm  # type: ignore

from .sqlite import sqlite_connect, sqlite_cursor
from .audit import audit
from .fetch import fetch_if_needed
from .areas import load_areas

from dp.ms import pretty_ms, parse_ms_str


def baseline(args: argparse.Namespace) -> None:
    fetch_if_needed(args)

    with sqlite_connect(args.db) as conn:
        print('clearing baseline data... ', end='', flush=True)
        conn.execute('DELETE FROM baseline')
        conn.commit()
        print('cleared')

    minimum_duration = parse_ms_str(args.minimum_duration)

    with sqlite_connect(args.db) as conn:
        results = conn.execute('''
            SELECT
                count(duration) as count,
                coalesce(max(sum(duration) / :workers, max(duration)), 0) as duration_s
            FROM server_data
            WHERE duration < :min
        ''', {'min': minimum_duration.sec(), 'workers': args.workers})

        count, estimated_duration_s = results.fetchone()

        pretty_min = pretty_ms(minimum_duration.ms())
        pretty_dur = pretty_ms(estimated_duration_s * 1000)
        print(f'{count:,} audits under {pretty_min} each: ~{pretty_dur} with {args.workers:,} workers')

        results = conn.execute('''
            SELECT catalog, code
            FROM server_data
            WHERE duration < :min
            GROUP BY catalog, code
        ''', {'min': minimum_duration.sec()})

        area_specs = load_areas(args, list(results))

        results = conn.execute('''
            SELECT stnum, catalog, code
            FROM server_data
            WHERE duration < :min
            ORDER BY duration DESC, stnum, catalog, code
        ''', {'min': minimum_duration.sec()})

        records = [(stnum, catalog, code) for stnum, catalog, code in results]

    remaining_records = list(records)
    print(f'running {len(records):,} audits...')

    with sqlite_connect(args.db) as conn, ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                audit,
                (stnum, catalog, code),
                db=args.db,
                area_spec=area_specs[f"{catalog}/{code}"],
                timeout=float(minimum_duration.sec()) * 2.5,
            ): (stnum, catalog, code)
            for (stnum, catalog, code) in records
            if f"{catalog}/{code}" in area_specs
        }

        pbar = tqdm.tqdm(total=len(futures), disable=None)

        upcoming = [f"{stnum}:{code}" for stnum, _catalog, code in remaining_records[:args.workers]]
        pbar.set_description(', '.join(upcoming))

        for future in as_completed(futures):
            stnum, catalog, code = futures[future]

            try:
                remaining_records.remove((stnum, catalog, code))
                upcoming = [f"{stnum}:{code}" for stnum, _catalog, code in remaining_records[:args.workers]]
            except ValueError:
                pass

            pbar.update(n=1)
            pbar.write(f"completed ({stnum}, {code})")
            pbar.set_description(', '.join(upcoming))

            try:
                db_args = future.result()
            except TimeoutError as timeout:
                print(timeout.args[0])
                conn.commit()
                continue
            except Exception as exc:
                print(f'{stnum} {catalog} {code} generated an exception: {exc}')
                continue

            assert db_args is not None

            with sqlite_cursor(conn) as curs:
                try:
                    curs.execute('''
                        INSERT INTO baseline (stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result)
                        VALUES (:stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, :status, json(:result))
                    ''', db_args)
                except sqlite3.Error as ex:
                    print(db_args)
                    print(db_args['stnum'], db_args['catalog'], db_args['code'], 'generated an exception', ex)
                    conn.rollback()
                    continue

                conn.commit()
