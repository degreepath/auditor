# mypy: warn_unreachable = False

from typing import List, Optional

import argparse
import logging
import json
import sys
import os

from .dotenv import load as load_dotenv
from .run import run, load_student, load_area
from .ms import pretty_ms
from .stringify_v3 import summarize
# from .stringify_csv import to_csv
from .audit import EstimateMsg, ResultMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments

logger = logging.getLogger(__name__)


def main(sys_args: Optional[List[str]] = None) -> int:  # noqa: C901
    if not sys_args:
        sys_args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file", help="the area specification file")
    parser.add_argument("--student", dest="student_file", help="the student data file")
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info", "critical"), default="info")
    parser.add_argument("--json", action='store_true', help="output results as json")
    parser.add_argument("--json-with-transcript", action='store_true', help="output results as json, including the course transcript")
    # parser.add_argument("--csv", action='store_true')
    parser.add_argument("--print-all", action='store_true', help="print every result, not just the best one")
    parser.add_argument("--print-only", action='store', nargs='?', type=str, help="print result for the specified iterations")
    parser.add_argument("--stop-after", action='store', type=int, metavar="N", help="stop checking results after N results have been checked")
    parser.add_argument("--progress-every", action='store', type=int, metavar="N", default=1_000, help="print a status message every N checks")
    parser.add_argument("--audit-each", action='store', type=int, default=1, metavar="N", help="only check every Nth result")
    parser.add_argument("--estimate", action='store_true', help="only estimate the number of checkable possibilities")
    parser.add_argument("--transcript", action='store_true', help="only print the transcript; do not audit")
    parser.add_argument("--gpa", action='store_true', help="only compute the GPA; do not audit")
    parser.add_argument("--quiet", "-q", action='store_true', help="be quiet")
    parser.add_argument("--print-path", action='store', help='the JSON array of text that indicates a requirement path')
    parser.add_argument("--paths", dest='show_paths', action='store_const', const=True, default=True)
    parser.add_argument("--no-paths", dest='show_paths', action='store_const', const=False)
    parser.add_argument("--ranks", dest='show_ranks', action='store_const', const=True, default=True)
    parser.add_argument("--no-ranks", dest='show_ranks', action='store_const', const=False)
    parser.add_argument("--claimed", dest='claimed', action='store_true')
    cli_args = parser.parse_args(sys_args)

    loglevel = getattr(logging, cli_args.loglevel.upper())
    logformat = "%(asctime)s %(name)s %(levelname)s %(message)s"
    logging.basicConfig(level=loglevel, format=logformat)

    if cli_args.estimate:
        os.environ['DP_ESTIMATE'] = '1'

    if cli_args.print_path:
        cli_args.print_path = json.loads(cli_args.print_path)
        assert isinstance(cli_args.print_path, list)

    args = Arguments(
        gpa_only=cli_args.gpa,
        print_all=cli_args.print_all,
        print_only=[int(x) for x in cli_args.print_only.split(',')] if cli_args.print_only else [],
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
                    as_json_and_transcript=cli_args.json_with_transcript,
                    # as_csv=cli_args.csv,
                    gpa_only=cli_args.gpa,
                    show_paths=cli_args.show_paths,
                    show_ranks=cli_args.show_ranks,
                    print_path=cli_args.print_path,
                    claimed=cli_args.claimed,
                ))

        else:
            if not cli_args.quiet:
                logger.critical('unknown message %s', msg)
            return 1

    return 0


def result_str(
    msg: ResultMsg, *,
    as_json: bool,
    as_json_and_transcript: bool,
    # as_csv: bool,
    gpa_only: bool,
    show_paths: bool,
    show_ranks: bool,
    claimed: bool,
    print_path: Optional[List[str]] = None,
) -> str:
    if gpa_only:
        return f"GPA: {msg.result.gpa()}"

    if claimed:
        claimed_courses = sorted((c.course for c in msg.result.claims()), key=lambda c: [c.subject, c.number, c.year, c.term, c.section])
        return ','.join(course.pretty() for course in claimed_courses)

    dict_result = msg.result.to_dict()

    # if as_csv:
    #     return to_csv(dict_result, transcript=msg.transcript)

    if as_json:
        return json.dumps(dict_result)

    if as_json_and_transcript:
        transcript = [c.to_dict() for c in msg.transcript]
        return json.dumps({'transcript': transcript, 'output': dict_result})

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
        only_path=print_path,
    ))


if __name__ == "__main__":
    load_dotenv()

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
