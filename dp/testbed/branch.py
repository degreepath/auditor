from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import sqlite3
import traceback

import tqdm  # type: ignore

from .sqlite import sqlite_connect, sqlite_cursor
from .audit import audit
from .fetch import fetch_if_needed
from .areas import load_areas

from dp.ms import pretty_ms, parse_ms_str


def branch(args: argparse.Namespace) -> None:
    fetch_if_needed(args)

    with sqlite_connect(args.db) as conn:
        print(f'clearing data for "{args.branch}"... ', end='', flush=True)
        conn.execute('DELETE FROM branch WHERE branch = ?', [args.branch])
        conn.commit()
        print('cleared')

    minimum_duration = parse_ms_str(args.minimum_duration)

    with sqlite_connect(args.db) as conn:
        results = conn.execute('''
            SELECT
                count(duration) as count,
                coalesce(max(sum(duration) / :workers, max(duration)), 0) as duration_s
            FROM baseline
            WHERE duration < :min
                AND CASE WHEN :code IS NULL THEN 1 = 1 ELSE code = :code END
        ''', {'min': minimum_duration.sec(), 'workers': args.workers, 'code': args.filter})

        count, estimated_duration_s = results.fetchone()

        pretty_min = pretty_ms(minimum_duration.ms())
        pretty_dur = pretty_ms(estimated_duration_s * 1000)
        print(f'{count:,} audits under {pretty_min} each: ~{pretty_dur} with {args.workers:,} workers')

        results = conn.execute('''
            SELECT catalog, code
            FROM baseline
            WHERE duration < :min
                AND CASE WHEN :code IS NULL THEN 1 = 1 ELSE code = :code END
            GROUP BY catalog, code
        ''', {'min': minimum_duration.sec(), 'code': args.filter})

        area_specs = load_areas(args, list(results))

        results = conn.execute('''
            SELECT stnum, catalog, code
            FROM baseline
            WHERE duration < :min
                AND CASE WHEN :code IS NULL THEN 1 = 1 ELSE code = :code END
            ORDER BY duration DESC, stnum, catalog, code
        ''', {'min': minimum_duration.sec(), 'code': args.filter})

        records = [(stnum, catalog, code) for stnum, catalog, code in results]

    print(f'running {len(records):,} audits...')

    with sqlite_connect(args.db) as conn, ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                audit,
                (stnum, catalog, code),
                db=args.db,
                area_spec=area_specs[f"{catalog}/{code}"],
                # timeout=float(minimum_duration.sec()),
                run_id=args.branch,
            ): (stnum, catalog, code)
            for (stnum, catalog, code) in records
        }

        for future in tqdm.tqdm(as_completed(futures), total=len(futures), disable=None):
            stnum, catalog, code = futures[future]

            with sqlite_cursor(conn) as curs:
                try:
                    db_args = future.result()
                except TimeoutError as timeout:
                    print(timeout.args[0])
                    conn.commit()
                    continue
                except Exception:
                    print(f'{stnum} {catalog} {code} generated an exception: {traceback.format_exc()}')
                    continue

                assert db_args is not None, f"{stnum}, {catalog}, {code} returned None"

                try:
                    curs.execute('''
                        INSERT INTO branch (branch, stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result)
                        VALUES (:run, :stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, :status, json(:result))
                    ''', db_args)
                except sqlite3.Error as ex:
                    print(db_args)
                    print(db_args['stnum'], db_args['catalog'], db_args['code'], 'generated an exception', ex)
                    conn.rollback()
                    continue

                conn.commit()
