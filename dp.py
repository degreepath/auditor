from typing import Any, Iterator, Tuple, Dict
import argparse
import logging
import runpy
import json
import sys
import os
import dotenv
import prettyprinter  # type: ignore
from collections import defaultdict

from degreepath.ms import pretty_ms
from degreepath.stringify import summarize
from degreepath.stringify_csv import to_csv
from degreepath.area import AreaResult
from degreepath.audit import NoStudentsMsg, ResultMsg, AuditStartMsg, ExceptionMsg, NoAuditsCompletedMsg, ProgressMsg, Arguments, AreaFileNotFoundMsg

dirpath = os.path.dirname(os.path.abspath(__file__))
dp = runpy.run_path(dirpath + '/dp-common.py')

prettyprinter.install_extras(['attrs', 'dataclasses'])
dotenv.load_dotenv(verbose=False)

logger = logging.getLogger(__name__)
# logformat = "%(levelname)s:%(name)s:%(message)s"
logformat = "%(asctime)s %(name)s %(levelname)s %(message)s"


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    parser.add_argument("--archive", dest="archive_file")
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info", "critical"), default="info")
    parser.add_argument("--json", action='store_true')
    parser.add_argument("--csv", action='store_true')
    parser.add_argument("--raw", action='store_true')
    parser.add_argument("--print-all", action='store_true')
    parser.add_argument("--estimate", action='store_true')
    parser.add_argument("--transcript", action='store_true')
    parser.add_argument("--gpa", action='store_true')
    parser.add_argument("-q", "--quiet", action='store_true')
    parser.add_argument("--tracemalloc-init", action='store_true')
    parser.add_argument("--tracemalloc-end", action='store_true')
    parser.add_argument("--tracemalloc-each", action='store_true')
    parser.add_argument("--paths", dest='show_paths', action='store_const', const=True, default=True)
    parser.add_argument("--no-paths", dest='show_paths', action='store_const', const=False)
    parser.add_argument("--ranks", dest='show_ranks', action='store_const', const=True, default=True)
    parser.add_argument("--no-ranks", dest='show_ranks', action='store_const', const=False)
    cli_args = parser.parse_args()

    loglevel = getattr(logging, cli_args.loglevel.upper())
    logging.basicConfig(level=loglevel, format=logformat)

    if cli_args.estimate:
        os.environ['DP_ESTIMATE'] = '1'

    has_tracemalloc = cli_args.tracemalloc_init or cli_args.tracemalloc_end or cli_args.tracemalloc_each

    args = Arguments(
        area_files=cli_args.area_files,
        student_files=cli_args.student_files,
        print_all=cli_args.print_all,
        archive_file=cli_args.archive_file,
    )

    if has_tracemalloc:
        import tracemalloc
        tracemalloc.start()

    first_progress_message = True

    top_mem_items: Dict[str, Dict[int, float]] = defaultdict(dict)
    tracemalloc_index = 0

    for msg in dp['run'](args, transcript_only=cli_args.transcript, gpa_only=cli_args.gpa):
        if isinstance(msg, NoStudentsMsg):
            logger.critical('no student files provided')
            return 3

        elif isinstance(msg, NoAuditsCompletedMsg):
            logger.critical('no audits completed')
            return 2

        elif isinstance(msg, AuditStartMsg):
            if not cli_args.quiet:
                print(f"auditing #{msg.stnum} against {msg.area_catalog} {msg.area_code}", file=sys.stderr)

        elif isinstance(msg, ExceptionMsg):
            logger.critical("%s %s\n%s %s", msg.stnum, msg.area_code, msg.ex, msg.tb)
            return 1

        elif isinstance(msg, AreaFileNotFoundMsg):
            pass

        elif isinstance(msg, ProgressMsg):
            if (cli_args.tracemalloc_init and first_progress_message) or cli_args.tracemalloc_each:
                snapshot = tracemalloc.take_snapshot()
                for k, v in process_top(snapshot):
                    top_mem_items[k][tracemalloc_index] = v
                tracemalloc_index += 1

            first_progress_message = False

            if not cli_args.quiet or (cli_args.tracemalloc_init or cli_args.tracemalloc_each):
                avg_iter_s = sum(msg.recent_iters) / max(len(msg.recent_iters), 1)
                avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True)
                print(f"{msg.count:,} at {avg_iter_time} per audit (best: {msg.best_rank})", file=sys.stderr)

        elif isinstance(msg, ResultMsg):
            if not cli_args.quiet:
                print(result_str(
                    msg,
                    as_json=cli_args.json,
                    as_raw=cli_args.raw,
                    as_csv=cli_args.csv,
                    gpa_only=cli_args.gpa,
                    show_paths=cli_args.show_paths,
                    show_ranks=cli_args.show_ranks,
                ))

        else:
            if not cli_args.quiet:
                logger.critical('unknown message %s', msg)
            return 1

    if cli_args.tracemalloc_end:
        snapshot = tracemalloc.take_snapshot()
        for k, v in process_top(snapshot):
            top_mem_items[k][tracemalloc_index] = v

    if has_tracemalloc:
        longest = max(index for item in top_mem_items.values() for index, datapoint in item.items())
        for tracemalloc_index in range(0, longest + 1):
            print(tracemalloc_index * 10_000, end='\t')

        for file, datapoints in top_mem_items.items():
            print(file, end='\t')
            for i in range(0, longest + 1):
                print(f"{datapoints.get(i, 0):.1f}", end='\t')
            print()

    return 0


def result_str(
    msg: ResultMsg, *,
    as_json: bool,
    as_raw: bool,
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

    if as_raw:
        prettyprinter.cpprint(dict_result)
        return ''

    dict_result = json.loads(json.dumps(dict_result))

    return "\n" + "".join(summarize(
        result=dict_result,
        transcript=msg.transcript,
        count=msg.count,
        elapsed=msg.elapsed,
        iterations=msg.iterations,
        show_paths=show_paths,
        show_ranks=show_ranks,
        claims=msg.result.keyed_claims(),
    ))


def process_top(snapshot: Any, key_type: str = 'lineno', limit: int = 10) -> Iterator[Tuple[str, float]]:
    from tracemalloc import Filter

    snapshot = snapshot.filter_traces((
        Filter(False, "<frozen importlib._bootstrap>"),
        Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        yield (f"{filename}:{frame.lineno}", stat.size / 1024)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        yield ("other", size / 1024)

    total = sum(stat.size for stat in top_stats)
    yield ("total", total / 1024)


def display_top(snapshot: Any, key_type: str = 'lineno', limit: int = 10) -> None:
    import linecache
    from tracemalloc import Filter

    snapshot = snapshot.filter_traces((
        Filter(False, "<frozen importlib._bootstrap>"),
        Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print("#%s: %s:%s: %.1f KiB" % (index, filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))

    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))


@prettyprinter.register_pretty(AreaResult)  # type: ignore
def pretty_arearesult(value: Any, ctx: Any) -> Any:
    return prettyprinter.pretty_call(ctx, AreaResult, result=value.result)


if __name__ == "__main__":
    sys.exit(main())
