# mypy: warn_unreachable = False

import json
import logging
from typing import Optional, Dict, cast

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

from dp.run import run
from dp.ms import pretty_ms
from dp.audit import NoStudentsMsg, ResultMsg, AuditStartMsg, ExceptionMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments, AreaFileNotFoundMsg, EstimateMsg

logger = logging.getLogger(__name__)


def audit(*, area_file: str, student_data: Dict, run_id: int, curs: psycopg2.extensions.cursor) -> None:
    result_id = None
    args = Arguments()

    for msg in run(args, area_files=[area_file], student_data=[student_data]):
        if isinstance(msg, NoStudentsMsg):
            logger.critical('no student files provided')

        elif isinstance(msg, NoAuditsCompletedMsg):
            logger.critical('no audits completed')

        elif isinstance(msg, AuditStartMsg):
            logger.info("auditing #%s against %s %s", msg.stnum, msg.area_catalog, msg.area_code)
            with sentry_sdk.configure_scope() as scope:
                scope.user = {"id": msg.stnum}

            curs.execute("""
                INSERT INTO result (student_id, area_code, catalog, in_progress, run, input_data)
                VALUES (%(student_id)s, %(area_code)s, %(catalog)s, true, %(run)s, %(student)s)
                RETURNING id
            """, {"student_id": msg.stnum, "area_code": msg.area_code, "catalog": msg.area_catalog, "run": run_id, "student": json.dumps(msg.student)})

            row = curs.fetchone()
            result_id = cast(int, row[0])

            logger.info("result id = %s", result_id)

            with sentry_sdk.configure_scope() as scope:
                scope.user = {"id": msg.stnum}
                scope.set_tag('area_code', msg.area_code)
                scope.set_tag('catalog', msg.area_catalog)
                scope.set_extra('result_id', result_id)

        elif isinstance(msg, ExceptionMsg):
            sentry_sdk.capture_exception(msg.ex)

            if result_id:
                error = {"error": str(msg.ex)}

                curs.execute("""
                    UPDATE result
                    SET in_progress = false, error = %(error)s
                    WHERE id = %(result_id)s
                """, {"result_id": result_id, "error": json.dumps(error)})

        elif isinstance(msg, AreaFileNotFoundMsg):
            message = "Could not load area file"

            for stnum in msg.stnums:
                with sentry_sdk.configure_scope() as scope:
                    scope.user = {"id": stnum}
                    scope.set_tag('area_file', msg.area_file)
                    sentry_sdk.capture_message(message)

        elif isinstance(msg, ProgressMsg):
            avg_iter_s = sum(msg.recent_iters) / max(len(msg.recent_iters), 1)
            avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

            curs.execute("""
                UPDATE result
                SET iterations = %(count)s, duration = cast(now() - %(start_time)s as interval)
                WHERE id = %(result_id)s
            """, {"result_id": result_id, "count": msg.count, "start_time": msg.start_time})

            logger.info(f"{msg.count:,} at {avg_iter_time} per audit")

        elif isinstance(msg, ResultMsg):
            record(curs=curs, result_id=result_id, message=msg)

        elif isinstance(msg, EstimateMsg):
            pass

        else:
            logger.critical('unknown message %s', msg)


def record(*, message: ResultMsg, curs: psycopg2.extensions.cursor, result_id: Optional[int]) -> None:
    result = message.result.to_dict()

    avg_iter_s = sum(message.iterations) / max(len(message.iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

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
