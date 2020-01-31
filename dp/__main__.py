# mypy: warn_unreachable = False

from typing import Any, Iterator, Tuple, Dict
import argparse
import logging
import json
import sys
import os
import dotenv
from collections import defaultdict

from dp.run import run, load_student, load_area
from dp.ms import pretty_ms
from dp.stringify import summarize
from dp.stringify_csv import to_csv
from dp.audit import EstimateMsg, ResultMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments

dotenv.load_dotenv(verbose=False)

logger = logging.getLogger(__name__)
logformat = "%(asctime)s %(name)s %(levelname)s %(message)s"


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file")
    parser.add_argument("--student", dest="student_file")
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info", "critical"), default="info")
    parser.add_argument("--json", action='store_true')
    parser.add_argument("--csv", action='store_true')
    parser.add_argument("--print-all", action='store_true')
    parser.add_argument("--stop-after", action='store', type=int)
    parser.add_argument("--progress-every", action='store', type=int, default=1_000)
    parser.add_argument("--audit-each", action='store', type=int, default=1)
    parser.add_argument("--estimate", action='store_true')
    parser.add_argument("--transcript", action='store_true')
    parser.add_argument("--gpa", action='store_true')
    parser.add_argument("--quiet", "-q", action='store_true')
    parser.add_argument("--paths", dest='show_paths', action='store_const', const=True, default=True)
    parser.add_argument("--no-paths", dest='show_paths', action='store_const', const=False)
    parser.add_argument("--ranks", dest='show_ranks', action='store_const', const=True, default=True)
    parser.add_argument("--no-ranks", dest='show_ranks', action='store_const', const=False)
    cli_args = parser.parse_args()

    loglevel = getattr(logging, cli_args.loglevel.upper())
    logging.basicConfig(level=loglevel, format=logformat)

    if cli_args.estimate:
        os.environ['DP_ESTIMATE'] = '1'

    args = Arguments(
        gpa_only=cli_args.gpa,
        print_all=cli_args.print_all,
        progress_every=cli_args.progress_every,
        stop_after=cli_args.stop_after,
        audit_each=cli_args.audit_each,
        transcript_only=cli_args.transcript,
        estimate_only=cli_args.estimate,
    )

    student = load_student(cli_args.student_file)
    area_spec = load_area(cli_args.area_file)

    if not cli_args.quiet:
        print(f"auditing #{student['stnum']} against {cli_args.area_file}", file=sys.stderr)

    for msg in run(args, student=student, area_spec=area_spec):
        if isinstance(msg, NoAuditsCompletedMsg):
            logger.critical('no audits completed')
            return 2

        elif isinstance(msg, EstimateMsg):
            if not cli_args.quiet:
                print(f"{msg.estimate:,} estimated solution{'s' if msg.estimate != 1 else ''}", file=sys.stderr)

        elif isinstance(msg, ProgressMsg):
            if not cli_args.quiet:
                avg_iter_time = pretty_ms(msg.avg_iter_ms, format_sub_ms=True)

                addendum = ""
                if msg.iters != msg.total_iters:
                    addendum = f" (of {msg.total_iters:,} generated)"

                print(f"{msg.iters:,} checked{addendum} at {avg_iter_time} per check (best: #{msg.best_i} at {msg.best_rank})", file=sys.stderr)

        elif isinstance(msg, ResultMsg):
            if not cli_args.quiet:
                print(result_str(
                    msg,
                    as_json=cli_args.json,
                    as_csv=cli_args.csv,
                    gpa_only=cli_args.gpa,
                    show_paths=cli_args.show_paths,
                    show_ranks=cli_args.show_ranks,
                ))

        else:
            if not cli_args.quiet:
                logger.critical('unknown message %s', msg)
            return 1

    return 0


def result_str(
    msg: ResultMsg, *,
    as_json: bool,
    as_csv: bool,
    gpa_only: bool,
    show_paths: bool,
    show_ranks: bool,
) -> str:
    if gpa_only:
        return f"GPA: {msg.result.gpa()}"

    dict_result = msg.result.to_dict()

    if as_csv:
        return to_csv(dict_result, transcript=msg.transcript)

    if as_json:
        return json.dumps(dict_result)

    dict_result = json.loads(json.dumps(dict_result))

    return "\n" + "".join(summarize(
        result=dict_result,
        transcript=msg.transcript,
        final_index=msg.best_i,
        count=msg.iters,
        gen_count=msg.total_iters,
        avg_iter_ms=msg.avg_iter_ms,
        elapsed=pretty_ms(msg.elapsed_ms),
        show_paths=show_paths,
        show_ranks=show_ranks,
        claims=msg.result.keyed_claims(),
    ))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
