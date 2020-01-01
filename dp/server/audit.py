# mypy: warn_unreachable = False

import json
import logging
from typing import Dict, cast

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

from dp.run import run
from dp.ms import pretty_ms
from dp.audit import ResultMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments, EstimateMsg

logger = logging.getLogger(__name__)


def audit(*, area_spec: Dict, area_code: str, area_catalog: str, student: Dict, run_id: int, curs: psycopg2.extensions.cursor) -> None:
    args = Arguments()

    stnum = student['stnum']

    logger.info("auditing #%s against %s %s", stnum, area_catalog, area_code)
    with sentry_sdk.configure_scope() as scope:
        scope.user = {"id": stnum}

    curs.execute("""
        INSERT INTO result (  student_id,     area_code,     catalog,     run,     input_data, in_progress)
        VALUES             (%(student_id)s, %(area_code)s, %(catalog)s, %(run)s, %(student)s , true       )
        RETURNING id
    """, {"student_id": stnum, "area_code": area_code, "catalog": area_catalog, "run": run_id, "student": json.dumps(student)})

    row = curs.fetchone()
    result_id: int = cast(int, row[0])

    logger.info(f"result id = {result_id}")

    with sentry_sdk.configure_scope() as scope:
        scope.user = dict(id=stnum)
        scope.set_tag("area_code", area_code)
        scope.set_tag("catalog", area_catalog)
        scope.set_extra("result_id", result_id)

    try:
        for msg in run(args, area_spec=area_spec, student=student):
            if isinstance(msg, NoAuditsCompletedMsg):
                logger.critical('no audits completed')

            elif isinstance(msg, EstimateMsg):
                pass

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

            else:
                logger.critical('unknown message %s', msg)

    except Exception as ex:
        sentry_sdk.capture_exception(ex)

        curs.execute("""
            UPDATE result
            SET in_progress = false, error = %(error)s
            WHERE id = %(result_id)s
        """, {"result_id": result_id, "error": json.dumps({"error": str(ex)})})


def record(*, message: ResultMsg, curs: psycopg2.extensions.cursor, result_id: int) -> None:
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
