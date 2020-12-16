import argparse
from .sqlite import sqlite_connect, sqlite_cursor, Connection


def init_local_db(args: argparse.Namespace) -> None:
    with sqlite_connect(args.db) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS server_data (
                run integer not null,
                stnum text not null,
                catalog text not null,
                code text not null,
                iterations integer not null,
                duration real not null,
                gpa real not null,
                ok boolean not null,
                rank real not null,
                max_rank real not null,
                result json not null,
                status text not null,
                input_data json not null,
                classification text,
                class text,
                name text
            )
        ''')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS server_data_key_idx ON server_data (stnum, catalog, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS server_data_cmp_idx ON server_data (ok, gpa, iterations, rank, max_rank)')
        conn.execute('CREATE INDEX IF NOT EXISTS server_data_duration_idx ON server_data (duration)')
        conn.execute('CREATE INDEX IF NOT EXISTS server_data_classification_idx ON server_data (classification)')
        conn.execute('CREATE INDEX IF NOT EXISTS server_data_class_idx ON server_data (class)')

    with sqlite_connect(args.db) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS baseline (
                stnum text not null,
                catalog text not null,
                code text not null,
                iterations integer not null,
                duration real not null,
                gpa real not null,
                ok boolean not null,
                rank real not null,
                max_rank real not null,
                status text not null,
                result json not null,
                classification text,
                class text,
                name text
            )
        ''')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS baseline_key_idx ON baseline (stnum, catalog, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS baseline_cmp_idx ON baseline (ok, gpa, iterations, rank, max_rank)')
        conn.execute('CREATE INDEX IF NOT EXISTS baseline_cmp_classification_idx ON baseline (classification, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS baseline_cmp_class_idx ON baseline (class, code)')

    with sqlite_connect(args.db) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS branch (
                branch text not null,
                stnum text not null,
                catalog text not null,
                code text not null,
                iterations integer not null,
                duration real not null,
                gpa real not null,
                ok boolean not null,
                rank real not null,
                max_rank real not null,
                status text not null,
                result json not null,
                classification text,
                class text,
                name text
            )
        ''')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS branch_key_idx ON branch (branch, stnum, catalog, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS branch_cmp_idx ON branch (ok, gpa, iterations, rank, max_rank)')
        conn.execute('CREATE INDEX IF NOT EXISTS branch_cmp_branch_idx ON branch (branch, ok, gpa, iterations, rank, max_rank)')
        conn.execute('CREATE INDEX IF NOT EXISTS branch_cmp_classification_idx ON branch (branch, classification, code)')
        conn.execute('CREATE INDEX IF NOT EXISTS branch_cmp_class_idx ON branch (branch, class, code)')

    with sqlite_connect(args.db) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS area_cache (
                path text not null primary key,
                key text not null,
                catalog text not null,
                code text not null,
                content text not null,
                as_json text not null
            )
        ''')
