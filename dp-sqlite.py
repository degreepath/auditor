import argparse
import json
import logging
import os
import runpy
from datetime import datetime
from typing import Optional, Any, Dict, cast, Iterator
import contextlib
import sqlite3
import time
import random

from degreepath.ms import pretty_ms
from degreepath.audit import NoStudentsMsg, ResultMsg, AuditStartMsg, ExceptionMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments, EstimateMsg, AreaFileNotFoundMsg

logger = logging.getLogger(__name__)
dirpath = os.path.dirname(os.path.abspath(__file__))
dp = runpy.run_path(dirpath + '/dp-common.py')


def cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file", required=True)
    parser.add_argument("--student", dest="student_file", required=True)
    parser.add_argument("--run", dest="run", type=int, required=True)
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info", "critical"), default="warn")
    args = parser.parse_args()

    loglevel = getattr(logging, args.loglevel.upper())
    logging.basicConfig(level=loglevel)

    main(student_file=args.student_file, area_file=args.area_file, run_id=args.run)


def main(area_file: str, student_file: str, run_id: int) -> None:
    with connect('result.db') as conn:
        init_tables(conn=conn)

        result_id = None

        args = Arguments(area_files=[area_file], student_files=[student_file], archive_file=None)

        for msg in dp['run'](args):
            if isinstance(msg, NoStudentsMsg):
                logger.critical('no student files provided')

            elif isinstance(msg, NoAuditsCompletedMsg):
                logger.critical('no audits completed')

            elif isinstance(msg, AuditStartMsg):
                logger.info("auditing #%s against %s %s", msg.stnum, msg.area_catalog, msg.area_code)

                result_id = make_result_id(conn=conn, stnum=msg.stnum, area_code=msg.area_code, catalog=msg.area_catalog, run=run_id)

            elif isinstance(msg, ExceptionMsg):
                if result_id is not None:
                    record_error(result_id=result_id, conn=conn, error={"error": str(msg.ex)})

            elif isinstance(msg, AreaFileNotFoundMsg):
                message = "Could not load area file"

                if result_id is not None:
                    record_error(result_id=result_id, conn=conn, error={"error": message, "stnum": msg.stnum, "area_file": msg.area_file})

            elif isinstance(msg, ProgressMsg):
                avg_iter_s = sum(msg.recent_iters) / max(len(msg.recent_iters), 1)
                avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)
                update_progress(conn=conn, start_time=msg.start_time, count=msg.count, result_id=result_id)
                logger.info(f"{msg.count:,} at {avg_iter_time} per audit")

            elif isinstance(msg, ResultMsg):
                record(conn=conn, result_id=result_id, message=msg)

            elif isinstance(msg, EstimateMsg):
                pass

            else:
                logger.critical('unknown message %s', msg)


@contextlib.contextmanager
def connect(filename: str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(filename, isolation_level=None)
    conn.execute('pragma journal_mode=wal;')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def cursor(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    curs = conn.cursor()
    try:
        yield curs
    finally:
        curs.close()


@contextlib.contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    # We must issue a "BEGIN" explicitly when running in auto-commit mode.
    conn.execute('BEGIN')
    try:
        # Yield control back to the caller.
        yield
    except Exception:
        conn.rollback()  # Roll back all changes if an exception occurs.
        raise
    else:
        for n in range(10):
            try:
                conn.commit()
                return
            except sqlite3.OperationalError:
                time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
                if n == 9:
                    raise


def record(*, message: ResultMsg, conn: sqlite3.Connection, result_id: Optional[int]) -> None:
    result = message.result.to_dict()

    avg_iter_s = sum(message.iterations) / max(len(message.iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    with transaction(conn):
        conn.execute("""
            UPDATE result
            SET iterations = :total_count
              , duration = :elapsed
              , per_iteration = :avg_iter_time
              , rank = :rank
              , max_rank = :max_rank
              , result = :result
              , ok = :ok
              , ts = datetime('now')
              , gpa = :gpa
              , in_progress = false
            WHERE id = :result_id
        """, {
            "result_id": result_id,
            "total_count": message.count,
            "elapsed": message.elapsed,
            "avg_iter_time": avg_iter_time.strip("~"),
            "result": json.dumps(result),
            "rank": result["rank"],
            "max_rank": result["max_rank"],
            "gpa": result["gpa"],
            "ok": result["ok"],
        })

        for clause_hash, clbids in message.potentials_for_all_clauses.items():
            conn.execute("""
                INSERT INTO potential_clbids (result_id, clause_hash, clbids)
                VALUES (:result_id, :clause_hash, :clbids)
            """, {
                "result_id": result_id,
                "clause_hash": clause_hash,
                "clbids": json.dumps(clbids),
            })


def init_tables(*, conn: sqlite3.Connection) -> None:
    with transaction(conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS result (
                id INTEGER PRIMARY KEY,
                iterations INTEGER,
                duration TEXT,
                student_id TEXT,
                area_code TEXT,
                catalog TEXT,
                in_progress BOOLEAN,
                run INTEGER,
                error TEXT,
                per_iteration TEXT,
                rank NUMERIC,
                max_rank NUMERIC,
                result TEXT,
                ok BOOLEAN,
                ts TEXT,
                gpa NUMERIC
            )
        """)

        conn.execute("""CREATE INDEX IF NOT EXISTS result_area_code_index ON result (area_code)""")
        conn.execute("""CREATE INDEX IF NOT EXISTS result_catalog_index ON result (catalog)""")
        conn.execute("""CREATE INDEX IF NOT EXISTS result_ok_index ON result (ok)""")
        conn.execute("""CREATE INDEX IF NOT EXISTS result_run_index ON result (run)""")
        conn.execute("""CREATE INDEX IF NOT EXISTS result_student_id_index ON result (student_id)""")
        conn.execute("""CREATE INDEX IF NOT EXISTS result_multi_index ON result (student_id, area_code, run)""")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS potential_clbids (
                result_id INTEGER,
                clause_hash INTEGER,
                clbids TEXT
            )
        """)


def update_progress(*, conn: sqlite3.Connection, start_time: datetime, count: int, result_id: Optional[int]) -> None:
    with transaction(conn):
        conn.execute("""
            UPDATE result
            SET iterations = :count, duration = (strftime('%s','now') - strftime('%s', ts))
            WHERE id = :result_id
        """, {"result_id": result_id, "count": count, "start_time": start_time})


def make_result_id(*, stnum: str, conn: sqlite3.Connection, area_code: str, catalog: str, run: Optional[int]) -> Optional[int]:
    with cursor(conn) as curs:
        with transaction(conn):
            curs.execute("""
                INSERT INTO result (student_id, area_code, catalog, in_progress, run, ts)
                VALUES (:student_id, :area_code, :catalog, true, :run, datetime('now'))
            """, {"student_id": stnum, "area_code": area_code, "catalog": catalog, "run": run})

        return cast(int, curs.lastrowid)


def record_error(*, conn: sqlite3.Connection, result_id: int, error: Dict[str, Any]) -> None:
    with transaction(conn):
        conn.execute("""
            UPDATE result
            SET in_progress = false, error = :error
            WHERE id = :result_id
        """, {"result_id": result_id, "error": json.dumps(error)})


if __name__ == "__main__":
    cli()
