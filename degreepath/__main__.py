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
import jsonpickle
import pendulum
import yaml

from . import CourseInstance, AreaOfStudy, CourseStatus
from .ms import pretty_ms

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
# @click.option("--estimate", default=None, is_flag=True)
@click.option("--print/--no-print", "stream", default=True)
@click.option(
    "--area", "area_files", envvar="AREAS", multiple=True, type=click.Path(exists=True)
)
@click.argument("student_file", nargs=-1, type=click.Path(exists=True))
def main(*, student_file, print_every, loglevel, record, stream, area_files):
    """Audits a student against their areas of study."""

    should_record = record
    should_print = stream

    if loglevel.lower() == "warn":
        logger.setLevel(logging.WARNING)
        coloredlogs.install(level="WARNING", logger=logger, fmt=logformat)
    elif loglevel.lower() == "debug":
        logger.setLevel(logging.DEBUG)
        coloredlogs.install(level="DEBUG", logger=logger, fmt=logformat)
    elif loglevel.lower() == "info":
        logger.setLevel(logging.INFO)
        coloredlogs.install(level="INFO", logger=logger, fmt=logformat)

    areas = []
    allowed = collections.defaultdict(set)
    for f in area_files:
        with open(f, "r", encoding="utf-8") as infile:
            a = yaml.load(stream=infile, Loader=yaml.SafeLoader)
        areas.append(a)
        allowed[a["type"]].add(a["name"])

    students = []
    for file in student_file:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        if set(data["majors"]).intersection(allowed["major"]):
            students.append(data)
        if set(data["concentrations"]).intersection(allowed["concentration"]):
            students.append(data)

    run(
        students=students,
        areas=areas,
        allowed=allowed,
        print_every=print_every,
        should_record=should_record,
        should_print=should_print,
    )


def run(*, students, areas, allowed, print_every, should_record, should_print):
    for i, student in enumerate(students):
        transcript = []
        for row in student["courses"]:
            try:
                transcript.append(CourseInstance.from_dict(**row))
            except:
                continue

        major_names = set(student["majors"])
        allowed_major_names = major_names.intersection(allowed["major"])

        conc_names = set(student["concentrations"])
        allowed_conc_names = conc_names.intersection(allowed["concentration"])

        allowed_area_names = allowed_major_names.union(allowed_conc_names)

        for area_name in allowed_area_names:
            area_def = next(a for a in areas if a["name"] == area_name)

            audit(
                area_def=area_def,
                transcript=transcript,
                student=student,
                print_every=print_every,
                should_print=should_print,
                should_record=should_record,
            )


def audit(*, area_def, transcript, student, print_every, should_print, should_record):
    print(f"auditing #{student['stnum']}", file=sys.stderr)

    area = AreaOfStudy.load(area_def)

    area.validate()

    this_transcript = []
    for c in transcript:
        attributes = area.attributes.get("courses", {}).get(c.course(), [])
        c = c.attach_attrs(attributes=attributes)
        this_transcript.append(c)

    start = time.perf_counter()

    best_sol = None
    total_count = 0

    times = []

    iter_start = time.perf_counter()

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
        print("no audits completed")
        return

    if should_print:
        print()

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    output = "".join(
        summarize(
            name=student["name"],
            stnum=student["stnum"],
            area=area,
            result=best_sol,
            count=total_count,
            elapsed=elapsed,
            iterations=times,
        )
    )

    if should_record:
        filename = f'{student["stnum"]} {student["name"]}.txt'

        outdir = Path("./output")
        areadir = area.name.replace("/", "_")
        datestring = pendulum.now().format("MM MMMM DD")
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

    # print(result)
    # import yaml
    # print(yaml.dump(result))
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


import pprint


def print_result(rule, indent=0):
    prefix = " " * indent

    # print(json.dumps(rule, indent=2))

    if rule is None:
        yield f"{prefix}???"
        return

    rule_type = rule["type"]

    if rule_type == "course":
        if rule["ok"]:
            course = rule["claims"][0]

            if course["status"] == CourseStatus.Ok.name:
                status = "✅ [ ok]"
            elif course["status"] == CourseStatus.DidNotComplete.name:
                status = "⛔️ [dnf]"
            elif course["status"] == CourseStatus.InProgress.name:
                status = "✅ [ ip]"
            elif course["status"] == CourseStatus.Repeated.name:
                status = "✅ [rep]"
            elif course["status"] == CourseStatus.NotTaken.name:
                status = "🌀      "
        else:
            status = "🌀      "

        yield f"{prefix}{status} {rule['course']}"

    elif rule_type == "count":
        if rule["status"] == "pass":
            emoji = "✅"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "⚠️"

        size = len(rule["items"])
        if rule["count"] == 1 and size == 2:
            descr = f"either of (these {size})"
        elif rule["count"] == 2 and size == 2:
            descr = f"both of (these {size})"
        elif rule["count"] == size:
            descr = f"all of (these {size})"
        elif rule["count"] == 1:
            descr = f"any of (these {size})"
        else:
            descr = f"{rule['count']} of {size}"

        ok_count = len([r for r in rule["items"] if r["ok"]])
        descr += f" (ok: {ok_count}; need: {rule['count']})"

        yield f"{prefix}{emoji} {descr}"

        for r in rule["items"]:
            yield from print_result(r, indent=indent + 4)

    elif rule_type == "requirement":
        if rule["status"] == "pass":
            emoji = "✅"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "⚠️"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        if rule["audited_by"] is not None:
            yield f"{prefix}    Audited by: {rule['audited_by']}; assuming success"
            return
        yield from print_result(rule["result"], indent=indent + 4)

    else:
        yield json.dumps(rule, indent=2)


if __name__ == "__main__":
    main()
