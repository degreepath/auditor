import argparse
import json
import logging
import os
import runpy
from datetime import datetime
from typing import Optional, Any, Dict, cast

import dotenv
import psycopg2  # type: ignore
import sentry_sdk

from degreepath.ms import pretty_ms
from degreepath.audit import NoStudentsMsg, ResultMsg, AuditStartMsg, ExceptionMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments, EstimateMsg, AreaFileNotFoundMsg

logger = logging.getLogger(__name__)
dirpath = os.path.dirname(os.path.abspath(__file__))
dp = runpy.run_path(dirpath + '/dp-common.py')

dotenv.load_dotenv(verbose=True)
if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))
else:
    logger.warning('SENTRY_DSN not set; skipping')


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


def main(area_file: str, student_file: str, run_id: Optional[int] = None) -> None:
    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST"),
        database=os.environ.get("PG_DATABASE"),
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
    )

    try:
        result_id = None

        args = Arguments(area_files=[area_file], student_files=[student_file])

        for msg in dp['run'](args):
            if isinstance(msg, NoStudentsMsg):
                logger.critical('no student files provided')

            elif isinstance(msg, NoAuditsCompletedMsg):
                logger.critical('no audits completed')

            elif isinstance(msg, AuditStartMsg):
                logger.info("auditing #%s against %s %s", msg.stnum, msg.area_catalog, msg.area_code)
                with sentry_sdk.configure_scope() as scope:
                    scope.user = {"id": msg.stnum}

                result_id = make_result_id(
                    conn=conn,
                    stnum=msg.stnum,
                    area_code=msg.area_code,
                    catalog=msg.area_catalog,
                    run=run_id,
                    student=msg.student,
                )
                logger.info("result id = %s", result_id)

                with sentry_sdk.configure_scope() as scope:
                    scope.user = {"id": msg.stnum}
                    scope.set_tag('area_code', msg.area_code)
                    scope.set_tag('catalog', msg.area_catalog)
                    scope.set_extra('result_id', result_id)

            elif isinstance(msg, ExceptionMsg):
                sentry_sdk.capture_exception(msg.ex)

                if result_id:
                    record_error(result_id=result_id, conn=conn, error={"error": str(msg.ex)})

            elif isinstance(msg, AreaFileNotFoundMsg):
                message = "Could not load area file"

                with sentry_sdk.configure_scope() as scope:
                    scope.user = {"id": msg.stnum}
                    scope.set_tag('area_file', msg.area_file)
                    sentry_sdk.capture_message(message)

                if result_id:
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

    finally:
        conn.close()


def record(*, message: ResultMsg, conn: Any, result_id: Optional[int]) -> None:
    result = message.result.to_dict()

    avg_iter_s = sum(message.iterations) / max(len(message.iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    with conn.cursor() as curs:
        curs.execute("""
            UPDATE result
            SET iterations = %(total_count)s
              , duration = interval %(elapsed)s
              , per_iteration = interval %(avg_iter_time)s
              , rank = %(rank)s
              , max_rank = %(max_rank)s
              , result = %(result)s::jsonb
              , ok = %(ok)s
              , ts = now()
              , gpa = %(gpa)s
              , in_progress = false
              , claimed_courses = %(claimed_courses)s::jsonb
            WHERE id = %(result_id)s
        """, {
            "result_id": result_id,
            "total_count": message.count,
            "elapsed": message.elapsed,
            "avg_iter_time": avg_iter_time.strip("~"),
            "result": json.dumps(result),
            "claimed_courses": json.dumps(message.result.keyed_claims()),
            "rank": result["rank"],
            "max_rank": result["max_rank"],
            "gpa": result["gpa"],
            "ok": result["ok"],
        })

        for clause_hash, clbids in message.potentials_for_all_clauses.items():
            curs.execute("""
                INSERT INTO potential_clbids (result_id, clause_hash, clbids)
                VALUES (%(result_id)s, %(clause_hash)s, %(clbids)s)
            """, {
                "result_id": result_id,
                "clause_hash": clause_hash,
                "clbids": clbids,
            })

        conn.commit()


def update_progress(*, conn: Any, start_time: datetime, count: int, result_id: Optional[int]) -> None:
    with conn.cursor() as curs:
        curs.execute("""
            UPDATE result
            SET iterations = %(count)s, duration = cast(now() - %(start_time)s as interval)
            WHERE id = %(result_id)s
        """, {"result_id": result_id, "count": count, "start_time": start_time})

        conn.commit()


def make_result_id(*, stnum: str, conn: Any, student: Dict[str, Any], area_code: str, catalog: str, run: Optional[int]) -> Optional[int]:
    with conn.cursor() as curs:
        curs.execute("""
            INSERT INTO result (student_id, area_code, catalog, in_progress, run, input_data)
            VALUES (%(student_id)s, %(area_code)s, %(catalog)s, true, %(run)s, %(student)s)
            RETURNING id
        """, {"student_id": stnum, "area_code": area_code, "catalog": catalog, "run": run, "student": json.dumps(student)})

        conn.commit()

        for row in curs:
            return cast(int, row[0])

    return None


def record_error(*, conn: Any, result_id: int, error: Dict[str, Any]) -> None:
    with conn.cursor() as curs:
        curs.execute("""
            UPDATE result
            SET in_progress = false, error = %(error)s
            WHERE id = %(result_id)s
        """, {
            "result_id": result_id,
            "error": json.dumps(error),
        })
        conn.commit()


if __name__ == "__main__":
    cli()
