from typing import Any
import argparse

import tqdm  # type: ignore

from .sqlite import sqlite_connect, sqlite_cursor
from dp.ms import pretty_ms


def fetch(args: argparse.Namespace) -> None:
    import psycopg2  # type: ignore
    import psycopg2.extras  # type: ignore

    # empty string means "use the environment variables"
    pg_conn = psycopg2.connect('', application_name='degreepath-testbed', cursor_factory=psycopg2.extras.DictCursor)
    pg_conn.set_session(readonly=True)

    selected_run = None
    if not args.latest:
        selected_run = fetch__select_run(args, pg_conn)

    with pg_conn.cursor() as curs:
        # language=PostgreSQL
        curs.execute('''
            SELECT count(*) total_count
            FROM result
            WHERE CASE
                WHEN %(run)s IS NOT NULL THEN run = %(run)s
                ELSE is_active = true
            END
        ''', dict(run=selected_run))

        total_items = curs.fetchone()['total_count']

    if args.latest:
        print(f"Fetching all {total_items:,} audits into {args.db!r}")
    else:
        print(f"Fetching run #{selected_run} with {total_items:,} audits into {args.db!r}")

    if args.clear:
        with sqlite_connect(args.db) as conn:
            print('clearing cached data... ', end='', flush=True)
            # noinspection SqlWithoutWhere
            # language=SQLite
            conn.execute('DELETE FROM server_data')
            conn.commit()
            print('cleared')

    # named cursors only allow one execute() call, so this must be its own block
    with pg_conn.cursor(name="degreepath_testbed") as curs:
        curs.itersize = 75

        # language=PostgreSQL
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
                 , status
                 , run
                 , student_classification as classification
                 , student_class as class
                 , student_name as name
            FROM result
            WHERE result IS NOT NULL
                AND CASE
                    WHEN %(run)s IS NOT NULL THEN run = %(run)s
                    ELSE is_active = true
                END
        ''', dict(run=selected_run))

        with sqlite_connect(args.db) as conn:
            for row in tqdm.tqdm(curs, total=total_items, unit_scale=True):
                try:
                    conn.execute('''
                        INSERT INTO server_data
                                (run,  stnum,  catalog,  code,  name,  class,  classification,  iterations,  duration,  ok,  gpa,  rank,  max_rank,  status,       result,        input_data)
                        VALUES (:run, :stnum, :catalog, :code, :name, :class, :classification, :iterations, :duration, :ok, :gpa, :rank, :max_rank, :status, json(:result), json(:input_data))
                    ''', dict(row))
                except Exception as e:
                    print(dict(row))
                    raise e

            conn.commit()


def fetch__select_run(args: argparse.Namespace, conn: Any) -> int:
    with conn.cursor() as curs:
        if args.latest:
            # language=PostgreSQL
            curs.execute('SELECT max(run) as max FROM result')
            to_fetch = curs.fetchone()['max']

        elif args.run:
            to_fetch = args.run

        else:
            fetch__print_summary(args=args, curs=curs)

            print('Download which run?')
            to_fetch = int(input('>>> '))

        return int(to_fetch)


def fetch__print_summary(args: argparse.Namespace, curs: Any) -> None:
    # language=PostgreSQL
    curs.execute("""
        SELECT run
             , min(ts AT TIME ZONE 'America/Chicago') AS first
             , max((ts + duration) AT TIME ZONE 'America/Chicago') AS last
             , extract(EPOCH FROM max((ts + duration)) - min(ts)) AS duration
             , count(*) AS total
             , coalesce(sum(1) FILTER(WHERE ok), 0) AS ok
             , coalesce(sum(1) FILTER(WHERE NOT ok), 0) AS "not-ok"
             , ((SELECT count(*) FROM queue WHERE run = r.run)) as queued
        FROM result r
        WHERE run > 0
          AND ts > now() - INTERVAL '1 week'
        GROUP BY run
        ORDER BY run DESC
    """)

    # 219: 2019-12-06 23:07 / 2019-12-07 04:40 [5h 32m 58.7s]; 6,997 total, 201 ok, 6,796 not-ok
    date_fmt = "%Y-%m-%d %H:%M"
    for row in curs.fetchall():
        first = row['first'].strftime(date_fmt)
        last = row['last'].strftime(date_fmt)
        duration = pretty_ms(row['duration'] * 1000, unit_count=2)
        queue_count = f", {row['queued']:,} queued" if row['queued'] else ''
        print(f"{row['run']}: {first} / {last} [{duration.ljust(10, ' ')}]; {row['total']:,} total, {row['ok']:,} ok, {row['not-ok']:,} not-ok{queue_count}")


def summarize(args: argparse.Namespace) -> None:
    import psycopg2
    import psycopg2.extras

    # empty string means "use the environment variables"
    pg_conn = psycopg2.connect('', application_name='degreepath-testbed', cursor_factory=psycopg2.extras.DictCursor)
    pg_conn.set_session(readonly=True)

    with pg_conn.cursor() as curs:
        fetch__print_summary(args=args, curs=curs)


def fetch_if_needed(args: argparse.Namespace) -> None:
    with sqlite_connect(args.db) as conn:
        with sqlite_cursor(conn) as curs:
            curs.execute('SELECT count(*) FROM server_data')

            if curs.fetchone()[0]:
                return
            else:
                raise Exception('run the fetch subcommand')
