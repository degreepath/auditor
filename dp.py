import argparse
import logging
import runpy
import sys

from degreepath import pretty_ms, summarize
from degreepath.audit import NoStudentsMsg, ResultMsg, AuditStartMsg, ExceptionMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments

dp = runpy.run_path('./dp-common.py')

logger = logging.getLogger(__name__)
# logformat = "%(levelname)s:%(name)s:%(message)s"
logformat = "%(asctime)s %(name)s %(levelname)s %(message)s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info", "critical"), default="info")
    parser.add_argument("--json", action='store_true')
    parser.add_argument("--raw", action='store_true')
    parser.add_argument("--print-all", action='store_true')
    cli_args = parser.parse_args()

    loglevel = getattr(logging, cli_args.loglevel.upper())
    logging.basicConfig(level=loglevel, format=logformat)

    args = Arguments(area_files=cli_args.area_files, student_files=cli_args.student_files, print_all=cli_args.print_all)

    for msg in dp['run'](args):
        if isinstance(msg, NoStudentsMsg):
            logger.critical('no student files provided')

        elif isinstance(msg, NoAuditsCompletedMsg):
            logger.critical('no audits completed')

        elif isinstance(msg, AuditStartMsg):
            print(f"auditing #{msg.stnum} against {msg.area_catalog} {msg.area_code}", file=sys.stderr)

        elif isinstance(msg, ExceptionMsg):
            logger.critical("%s %s", msg.msg, msg.ex)

        elif isinstance(msg, ProgressMsg):
            avg_iter_s = sum(msg.recent_iters) / max(len(msg.recent_iters), 1)
            avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)
            print(f"{msg.count:,} at {avg_iter_time} per audit", file=sys.stderr)

        elif isinstance(msg, ResultMsg):
            print(result_str(msg, json=cli_args.json, raw=cli_args.raw))

        else:
            logger.critical('unknown message %s', msg)


def result_str(msg, *, json=False, raw=False):
    if json:
        return json.dumps(msg.result.to_dict() if msg.result is not None else None)

    if raw:
        return msg.result

    return "\n" + "".join(summarize(
        result=msg.result.to_dict() if msg.result is not None else None,
        count=msg.count, elapsed=msg.elapsed, iterations=msg.iterations,
        transcript=msg.transcript,
    ))


if __name__ == "__main__":
    main()
