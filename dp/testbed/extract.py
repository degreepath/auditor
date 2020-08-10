import argparse
import json
import sys

from .sqlite import sqlite_connect


def do_extract(args: argparse.Namespace) -> None:
    stnum = args.stnum
    code = args.code

    with sqlite_connect(args.db, readonly=True) as conn:
        results = conn.execute('''
            SELECT d.input_data
            FROM server_data d
            WHERE (d.stnum, d.code) = (:stnum, :code)
        ''', {'code': code, 'stnum': stnum})

        record = results.fetchone()
        if record is None:
            print('no record found', file=sys.stderr)
            sys.exit(1)

        input_data = json.loads(record['input_data'])

    with open(f'./{stnum}.json', 'w', encoding='utf-8') as outfile:
        json.dump(input_data, outfile, sort_keys=True, indent=2)


def extract_one(args: argparse.Namespace) -> None:
    do_extract(args)
    print(f'./{args.stnum}.json')
