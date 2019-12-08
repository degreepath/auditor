import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
import dotenv
import tqdm  # type: ignore
import yaml

# input() will use readline if imported
import readline  # noqa: F401

import sqlite3
import pathlib
import decimal
import math
import contextlib
import argparse
import logging
import os
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, Any, Tuple, Dict, Sequence, Iterator

from degreepath.main import run
from degreepath.ms import pretty_ms, parse_ms_str
from degreepath.audit import ResultMsg, Arguments

logger = logging.getLogger(__name__)


def adapt_decimal(d: decimal.Decimal) -> str:
    return str(d)


def convert_decimal(s: Any) -> decimal.Decimal:
    return decimal.Decimal(s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda args: parser.print_usage())

    parser.add_argument('--db', action='store', default='testbed_db.db')
    parser.add_argument('-w', '--workers', action='store', type=int, help='how many workers to use to run parallel audits', default=math.floor((os.cpu_count() or 0) / 4 * 3))

    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands')

    parser_fetch = subparsers.add_parser('fetch', help='downloads audit results from a server')
    parser_fetch.add_argument('--latest', action='store_true', default=False, help='always fetch the latest run of audits')
    parser_fetch.add_argument('--run', action='store', type=int, help='fetch the Nth run of audits')
    parser_fetch.add_argument('--clear', action='store_true', default=False, help='clear the cached results table')
    parser_fetch.set_defaults(func=fetch)

    parser_bench = subparsers.add_parser('bench', help='runs local "benchmarks" against the audits')
    parser_bench.add_argument('--min', dest='minimum_duration', default='30s', nargs='?', help='the minimum duration of audits to benchmark against')
    parser_bench.set_defaults(func=bench)

    parser_compare = subparsers.add_parser('compare', help='runs audits locally to check for changes')
    parser_compare.add_argument('branch', nargs='?', help='the git branch to compare against')
    parser_compare.set_defaults(func=compare)

    args = parser.parse_args()
    args.func(args)


def fetch(args: argparse.Namespace) -> None:
    '''
    $ python3 testbed.py fetch
    Which run would you like to fetch?
    1. 217, 2019-12-06 10pm / 2019-12-07 2am [4hr]; 7701 total, 100 ok, 7601 not-ok
    2. 216, 2019-12-06 10pm / 2019-12-07 2am [4hr]; 7701 total, 100 ok, 7601 not-ok
    3. 215, 2019-12-06 10pm / 2019-12-07 2am [4hr]; 7701 total, 100 ok, 7601 not-ok
    4. 214, 2019-12-06 10pm / 2019-12-07 2am [4hr]; 7701 total, 100 ok, 7601 not-ok
    5. 213, 2019-12-06 10pm / 2019-12-07 2am [4hr]; 7701 total, 100 ok, 7601 not-ok
    219: 2019-12-06 23:07 / 2019-12-07 04:40 [5h 32m 58.7s]; 6,997 total, 201 ok, 6,796 not-ok
    >>> 1
    Fetching and storing into run-217.sqlite3
    76%|████████████████████████████         | 7568/10000 [00:33<00:10, 229.00it/s]
    '''

    conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        cursor_factory=psycopg2.extras.DictCursor,
    )
    conn.set_session(readonly=True)

    selected_run = fetch__select_run(args, conn)

    with conn.cursor() as curs:
        curs.execute('''
            SELECT count(*) total_count
            FROM result
            WHERE run = %s
        ''', [selected_run])

        count_row = curs.fetchone()
        total_items = count_row['total_count']

    print(f"Fetching run #{selected_run} with {total_items:,} audits into '{args.db}'")

    with sqlite_connect(args.db) as sqlite_conn:
        with sqlite_cursor(sqlite_conn) as s_curs:
            s_curs.execute('''
                CREATE TABLE IF NOT EXISTS server_data (
                    run integer not null,
                    stnum text not null,
                    catalog text not null,
                    code text not null,
                    iterations integer not null,
                    duration numeric not null,
                    gpa numeric not null,
                    ok boolean not null,
                    rank numeric not null,
                    max_rank numeric not null,
                    result json not null,
                    input_data json not null
                )
            ''')
            curs.execute('CREATE UNIQUE INDEX IF NOT EXISTS server_data_key_idx ON server_data (stnum, catalog, code)')
            curs.execute('CREATE INDEX IF NOT EXISTS server_data_cmp_idx ON server_data (ok, gpa, iterations, rank, max_rank)')

            sqlite_conn.commit()

        if args.clear:
            print('clearing cached data...')
            with sqlite_cursor(sqlite_conn) as s_curs:
                s_curs.execute('DELETE FROM server_data')
                s_curs.commit()
            print('cleared')

    # named cursors only allow one execute() call, so this must be its own block
    with conn.cursor(name="degreepath_testbed") as curs:
        curs.itersize = 10

        curs.execute('''
            SELECT student_id AS stnum
                 , catalog
                 , area_code AS code
                 , iterations
                 , extract(EPOCH FROM duration) AS duration
                 , gpa
                 , ok
                 , rank
                 , max_rank
                 , result::text as result
                 , input_data::text as input_data
                 , run
            FROM result
            WHERE run = %s
        ''', [selected_run])

        with sqlite_connect(args.db) as sqlite_conn:
            with sqlite_cursor(sqlite_conn) as s_curs:
                for row in tqdm.tqdm(curs, total=total_items, disable=None, unit_scale=True):
                    if row['result'] is None:
                        continue

                    try:
                        s_curs.execute('''
                            INSERT INTO server_data (run, stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, result, input_data)
                            VALUES (:run, :stnum, :catalog, :code, :iterations, :duration, :ok, :gpa, :rank, :max_rank, json(:result), json(:input_data))
                        ''', {**row})
                    except Exception as e:
                        print({**row})
                        raise e

                sqlite_conn.commit()


def fetch__select_run(args: argparse.Namespace, conn: psycopg2.Connection) -> int:
    with conn.cursor() as curs:
        if args.latest:
            curs.execute('SELECT max(run) as max FROM result')
            to_fetch = curs.fetchone()['max']

        elif args.run:
            to_fetch = args.run

        else:
            curs.execute("""
                SELECT run
                     , min(ts AT TIME ZONE 'America/Chicago') AS first
                     , max(ts AT TIME ZONE 'America/Chicago') AS last
                     , extract(epoch from max(ts AT TIME ZONE 'America/Chicago') - min(ts AT TIME ZONE 'America/Chicago')) AS duration
                     , count(*) AS total
                     , sum(ok::integer) AS ok
                     , sum((NOT ok)::integer) AS "not-ok"
                FROM result
                WHERE run > 0
                  AND ts > now() - INTERVAL '1 week'
                GROUP BY run
                ORDER BY run DESC
            """)

            # 219: 2019-12-06 23:07 / 2019-12-07 04:40 [5h 32m 58.7s]; 6,997 total, 201 ok, 6,796 not-ok
            datefmt = "%Y-%m-%d %H:%M"
            for row in curs.fetchall():
                first = row['first'].strftime(datefmt)
                last = row['last'].strftime(datefmt)
                duration = pretty_ms(row['duration'] * 1000, unit_count=2)
                print(f"{row['run']}: {first} / {last} [{duration}]; {row['total']:,} total, {row['ok']:,} ok, {row['not-ok']:,} not-ok")

            print('Download which run?')
            to_fetch = int(input('>>> '))

        return int(to_fetch)


def fetch_if_needed(args: argparse.Namespace) -> None:
    with sqlite_connect(args.db) as conn:
        with sqlite_cursor(conn) as curs:
            curs.execute('SELECT count(*) FROM server_data')

            if curs.fetchone()[0]:
                return
            else:
                raise Exception('run the fetch subcommand')


def bench(args: argparse.Namespace) -> None:
    '''
    $ python3 testbed.py bench
    Saving initial results...  # skip printing if results are already downloaded
    Initial results saved: run 217
    Running local checks on all <30s audits...
    76%|████████████████████████████         | 7568/10000 [00:33<00:10, 229.00it/s]
    [...]
    Found 300 unexpected audit result changes:
    code,catalog,count
    150,2016-17,100
    200,2016-17,200
    Details for 150, 2016-17:
    code,catalog,stnum,iterations,now_ok,now_rank,now_max,then_ok,then_rank,then_max_rank
    150,2016-17,123456,5,t,10,10,f,9,10
    [...]
    '''

    fetch_if_needed(args)

    minimum_duration = parse_ms_str(args.minimum_duration)

    with sqlite_connect(args.db) as conn:
        with sqlite_cursor(conn) as curs:
            curs.execute('''
                CREATE TABLE IF NOT EXISTS local_run (
                    run text not null,
                    stnum text not null,
                    catalog text not null,
                    code text not null,
                    iterations integer not null,
                    duration numeric not null,
                    gpa numeric not null,
                    ok boolean not null,
                    rank numeric not null,
                    max_rank numeric not null,
                    result json not null
                )
            ''')
            curs.execute('CREATE UNIQUE INDEX IF NOT EXISTS local_run_key_idx ON local_run (stnum, catalog, code)')
            curs.execute('CREATE INDEX IF NOT EXISTS local_run_cmp_idx ON local_run (run, ok, gpa, iterations, rank, max_rank)')

            conn.commit()

    with sqlite_connect(args.db) as conn:
        with sqlite_cursor(conn) as curs:
            curs.execute('''
                SELECT
                    count(duration) as count,
                    coalesce(max(sum(duration) / :workers, max(duration)), 0) as duration_s
                FROM server_data
                WHERE duration < :min
            ''', {'min': minimum_duration.sec(), 'workers': args.workers})

            count, estimated_duration_s = curs.fetchone()

            pretty_min = pretty_ms(minimum_duration.ms())
            pretty_dur = pretty_ms(estimated_duration_s * 1000)
            print(f'{count:,} audits under {pretty_min} each: ~{pretty_dur} with {args.workers:,} workers')

            curs.execute('''
                SELECT catalog, code
                FROM server_data
                WHERE duration < :min
                GROUP BY catalog, code
            ''', {'min': minimum_duration.sec()})

            areas_to_load = list(curs.fetchall())

            area_specs = load_areas(args, areas_to_load)

            curs.execute('''
                SELECT stnum, catalog, code
                FROM server_data
                WHERE duration < :min
                ORDER BY duration DESC
            ''', {'min': minimum_duration.sec()})

            records = [tuple(row) for row in curs]

    print(f'running {len(records):,} audits...')

    with sqlite_connect(args.db) as conn:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(audit, row, db=args.db, area_spec=area_specs[f"{row[1]}/{row[2]}"], run_id='base')
                for row in records
            ]

            for future in tqdm.tqdm(as_completed(futures), total=len(futures), disable=None):
                db_args = future.result()

                with sqlite_cursor(conn) as curs:
                    conn.execute('''
                        INSERT INTO local_run (run, stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, result)
                        VALUES (:run, :stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, json(:result))
                    ''', db_args)

                    conn.commit()


def load_areas(args: argparse.Namespace, areas_to_load: Sequence[Dict]) -> Dict[str, Any]:
    root_env = os.getenv('AREA_ROOT')
    assert root_env
    area_root = pathlib.Path(root_env)

    print(f'loading {len(areas_to_load):,} areas...')
    area_specs = {}
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(load_area, area_root, record['catalog'], record['code']) for record in areas_to_load]

        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            key, area = future.result()
            area_specs[key] = area

    return area_specs


def load_area(root: pathlib.Path, catalog: str, code: str) -> Tuple[str, Dict]:
    with open(root / catalog / f"{code}.yaml", "r", encoding="utf-8") as infile:
        return f"{catalog}/{code}", yaml.load(stream=infile, Loader=yaml.SafeLoader)


def audit(row: Tuple[str, str, str], *, db: str, area_spec: Dict, run_id: str) -> Optional[Dict]:
    stnum, catalog, code = row

    with sqlite_connect(db, readonly=True) as conn:
        with sqlite_cursor(conn) as curs:
            curs.execute('''
                SELECT input_data
                FROM server_data
                WHERE (stnum, catalog, code) = (?, ?, ?)
            ''', [stnum, catalog, code])

            record = curs.fetchone()
            assert record is not None

            args = Arguments(
                student_data=[json.loads(record['input_data'])],
                area_specs=[(area_spec, catalog)],
            )

            for message in run(args):
                if isinstance(message, ResultMsg):
                    result = message.result.to_dict()
                    return {
                        "run": run_id,
                        "stnum": stnum,
                        "catalog": catalog,
                        "code": code,
                        "iterations": message.count,
                        "duration": message.elapsed_ms / 1000,
                        "gpa": result["gpa"],
                        "ok": result["ok"],
                        "rank": result["rank"],
                        "max_rank": result["max_rank"],
                        "result": json.dumps(result),
                    }
                else:
                    pass

    return None


def compare(args: argparse.Namespace) -> None:
    '''
    $ python3 testbed.py compare <git-branch> --min 45s
    Saving initial results...  # skip printing if results are already downloaded
    Initial results saved: run 217
    Running local checks on all <45s audits...
    76%|████████████████████████████         | 7568/10000 [00:33<00:10, 229.00it/s]
    [...]
    No audit results changed.
    Checking out <git-branch>...
    Running local checks on all <45s audits...
    76%|████████████████████████████         | 7568/10000 [00:33<00:10, 229.00it/s]
    [...]
    No audit results changed.
    value,stable,<git-branch>
    wall,30s,20s  # wall time
    '''

    print(args)

    # fetch()

    # bench()

    # run(['git', 'checkout', args.branch])

    # bench()


@contextlib.contextmanager
def sqlite_connect(filename: str, readonly: bool = False) -> Iterator[sqlite3.Connection]:
    uri = f'file:{filename}'
    if readonly:
        uri = f'file:{filename}?mode=ro'

    conn = sqlite3.connect(uri, uri=True, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def sqlite_cursor(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    curs = conn.cursor()
    try:
        yield curs
    finally:
        curs.close()


if __name__ == "__main__":
    dotenv.load_dotenv(verbose=True)

    # Register the adapter
    sqlite3.register_adapter(decimal.Decimal, adapt_decimal)

    # Register the converter
    sqlite3.register_converter("decimal", convert_decimal)

    main()
