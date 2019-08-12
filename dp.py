import argparse
import logging
import runpy
import json
import sys
import os

from degreepath import pretty_ms, summarize
from degreepath.audit import NoStudentsMsg, ResultMsg, AuditStartMsg, ExceptionMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments, EstimateMsg

dirpath = os.path.dirname(os.path.abspath(__file__))
dp = runpy.run_path(dirpath + '/dp-common.py')

logger = logging.getLogger(__name__)
# logformat = "%(levelname)s:%(name)s:%(message)s"
logformat = "%(asctime)s %(name)s %(levelname)s %(message)s"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info", "critical"), default="info")
    parser.add_argument("--json", action='store_true')
    parser.add_argument("--raw", action='store_true')
    parser.add_argument("--print-all", action='store_true')
    parser.add_argument("--estimate", action='store_true')
    parser.add_argument("--transcript", action='store_true')
    parser.add_argument("--gpa", action='store_true')
    cli_args = parser.parse_args()

    loglevel = getattr(logging, cli_args.loglevel.upper())
    logging.basicConfig(level=loglevel, format=logformat)

    args = Arguments(area_files=cli_args.area_files, student_files=cli_args.student_files, print_all=cli_args.print_all, estimate_only=cli_args.estimate)

    for msg in dp['run'](args, transcript_only=cli_args.transcript):
        if isinstance(msg, NoStudentsMsg):
            logger.critical('no student files provided')

        elif isinstance(msg, NoAuditsCompletedMsg):
            logger.critical('no audits completed')

        elif isinstance(msg, AuditStartMsg):
            print(f"auditing #{msg.stnum} against {msg.area_catalog} {msg.area_code}", file=sys.stderr)

        elif isinstance(msg, ExceptionMsg):
            logger.critical("%s %s", msg.ex, msg.tb)

        elif isinstance(msg, ProgressMsg):
            avg_iter_s = sum(msg.recent_iters) / max(len(msg.recent_iters), 1)
            avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)
            print(f"{msg.count:,} at {avg_iter_time} per audit (best: {msg.best_rank})", file=sys.stderr)

        elif isinstance(msg, ResultMsg):
            print(result_str(msg, as_json=cli_args.json, as_raw=cli_args.raw, gpa_only=cli_args.gpa))

        elif isinstance(msg, EstimateMsg):
            print(f"estimated iterations: {msg.estimate:,}", file=sys.stderr)

        else:
            logger.critical('unknown message %s', msg)


def result_str(msg: ResultMsg, *, as_json: bool = False, as_raw: bool = False, gpa_only: bool = False) -> str:
    if gpa_only:
        return f"GPA: {msg.gpa}"

    dict_result = msg.result.to_dict()
    dict_result['gpa'] = str(msg.gpa)

    if as_json:
        return json.dumps(dict_result)

    if as_raw:
        return repr(msg.result)

    return "\n" + "".join(summarize(
        result=dict_result, transcript=msg.transcript, gpa=msg.gpa,
        count=msg.count, elapsed=msg.elapsed, iterations=msg.iterations,
    ))


if __name__ == "__main__":
    main()
