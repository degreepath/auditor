import argparse
from .sqlite import sqlite_connect


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
            CREATE TABLE IF NOT EXISTS baseline_ip (
                stnum text not null,
                catalog text not null,
                code text not null,
                estimate integer not null,
                ts datetime not null default (datetime('now'))
            )
        ''')

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

        conn.execute('''
            CREATE TABLE IF NOT EXISTS branch_ip (
                branch text not null,
                stnum text not null,
                catalog text not null,
                code text not null,
                estimate integer not null,
                ts datetime not null default (datetime('now'))
            )
        ''')

        conn.commit()
