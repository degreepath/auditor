import json
import time
from typing import Optional, Tuple, Dict

from .sqlite import sqlite_connect

from dp.run import run
from dp.audit import ResultMsg, Arguments, EstimateMsg


def audit(
    row: Tuple[str, str, str],
    *,
    data: Optional[Dict] = None,
    db: str,
    area_spec: Dict,
    run_id: str = '',
    timeout: Optional[float] = None,
) -> Optional[Dict]:
    stnum, catalog, code = row

    if not data:
        with sqlite_connect(db, readonly=True) as conn:
            results = conn.execute('''
                SELECT input_data
                FROM server_data
                WHERE (stnum, catalog, code) = (?, ?, ?)
            ''', [stnum, catalog, code])

            record = results.fetchone()
            assert record is not None

            student = json.loads(record['input_data'])
            area_spec = area_spec
    else:
        student = data
        area_spec = area_spec

    estimate_count = estimate((stnum, catalog, code), db=db, area_spec=area_spec)
    assert estimate_count is not None

    db_keys = {'stnum': stnum, 'catalog': catalog, 'code': code, 'estimate': estimate_count, 'branch': run_id}

    start_time = time.perf_counter()

    for message in run(args=Arguments(), student=student, area_spec=area_spec):
        if isinstance(message, ResultMsg):
            result = message.result.to_dict()
            return {
                "run": run_id,
                "stnum": stnum,
                "catalog": catalog,
                "code": code,
                "iterations": message.iters,
                "duration": message.elapsed_ms / 1000,
                "gpa": result["gpa"],
                "ok": result["ok"],
                "rank": result["rank"],
                "max_rank": result["max_rank"],
                "result": json.dumps(result, sort_keys=True),
                "status": result["status"],
            }
        else:
            if timeout and time.perf_counter() - start_time >= timeout:
                raise TimeoutError(f'cancelling {" ".join(row)} after {time.perf_counter() - start_time}', db_keys)
            pass

    return None


def estimate(
    row: Tuple[str, str, str],
    *,
    data: Optional[Dict] = None,
    db: str,
    area_spec: Dict,
    run_id: str = '',
) -> Optional[int]:
    stnum, catalog, code = row

    if not data:
        with sqlite_connect(db, readonly=True) as conn:
            results = conn.execute('''
                SELECT input_data
                FROM server_data
                WHERE (stnum, catalog, code) = (?, ?, ?)
            ''', [stnum, catalog, code])

            record = results.fetchone()
            assert record is not None

            student = json.loads(record['input_data'])
            area_spec = area_spec
    else:
        student = data
        area_spec = area_spec

    for message in run(args=Arguments(estimate_only=True), student=student, area_spec=area_spec):
        if isinstance(message, EstimateMsg):
            return message.estimate
        else:
            assert False, type(message)

    return None
