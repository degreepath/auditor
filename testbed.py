import dotenv
import tqdm  # type: ignore
import yaml

# input() will use readline if imported
import readline  # noqa: F401

import contextlib
import argparse
import sqlite3
import pathlib
import decimal
import logging
import math
import json
import csv
import sys
import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, Any, Tuple, Dict, Sequence, Iterator

from degreepath.main import run
from degreepath.ms import pretty_ms, parse_ms_str
from degreepath.audit import ResultMsg, Arguments
from degreepath.data.course import load_course
from degreepath.stringify import print_result

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

    parser_baseline = subparsers.add_parser('baseline', help='runs a baseline audit benchmark')
    parser_baseline.add_argument('--min', dest='minimum_duration', default='30s', nargs='?', help='the minimum duration of audits to benchmark against')
    # parser_baseline.add_argument('--clear', action='store_true', default=False, help='clear the cached results table')
    parser_baseline.set_defaults(func=baseline)

    parser_branch = subparsers.add_parser('branch', help='runs an audit benchmark')
    parser_branch.add_argument('--min', dest='minimum_duration', default='30s', nargs='?', help='the minimum duration of audits to benchmark against')
    # parser_branch.add_argument('--clear', action='store_true', default=False, help='clear the cached results table')
    parser_branch.add_argument('branch', help='the git branch to compare against')
    parser_branch.set_defaults(func=branch)

    parser_compare = subparsers.add_parser('compare', help='compare an audit run against the baseline')
    parser_compare.add_argument('run', help='the run to compare against the base run')
    parser_compare.add_argument('base', default='baseline', nargs='?', help='the base run to compare against')
    parser_compare.add_argument('--mode', default='data', choices=['data', 'speed', 'all'], help='the base run to compare against')
    parser_compare.set_defaults(func=compare)

    parser_print = subparsers.add_parser('print', help='show the baseline and branched audit results')
    parser_print.add_argument('branch', help='')
    parser_print.add_argument('stnum', help='')
    parser_print.add_argument('catalog')
    parser_print.add_argument('code')
    parser_print.set_defaults(func=render)

    args = parser.parse_args()
    init_local_db(args)
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

    import psycopg2  # type: ignore
    import psycopg2.extras  # type: ignore

    pg_conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        cursor_factory=psycopg2.extras.DictCursor,
    )
    pg_conn.set_session(readonly=True)

    selected_run = fetch__select_run(args, pg_conn)

    with pg_conn.cursor() as curs:
        curs.execute('''
            SELECT count(*) total_count
            FROM result
            WHERE run = %s
        ''', [selected_run])

        total_items = curs.fetchone()['total_count']

    print(f"Fetching run #{selected_run} with {total_items:,} audits into '{args.db}'")

    if args.clear:
        with sqlite_connect(args.db) as conn:
            print('clearing cached data... ', end='')
            conn.execute('DELETE FROM server_data')
            conn.commit()
            print('cleared')

    # named cursors only allow one execute() call, so this must be its own block
    with pg_conn.cursor(name="degreepath_testbed") as curs:
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
            WHERE result IS NOT NULL AND run = %s
        ''', [selected_run])

        with sqlite_connect(args.db) as conn:
            for row in tqdm.tqdm(curs, total=total_items, unit_scale=True):
                try:
                    conn.execute('''
                        INSERT INTO server_data (run, stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, result, input_data)
                        VALUES (:run, :stnum, :catalog, :code, :iterations, :duration, :ok, :gpa, :rank, :max_rank, json(:result), json(:input_data))
                    ''', dict(row))
                except Exception as e:
                    print(dict(row))
                    raise e

            conn.commit()


def init_local_db(args: argparse.Namespace) -> None:
    with sqlite_connect(args.db) as conn:
        conn.execute('''
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
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS server_data_key_idx ON server_data (stnum, catalog, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS server_data_cmp_idx ON server_data (ok, gpa, iterations, rank, max_rank)')
        conn.execute('CREATE INDEX IF NOT EXISTS server_data_duration_idx ON server_data (duration)')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS baseline (
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
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS baseline_key_idx ON baseline (stnum, catalog, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS baseline_cmp_idx ON baseline (ok, gpa, iterations, rank, max_rank)')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS branch (
                branch text not null,
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
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS branch_key_idx ON branch (branch, stnum, catalog, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS branch_cmp_idx ON branch (ok, gpa, iterations, rank, max_rank)')
        conn.execute('CREATE INDEX IF NOT EXISTS branch_cmp_branch_idx ON branch (branch, ok, gpa, iterations, rank, max_rank)')

        conn.commit()


def fetch__select_run(args: argparse.Namespace, conn: Any) -> int:
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


def baseline(args: argparse.Namespace) -> None:
    '''
    $ python3 testbed.py baseline
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

    with sqlite_connect(args.db) as conn:
        print('clearing baseline data... ', end='')
        conn.execute('DELETE FROM baseline')
        conn.commit()
        print('cleared')

    area_specs, records = prepare_audits(args)

    with sqlite_connect(args.db) as conn:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(audit, row, db=args.db, area_spec=area_specs[f"{row[1]}/{row[2]}"])
                for row in records
            ]

            for future in tqdm.tqdm(as_completed(futures), total=len(futures), disable=None):
                db_args = future.result()

                with sqlite_cursor(conn) as curs:
                    try:
                        curs.execute('''
                            INSERT INTO baseline (stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, result)
                            VALUES (:stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, json(:result))
                        ''', db_args)
                    except sqlite3.Error as ex:
                        print(db_args['stnum'], db_args['catalog'], db_args['code'], 'generated an exception', ex)
                        break

                    conn.commit()


def branch(args: argparse.Namespace) -> None:
    '''
    $ python3 testbed.py baseline
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

    with sqlite_connect(args.db) as conn:
        print(f'clearing data for "{args.branch}"... ', end='')
        conn.execute('DELETE FROM branch WHERE branch = ?', [args.branch])
        conn.commit()
        print('cleared')

    area_specs, records = prepare_audits(args)

    with sqlite_connect(args.db) as conn:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(audit, row, db=args.db, area_spec=area_specs[f"{row[1]}/{row[2]}"], run_id=args.branch)
                for row in records
            ]

            for future in tqdm.tqdm(as_completed(futures), total=len(futures), disable=None):
                try:
                    db_args = future.result()
                except Exception as exc:
                    print('generated an exception: %s' % (exc))
                    break

                with sqlite_cursor(conn) as curs:
                    try:
                        curs.execute('''
                            INSERT INTO branch (branch, stnum, catalog, code, iterations, duration, gpa, ok, rank, max_rank, result)
                            VALUES (:run, :stnum, :catalog, :code, :iterations, :duration, :gpa, :ok, :rank, :max_rank, json(:result))
                        ''', db_args)
                    except sqlite3.Error as ex:
                        print(db_args)
                        print(db_args['stnum'], db_args['catalog'], db_args['code'], 'generated an exception', ex)
                        break

                    conn.commit()


def prepare_audits(args: argparse.Namespace) -> Tuple[Dict[str, Any], Sequence[Tuple[str, str, str]]]:
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
            ORDER BY duration, stnum, catalog, code DESC
        ''', {'min': minimum_duration.sec()})

        records = [(stnum, catalog, code) for stnum, catalog, code in results]

    print(f'running {len(records):,} audits...')

    return area_specs, records


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


def audit(row: Tuple[str, str, str], *, db: str, area_spec: Dict, run_id: str = '') -> Optional[Dict]:
    stnum, catalog, code = row

    with sqlite_connect(db, readonly=True) as conn:
        results = conn.execute('''
            SELECT input_data
            FROM server_data
            WHERE (stnum, catalog, code) = (?, ?, ?)
        ''', [stnum, catalog, code])

        record = results.fetchone()
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
                    "result": json.dumps(result, sort_keys=True),
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

    columns = [
        'b.stnum',
        'b.catalog',
        'b.code',
        'b.gpa AS gpa_b',
        'r.gpa AS gpa_r',
        'b.iterations AS it_b',
        'r.iterations AS it_r',
        'round(b.duration, 4) AS dur_b',
        'round(r.duration, 4) AS dur_r',
        'b.ok AS ok_b',
        'r.ok AS ok_r',
        'round(b.rank, 2) AS rank_b',
        'round(r.rank, 2) AS rank_r',
        'b.max_rank AS max_b',
        'r.max_rank AS max_r',
    ]

    if args.mode == 'data':
        query = '''
            SELECT {}
            FROM baseline b
                LEFT JOIN branch r ON (b.stnum, b.catalog, b.code) = (r.stnum, r.catalog, r.code)
            WHERE r.branch = ? AND (
                b.ok != r.ok
                OR b.gpa != r.gpa
                OR b.rank != r.rank
                OR b.max_rank != r.max_rank
            )
            ORDER BY b.stnum, b.catalog, b.code
        '''.format(','.join(columns))

    elif args.mode == 'speed':
        query = '''
            SELECT {}
            FROM baseline b
                LEFT JOIN branch r ON (b.stnum, b.catalog, b.code) = (r.stnum, r.catalog, r.code)
            WHERE r.branch = ? AND b.iterations != r.iterations
            ORDER BY b.stnum, b.catalog, b.code
        '''.format(','.join(columns))

    elif args.mode == 'all':
        query = '''
            SELECT {}
            FROM baseline b
                LEFT JOIN branch r ON (b.stnum, b.catalog, b.code) = (r.stnum, r.catalog, r.code)
            WHERE r.branch = ?
            ORDER BY b.stnum, b.catalog, b.code
        '''.format(','.join(columns))

    else:
        assert False

    with sqlite_connect(args.db, readonly=True) as conn:
        results = [r for r in conn.execute(query, [args.run])]

        fields = ['stnum', 'catalog', 'code', 'gpa_b', 'gpa_r', 'it_b', 'it_r', 'dur_b', 'dur_r', 'ok_b', 'ok_r', 'rank_b', 'rank_r', 'max_b', 'max_r']
        writer = csv.DictWriter(sys.stdout, fieldnames=fields)
        writer.writeheader()

        counter: Dict[str, decimal.Decimal] = defaultdict(decimal.Decimal)
        for row in results:
            record = dict(row)

            for fieldkey, value in record.items():
                if type(value) in (int, float):
                    v = decimal.Decimal(value).quantize(decimal.Decimal("1.000"), rounding=decimal.ROUND_DOWN)
                    counter[fieldkey] += v

            writer.writerow(record)

        counter = {k: v.quantize(decimal.Decimal("1.000"), rounding=decimal.ROUND_DOWN) for k, v in counter.items()}
        writer.writerow({**counter, 'stnum': 'totals', 'catalog': '=======', 'code': '==='})
        averages = {k: (v / len(results)).quantize(decimal.Decimal("1.000"), rounding=decimal.ROUND_DOWN) for k, v in counter.items()}
        writer.writerow({**averages, 'stnum': 'avg', 'catalog': '=======', 'code': '==='})


def render(args: argparse.Namespace) -> None:
    stnum = args.stnum
    catalog = args.catalog
    code = args.code
    branch = args.branch

    with sqlite_connect(args.db, readonly=True) as conn:
        results = conn.execute('''
            SELECT d.input_data, b1.result as baseline, b2.result as branch
            FROM server_data d
            LEFT JOIN baseline b1 ON (b1.stnum, b1.catalog, b1.code) = (d.stnum, d.catalog, d.code)
            LEFT JOIN branch b2 ON (b2.stnum, b2.catalog, b2.code) = (d.stnum, d.catalog, d.code)
            WHERE d.stnum = :stnum
                AND d.catalog = :catalog
                AND d.code = :code
                AND b2.branch = :branch
        ''', {'catalog': catalog, 'code': code, 'stnum': stnum, 'branch': branch})

        record = results.fetchone()

        input_data = json.loads(record['input_data'])
        baseline_result = json.loads(record['baseline'])
        branch_result = json.loads(record['branch'])

        print('Baseline')
        print('========\n')

        print(render_result(input_data, baseline_result))

        print()
        print()
        print(f'Branch: {args.branch}')
        print('========\n')
        print(render_result(input_data, branch_result))


def render_result(student_data: Dict, result: Dict) -> str:
    courses = [load_course(row) for row in student_data["courses"]]
    transcript = {c.clbid: c for c in courses}

    return "\n".join(print_result(result, transcript=transcript, show_paths=False, show_ranks=False))


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
