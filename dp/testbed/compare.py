import argparse
import decimal
import csv
import sys
from collections import defaultdict
from typing import Dict

from .sqlite import sqlite_connect


def compare(args: argparse.Namespace) -> None:
    # check to see if the branch has any results
    with sqlite_connect(args.db, readonly=True) as conn:
        count_results = conn.execute('''
            SELECT count(*) AS count
            FROM branch
            WHERE branch = ?
        ''', [args.run])

        count = count_results.fetchone()[0]

        assert count > 0, f'no records found for branch "{args.run}"'

    with sqlite_connect(args.db, readonly=False) as conn:
        conn.execute('DROP VIEW IF EXISTS changes')

        conn.execute('''
            CREATE VIEW changes AS
            SELECT r.branch,
                b.stnum,
                b.catalog,
                b.code,
                b.gpa AS gpa,
                r.gpa AS gpa_r,
                b.iterations AS it,
                r.iterations AS it_r,
                round(b.duration, 4) AS dur,
                round(r.duration, 4) AS dur_r,
                b.status AS stat,
                r.status AS stat_r,
                round(b.rank, 2) AS rank,
                round(r.rank, 2) AS rank_r,
                b.max_rank AS max,
                r.max_rank AS max_r,
                b.ok AS ok,
                r.ok AS ok_r
            FROM baseline b
                LEFT JOIN branch r ON (b.stnum, b.catalog, b.code) = (r.stnum, r.catalog, r.code)
            WHERE b.ok != r.ok
                OR b.gpa != r.gpa
                OR b.rank != r.rank
                OR b.max_rank != r.max_rank
            ORDER BY
                b.stnum,
                b.catalog,
                b.code
        ''')

    if args.mode == 'data':
        query = '''
            SELECT *
            FROM changes
            WHERE branch = ?
        '''

    elif args.mode == 'ok':
        query = '''
            SELECT *
            FROM changes
            WHERE branch = ? AND ok != ok_r
        '''

    elif args.mode == 'gpa':
        query = '''
            SELECT *
            FROM changes
            WHERE branch = ? AND gpa != gpa_r
        '''

    else:
        assert False

    with sqlite_connect(args.db, readonly=True) as conn:
        results = [r for r in conn.execute(query, [args.run])]

        fields = ['branch', 'stnum', 'catalog', 'code', 'gpa', 'gpa_r', 'it', 'it_r', 'dur', 'dur_r', 'stat', 'stat_r', 'rank', 'rank_r', 'max', 'max_r', 'ok', 'ok_r']
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
        writer.writerow({**counter, 'stnum': 'sum', 'catalog': '=======', 'code': '===='})
        averages = {k: (v / count).quantize(decimal.Decimal("1.000"), rounding=decimal.ROUND_DOWN) for k, v in counter.items()}
        writer.writerow({**averages, 'stnum': 'avg', 'catalog': '=======', 'code': '===='})
