import argparse

from .sqlite import sqlite_connect


def query(args: argparse.Namespace) -> None:
    stnum = args.stnum
    catalog = args.catalog
    code = args.code

    with sqlite_connect(args.db, readonly=True) as conn:
        # conn.set_trace_callback(print)

        results = conn.execute('''
            SELECT stnum, catalog, code
            FROM server_data d
            WHERE
                CASE WHEN :stnum IS NULL THEN :stnum IS NULL ELSE d.stnum = :stnum END
                AND CASE WHEN :catalog IS NULL THEN :catalog IS NULL ELSE d.catalog = :catalog END
                AND CASE WHEN :code IS NULL THEN :code IS NULL ELSE d.code = :code END
        ''', {'stnum': stnum, 'catalog': catalog, 'code': code})

        for record in results:
            print(record['stnum'], record['catalog'], record['code'])
