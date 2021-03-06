#!/usr/bin/env python3

"""Usage: python3 -m dp.bin.index <query>

Given a folder of student JSON files, caches their areas in a SQLite file within that folder, then executes <query> on
that db.

Output is intended to be piped to dp.bin.batch.

Defaults to the "max" folder matching the glob ~/2019-*.
"""

import argparse
import json
import glob
import os
import sqlite3


def main() -> int:
    default_dir = os.getenv('DP_STUDENT_DIR', default=max(glob.iglob(os.path.expanduser('~/2019-*'))))

    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default=default_dir)
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--more', action='store_true')
    parser.add_argument('--print', action='store_true')
    parser.add_argument('--print-file', action='store_true')
    parser.add_argument('query')

    args = parser.parse_args()

    index_path = os.path.join(args.dir, 'index.sqlite3')
    if args.print_file:
        print(index_path)
        return 0

    if args.clean:
        os.unlink(index_path)

    with sqlite3.connect(index_path) as conn:
        db = conn.cursor()

        db.execute('''
            create table if not exists area (
                  stnum varchar
                , name varchar
                , type varchar
                , catalog varchar
                , code varchar
                , dept varchar
                , status varchar
                , degree varchar
            )
        ''')

        files = {os.path.basename(f[:-5]) for f in glob.iglob(os.path.join(args.dir, '*.json'))}

        db.execute('select distinct stnum from area')

        known_stnums = {r[0] for r in db.fetchall()}
        to_index = files.difference(known_stnums)

        for i, stnum in enumerate(to_index):
            if i % 100 == 0:
                print(f'\rindexing {i}/{len(to_index)} items', end='')
            elif i + 1 == len(to_index):
                print(f'\rindexing {i + 1}/{len(to_index)} items', end='')

            with open(os.path.join(args.dir, f"{stnum}.json"), 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            for area in data['areas']:
                db.execute('''
                    insert into area (stnum, name, type, code, dept, status, degree, catalog)
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (str(data['stnum']), area['name'], area['kind'], area['code'], area.get('dept', ''), area['status'], area['degree'], area.get('catalog', data['catalog']).split('-')[0]))

        if to_index:
            print()

        db.execute(f'''
            select stnum, catalog || '-' || substr(catalog + 1, 3, 2), code, name, type
            from area
            where {args.query}
            order by stnum
        ''')

        for r in db.fetchall():
            if args.more:
                print(' '.join(r))
            else:
                print(r[0], r[1], r[2])

    return 0


if __name__ == '__main__':
    main()
