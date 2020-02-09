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
            SELECT count(*) count
            FROM branch
            WHERE branch = ?
        ''', [args.run])

        record = count_results.fetchone()

        assert record['count'] > 0, f'no records found for branch "{args.run}"'

    def status_col(table: str) -> str:
        return f"""
            case {table}.status
                when 'done' then 'done'
                when 'failed-invariant' then 'fail'
                when 'needs-more-items' then 'part'
                else {table}.status
            end AS ok_{table}
        """

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
        status_col('b'),
        status_col('r'),
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

    elif args.mode == 'ok':
        query = '''
            SELECT {}
            FROM baseline b
                LEFT JOIN branch r ON (b.stnum, b.catalog, b.code) = (r.stnum, r.catalog, r.code)
            WHERE r.branch = ?
                AND b.ok != r.ok
            ORDER BY b.stnum, b.catalog, b.code
        '''.format(','.join(columns))

    elif args.mode == 'gpa':
        query = '''
            SELECT {}
            FROM baseline b
                LEFT JOIN branch r ON (b.stnum, b.catalog, b.code) = (r.stnum, r.catalog, r.code)
            WHERE r.branch = ?
                AND b.gpa != r.gpa
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
