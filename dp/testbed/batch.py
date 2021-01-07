from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional
import argparse

import attr
import tqdm  # type: ignore

from .sqlite import sqlite_connect, sqlite_transaction
from .audit import audit
from .fetch import fetch_if_needed
from .areas import load_areas

from dp.ms import pretty_ms, parse_ms_str


@attr.s(frozen=True, auto_attribs=True)
class Record:
    stnum: str
    catalog: str
    code: str
    duration: float
    area_key: str


def run_batch(args: argparse.Namespace, *, baseline: bool) -> None:
    fetch_if_needed(args)

    with sqlite_connect(args.db) as conn, sqlite_transaction(conn):
        if baseline:
            print('clearing baseline data... ', end='', flush=True)
            conn.execute('DELETE FROM baseline')
        else:
            print(f'clearing data for "{args.branch}"... ', end='', flush=True)
            conn.execute('DELETE FROM branch WHERE branch = ?', [args.branch])
        print('cleared')

    minimum_duration = parse_ms_str(args.minimum_duration)

    with sqlite_connect(args.db) as conn:
        if baseline:
            results = conn.execute('''
                SELECT stnum, catalog, code, duration, catalog || '/' || code as area_key
                FROM server_data
                WHERE duration < :min
                ORDER BY duration DESC, stnum, catalog, code
            ''', {'min': minimum_duration.sec()})
        else:
            results = conn.execute('''
                SELECT stnum, catalog, code, duration, catalog || '/' || code as area_key
                FROM baseline
                WHERE duration < :min
                ORDER BY duration DESC, stnum, catalog, code
            ''', {'min': minimum_duration.sec()})

        records = [Record(**r) for r in results]

    if args.filter is not None:
        records = [r for r in records if r.code == args.filter]

    estimated_duration_s = sum(r.duration for r in records) / args.workers
    pretty_dur = pretty_ms(estimated_duration_s * 1000)
    pretty_min = pretty_ms(minimum_duration.ms())
    print(f'{len(records):,} audits under {pretty_min} each: ~{pretty_dur} with {args.workers:,} workers')

    if baseline and args.copy:
        with sqlite_transaction(conn):
            conn.execute('''
                INSERT INTO baseline (stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result)
                SELECT stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result
                FROM server_data
                WHERE duration < :min
            ''', {'min': minimum_duration.sec()})
        return

    area_codes = set((r.catalog, r.code) for r in records)
    area_specs = load_areas(args, [{"catalog": catalog, "code": code} for catalog, code in area_codes])

    remaining_records = list(records)
    print(f'running {len(records):,} audits...')

    timeout: Optional[float] = None
    if baseline:
        timeout = float(minimum_duration.sec()) * 2.5

    with \
            sqlite_connect(args.db) as conn, \
            sqlite_transaction(conn), \
            ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                audit,
                (r.stnum, r.catalog, r.code),
                db=args.db,
                area_spec=area_specs[r.area_key],
                timeout=timeout,
                run_id=getattr(args, 'branch', 'None'),
            ): r
            for r in records
            if r.area_key in area_specs
        }

        pbar = tqdm.tqdm(total=len(futures), disable=None)

        upcoming = [f"{r.stnum}:{r.code}" for r in remaining_records[:args.workers]]
        pbar.set_description(', '.join(upcoming))

        for future in as_completed(futures):
            record = futures[future]

            try:
                remaining_records.remove(record)
                upcoming = [f"{r.stnum}:{r.code}" for r in remaining_records[:args.workers]]
            except ValueError:
                pass

            pbar.update(n=1)
            # pbar.write(f"completed ({record.stnum}, {record.code})")
            pbar.set_description(', '.join(upcoming))

            try:
                db_args = future.result()
            except TimeoutError as err:
                print(err.args[0])
                continue
            except Exception as exc:
                print(f'{record.stnum} {record.catalog} {record.code} generated an exception: {exc}')
                continue

            assert db_args is not None, f"{record.stnum}, {record.catalog}, {record.code} returned None"

            if baseline:
                conn.execute('''
                    INSERT INTO baseline (stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result, version)
                    VALUES (:stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, :status, json(:result), :version)
                ''', db_args)
            else:
                conn.execute('''
                    INSERT INTO branch (branch, stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, status, result, version)
                    VALUES (:run, :stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, :status, json(:result), :version)
                ''', db_args)
