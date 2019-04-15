import logging
import glob
import time
import json
import sys
import pprint
import decimal
import collections
from pathlib import Path

import click
import coloredlogs
import yaml
import jsonpickle
import pendulum

from degreepath import CourseInstance, AreaOfStudy, CourseStatus
from degreepath.ms import pretty_ms

logger = logging.getLogger()
logformat = "%(levelname)s %(name)s: %(message)s"

def take(iter, n=5):
    for i, item in enumerate(iter):
        if i < n:
            yield item


@click.command()
@click.option("--print-every", "-e", default=1_000)
@click.option("--loglevel", "-l", default="warn")
@click.option("--record/--no-record", default=True)
@click.option("--estimate", default=None, is_flag=True)
@click.option("--print/--no-print", "stream", default=True)
@click.argument("student_file", nargs=-1, type=click.Path(exists=True))
def main(*, student_file, print_every, loglevel, record, stream, estimate):
    """Audits a student against their areas of study."""

    should_record = record
    should_print = stream

    if loglevel == "warn":
        logger.setLevel(logging.WARNING)
        coloredlogs.install(level="WARNING", logger=logger, fmt=logformat)
    elif loglevel == "debug":
        logger.setLevel(logging.DEBUG)
        coloredlogs.install(level="DEBUG", logger=logger, fmt=logformat)
    elif loglevel == "info":
        logger.setLevel(logging.INFO)
        coloredlogs.install(level="INFO", logger=logger, fmt=logformat)

    allowed = set(["Exercise Science", "Latin", "Social Work"])

    files = [
        "./gobbldygook-area-data/2015-16/major/exercise-science.yaml",
        "./gobbldygook-area-data/2018-19/major/latin.yaml",
        "./gobbldygook-area-data/2018-19/major/swrk.yaml",
    ]

    students = []
    for file in student_file:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        if set(data["majors"]).intersection(allowed):
            students.append(data)

    area_files = []
    for f in files:
        with open(f, "r", encoding="utf-8") as infile:
            area_files.append(yaml.load(stream=infile, Loader=yaml.SafeLoader))

    for i, data in enumerate(students):
        print(f"auditing #{data['stnum']}", file=sys.stderr)

        transcript = []
        for row in data["courses"]:
            try:
                transcript.append(CourseInstance.from_dict(**row))
            except:
                continue

        areas = set(data["majors"]).intersection(allowed)

        for area_name in areas:
            area_defs = [
                a for a in area_files if a["type"] == "major" and a["name"] == area_name
            ]
            area = AreaOfStudy.load(area_defs[0])

            area.validate()

            this_transcript = []
            for c in transcript:
                if area.attributes.get("courses", None):
                    attributes = area.attributes["courses"].get(c.course(), [])
                    c = c.attach_attrs(attributes=attributes)
                this_transcript.append(c)

            start = time.perf_counter()

            best_sol = None
            total_count = 0

            times = []

            iter_start = time.perf_counter()

            print(f"estimate: {area.estimate(transcript=this_transcript):,} possible combinations")

            if estimate:
                continue

            for sol in area.solutions(transcript=this_transcript):
                total_count += 1

                if total_count % print_every == 0:
                    print(f"... {total_count:,}", file=sys.stderr)

                result = sol.audit(transcript=this_transcript)

                if best_sol is None:
                    best_sol = result

                if result.rank() > best_sol.rank():
                    best_sol = result

                if result.ok():
                    iter_end = time.perf_counter()
                    times.append(iter_end - iter_start)
                    break

                iter_end = time.perf_counter()
                times.append(iter_end - iter_start)
                iter_start = time.perf_counter()

            if not times:
                print('no audits completed')
                continue

            if should_print:
                print()

            end = time.perf_counter()
            elapsed = pretty_ms((end - start) * 1000)

            # estimate = area.estimate(transcript=this_transcript)
            # print(f"estimated total count: {estimate:,}")
            # print()

            output = "".join(
                summarize(
                    name=data["name"],
                    stnum=data["stnum"],
                    area=area,
                    result=best_sol,
                    count=total_count,
                    elapsed=elapsed,
                    iterations=times,
                )
            )

            if should_record:
                filename = f'{data["stnum"]} {data["name"]}.txt'

                outdir = Path("./output")
                areadir = area.name.replace("/", "_")
                datestring = pendulum.now().format('MM MMMM DD')
                areadir = f"{areadir} - {datestring}"

                ok_path = outdir / areadir / "ok"
                ok_path.mkdir(parents=True, exist_ok=True)

                fail_path = outdir / areadir / "fail"
                fail_path.mkdir(parents=True, exist_ok=True)

                ok = best_sol.ok()

                container = ok_path if ok else fail_path
                otherpath = (ok_path if container == ok_path else fail_path) / filename

                if otherpath.exists():
                    otherpath.unlink()

                outpath = container / filename

                with outpath.open("w") as outfile:
                    outfile.write(output)

            if should_print:
                print(output)

        if i < len(student_file) and should_print:
            print()


def summarize(*, name, stnum, area, result, count, elapsed, iterations):
    times = [decimal.Decimal(t) for t in iterations]

    # chunked_times = [
    #     t.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_UP) for t in times
    # ]
    # counter = collections.Counter(chunked_times)
    # print(counter)

    avg_iter_s = sum(times) / len(times)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    endl = "\n"

    yield f'[#{stnum}] {name}\'s "{area.name}" {area.kind}'

    if result.ok():
        yield f" audit was successful."
    else:
        yield f" audit failed."

    yield f" (rank {result.rank()})"

    yield endl

    yield f"{count:,} attempts in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl

    dictver = result.to_dict()

    # print(f"The best solution we found was:")
    # print(json.dumps(dictver))

    yield endl

    yield "Results"
    yield endl
    yield "======="

    yield endl
    yield endl

    yield endl.join(print_result(dictver))

    yield endl


def print_result(rule, indent=0):
    prefix = " " * indent
    if rule.get("type", None) == "course":
        if rule.get("ok", None):
            if rule["status"] == CourseStatus.Ok.name:
                status = "✅ [ ok]"
            elif rule["status"] == CourseStatus.DidNotComplete.name:
                status = "⛔️ [dnf]"
            elif rule["status"] == CourseStatus.InProgress.name:
                status = "✅ [ ip]"
            elif rule["status"] == CourseStatus.Repeated.name:
                status = "✅ [rep]"
            elif rule["status"] == CourseStatus.NotTaken.name:
                status = "🌀      "
        else:
            status = "🌀      "

        yield f"{prefix}{status} {rule['course']}"

    elif rule.get("type", None) == "count":
        # print(rule)
        if "ok" in rule:
            if rule["ok"]:
                emoji = "✅"
            else:
                emoji = "⚠️ "
        else:
            emoji = "🌀"

        if rule["count"] == 1 and rule["size"] == 2:
            descr = f"either of (these {rule['size']})"
        elif rule["count"] == 2 and rule["size"] == 2:
            descr = f"both of (these {rule['size']})"
        elif rule["count"] == rule["size"]:
            descr = f"all of (these {rule['size']})"
        elif rule["count"] == 1:
            descr = f"any of (these {rule['size']})"
        else:
            descr = f"{rule['count']} of {rule['size']}"

        if "ok" in rule:
            ok_count = len([x for x in rule["of"] if "ok" in x and x["ok"]])
            descr += f" (ok: {ok_count}; need: {rule['count']})"

        yield f"{prefix}{emoji} {descr}"

        for r in rule["of"]:
            yield from print_result(r, indent=indent + 4)

        for x in rule["ignored"]:
            yield from print_result(x, indent=indent + 4)

    elif rule.get("type", None) == "requirement":
        if "ok" in rule:
            if rule["ok"]:
                emoji = "✅"
            else:
                emoji = "⚠️ "
        else:
            emoji = "🌀"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        yield from print_result(rule["result"], indent=indent + 4)

    else:
        yield json.dumps(rule, indent=2)


if __name__ == "__main__":
    main()
