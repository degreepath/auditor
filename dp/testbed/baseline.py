from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import sqlite3
import logging

import tqdm  # type: ignore

from .sqlite import sqlite_connect, sqlite_cursor
from .audit import audit
from .fetch import fetch_if_needed
from .areas import load_areas

from dp.ms import pretty_ms, parse_ms_str

logger = logging.getLogger(__name__)


def baseline(args: argparse.Namespace) -> None:
    fetch_if_needed(args)

    with sqlite_connect(args.db) as conn:
        print('clearing baseline data... ', end='', flush=True)
        conn.execute('DELETE FROM baseline')
        conn.execute('DELETE FROM baseline_ip')
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

        if args.copy:
            conn.execute('''
                INSERT INTO baseline (stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result)
                SELECT stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result
                FROM server_data
                WHERE duration < :min
            ''', {'min': minimum_duration.sec()})
            conn.commit()
            return

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

    print(f'running {len(records):,} audits...')

    with sqlite_connect(args.db) as conn:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
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

            for future in tqdm.tqdm(as_completed(futures), total=len(futures), disable=None):
                stnum, catalog, code = futures[future]

                with sqlite_cursor(conn) as curs:
                    try:
                        db_args = future.result()
                    except TimeoutError as timeout:
                        print(timeout.args[0])
                        curs.execute('''
                            DELETE
                            FROM baseline_ip
                            WHERE stnum = :stnum
                                AND catalog = :catalog
                                AND code = :code
                        ''', timeout.args[1])
                        conn.commit()
                        continue
                    except Exception as exc:
                        print(f'{stnum} {catalog} {code} generated an exception: {exc}')
                        continue

                    assert db_args is not None

                    try:
                        curs.execute('''
                            INSERT INTO baseline (stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result)
                            VALUES (:stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, :status, json(:result))
                        ''', db_args)

                        curs.execute('''
                            DELETE
                            FROM baseline_ip
                            WHERE stnum = :stnum
                                AND catalog = :catalog
                                AND code = :code
                        ''', db_args)
                    except sqlite3.Error as ex:
                        print(db_args)
                        print(db_args['stnum'], db_args['catalog'], db_args['code'], 'generated an exception', ex)
                        conn.rollback()
                        continue

                    conn.commit()
