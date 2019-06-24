import glob
import json
import logging
import pathlib
import sys
import time

import click
import coloredlogs
import pendulum
import yaml

from degreepath import (
    CourseInstance,
    AreaOfStudy,
    CourseStatus,
    Operator,
    str_clause,
    str_assertion,
)
from .ms import pretty_ms

logger = logging.getLogger()
logformat = "%(levelname)s %(name)s: %(message)s"


@click.command()
@click.option("--print-every", "-e", default=1000)
@click.option("--loglevel", "-l", default="warn")
@click.option("--print-all", default=False, is_flag=True)
@click.option("--record/--no-record", "should_record", default=True)
@click.option("--json", "print_json", default=False, is_flag=True)
@click.option("--print/--no-print", "should_print", default=True)
@click.option(
    "--area",
    "area_files",
    envvar="AREAS",
    multiple=True,
    required=True,
    type=click.Path(),
)
@click.option(
    "--student",
    "student_files",
    envvar="STUDENTS",
    multiple=True,
    required=True,
    type=click.Path(),
)
def main(
    *,
    student_files,
    print_every,
    loglevel,
    should_record,
    should_print,
    area_files,
    print_all,
    print_json,
):
    """Audits a student against their areas of study."""

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
    for globset in area_files:
        for f in glob.iglob(globset):
            with open(f, "r", encoding="utf-8") as infile:
                a = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            areas.append(a)

    students = []
    for file in student_files:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)
        students.append(data)

    run(
        students=students,
        areas=areas,
        print_every=print_every,
        should_record=should_record,
        should_print=should_print,
        print_all=print_all,
        print_json=print_json,
    )


def run(
    *, students, areas, print_every, should_record, should_print, print_all, print_json
):
    if not students:
        if not print_json:
            print("no students to process")

    for student in students:
        transcript = []
        for row in student["courses"]:
            instance = CourseInstance.from_dict(**row)
            if instance:
                transcript.append(instance)
            else:
                print("error loading course into transcript", row, file=sys.stderr)

        for area in areas:
            audit(
                area_def=area,
                transcript=transcript,
                student=student,
                print_every=print_every,
                should_print=should_print,
                should_record=should_record,
                print_all=print_all,
                print_json=print_json,
            )


def audit(
    *,
    area_def,
    transcript,
    student,
    print_every,
    should_print,
    should_record,
    print_all,
    print_json,
):
    if print_json:
        msg = {"stnum": student["stnum"], "action": "start", "area": area_def["name"]}
        print(json.dumps(msg))
    else:
        print(f"auditing #{student['stnum']} for {area_def['name']}", file=sys.stderr)

    area = AreaOfStudy.load(area_def)
    area.validate()

    this_transcript = []
    attributes_to_attach = area.attributes.get("courses", {})
    for c in transcript:
        attrs_by_course = attributes_to_attach.get(c.course(), [])
        attrs_by_shorthand = attributes_to_attach.get(c.course_shorthand(), [])

        c = c.attach_attrs(attributes=attrs_by_course or attrs_by_shorthand)
        this_transcript.append(c)

    best_sol = None
    total_count = 0
    times = []
    start = time.perf_counter()
    iter_start = time.perf_counter()

    for sol in area.solutions(transcript=this_transcript):
        total_count += 1

        if total_count % print_every == 0:
            if print_json:
                msg = {
                    "stnum": student["stnum"],
                    "action": "in-progress",
                    "count": total_count,
                }
                print(json.dumps(msg))
            else:
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

        if print_all:
            elapsed = pretty_ms((iter_end - start) * 1000)
            summary = summarize(
                name=student["name"],
                stnum=student["stnum"],
                area=area,
                result=result,
                count=total_count,
                elapsed=elapsed,
                iterations=times,
            )
            print("".join(summary))

        iter_start = time.perf_counter()

    if not times:
        if print_json:
            msg = {"stnum": student["stnum"], "action": "no-audits"}
            print(json.dumps(msg))
        else:
            print("no audits completed")
        return

    if should_print:
        if not print_json:
            print()

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    summary = summarize(
        name=student["name"],
        stnum=student["stnum"],
        area=area,
        result=best_sol,
        count=total_count,
        elapsed=elapsed,
        iterations=times,
    )
    output = "".join(summary)

    if should_print:
        if print_json:
            avg_iter_s = sum(times) / max(len(times), 1)
            avg_iter = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)
            msg = {
                "stnum": student["stnum"],
                "action": "complete",
                "area": area.to_dict(),
                "result": best_sol.to_dict(),
                "count": total_count,
                "student": student,
                "avg_iter": avg_iter,
                "elapsed": elapsed,
            }
            print(json.dumps(msg))
        else:
            print(output)

    if should_record:
        filename = f'{student["stnum"]} {student["name"]}.txt'

        outdir = pathlib.Path("./output")
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


def summarize(*, name, stnum, area, result, count, elapsed, iterations):
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    endl = "\n"

    yield f'[#{stnum}] {name}\'s "{area.name}" {area.kind}'

    if result.ok():
        yield f" audit was successful."
    else:
        yield f" audit failed."

    yield f" (rank {result.rank()})"

    yield endl

    word = "attempt" if count == 1 else "attempts"
    yield f"{count:,} {word} in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl

    dictver = result.to_dict()

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

    if rule is None:
        yield f"{prefix}???"
        return

    rule_type = rule["type"]

    if rule_type == "course":
        status = "🌀      "
        if "ok" in rule and rule["ok"]:
            claim = rule["claims"][0]["claim"]
            course = claim["course"]

            if course["status"] == CourseStatus.Ok.name:
                status = "💚 [ ok]"
            elif course["status"] == CourseStatus.DidNotComplete.name:
                status = "⛔️ [dnf]"
            elif course["status"] == CourseStatus.InProgress.name:
                status = "💚 [ ip]"
            elif course["status"] == CourseStatus.Repeated.name:
                status = "💚 [rep]"
            elif course["status"] == CourseStatus.NotTaken.name:
                status = "🌀      "

        yield f"{prefix}{status} {rule['course']}"

    elif rule_type == "count":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

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

    elif rule_type == "from":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        yield f"{prefix}{emoji} Given courses matching {str_clause(rule['where'])}"

        if rule["claims"]:
            yield f"{prefix} Matching courses:"
            for c in rule["claims"]:
                yield f"{prefix}   {c['claim']['course']['shorthand']} \"{c['claim']['course']['name']}\" ({c['claim']['course']['clbid']})"

        if rule["failures"]:
            yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
            for c in rule["failures"]:
                yield f"{prefix}   {c['claim']['course']['shorthand']} \"{c['claim']['course']['name']}\" ({c['claim']['course']['clbid']})"

        action = rule["action"]
        yield f"{prefix} There must be {str_assertion(action)} (have: {len(rule['claims'])}; need: {action['min']})"

    elif rule_type == "requirement":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        if rule["audited_by"] is not None:
            yield f"{prefix}    Audited by: {rule['audited_by']}; assuming success"
            return
        yield from print_result(rule["result"], indent=indent + 4)

    elif rule_type == "reference":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        yield f"{prefix}   [Skipped]"

    else:
        yield json.dumps(rule, indent=2)


if __name__ == "__main__":
    main()
