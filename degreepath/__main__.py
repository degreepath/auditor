import logging
import time
import json
import sys
import decimal
import collections
import glob
from pathlib import Path

import click
import coloredlogs
import pendulum
import yaml

from . import CourseInstance, AreaOfStudy, CourseStatus, Operator, str_clause
from .ms import pretty_ms

logger = logging.getLogger()
logformat = "%(levelname)s %(name)s: %(message)s"


def take(it, n=5):
    for i, item in enumerate(it):
        if i < n:
            yield item


@click.command()
@click.option("--print-every", "-e", default=1000)
@click.option("--loglevel", "-l", default="warn")
@click.option("--print-all", default=False, is_flag=True)
@click.option("--record/--no-record", default=True)
@click.option("--json", "print_json", default=False, is_flag=True)
@click.option("--print/--no-print", "stream", default=True)
@click.option("--area", "area_files", envvar="AREAS", multiple=True)
@click.argument("student_file", nargs=-1, type=click.Path(exists=True))
def main(
    *,
    student_file,
    print_every,
    loglevel,
    record,
    stream,
    area_files,
    print_all,
    print_json,
):
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
    for globset in area_files:
        for f in glob.iglob(globset):
            with open(f, "r", encoding="utf-8") as infile:
                a = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            areas.append(a)
            allowed[a["type"]].add(a["name"])

    students = []
    for file in student_file:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        if set(data["degrees"]).intersection(allowed["degree"]):
            students.append(data)
        elif set(data["majors"]).intersection(allowed["major"]):
            students.append(data)
        elif set(data["concentrations"]).intersection(allowed["concentration"]):
            students.append(data)
        else:
            if print_json:
                msg = {
                    "stnum": data["stnum"],
                    "action": "skip",
                    "reason": f"skipping student {file} as their majors/degrees/concentrations were not loaded",
                }
                print(json.dumps(msg))
            else:
                print(
                    f"skipping student {file} as their majors/degrees/concentrations were not loaded"
                )

    run(
        students=students,
        areas=areas,
        allowed=allowed,
        print_every=print_every,
        should_record=should_record,
        should_print=should_print,
        print_all=print_all,
        print_json=print_json,
    )


def run(
    *,
    students,
    areas,
    allowed,
    print_every,
    should_record,
    should_print,
    print_all,
    print_json,
):
    if not students:
        if not print_json:
            print("no students to process")

    for i, student in enumerate(students):
        transcript = []
        for row in student["courses"]:
            instance = CourseInstance.from_dict(**row)
            if instance:
                transcript.append(instance)
            # try:
            #     transcript.append(CourseInstance.from_dict(**row))
            # except Exception as err:
            #     print(err)
            #     continue

        degree_names = set(student["degrees"])
        allowed_degree_names = degree_names.intersection(allowed["degree"])

        major_names = set(student["majors"])
        allowed_major_names = major_names.intersection(allowed["major"])

        conc_names = set(student["concentrations"])
        allowed_conc_names = conc_names.intersection(allowed["concentration"])

        allowed_area_names = (
            allowed_major_names | allowed_conc_names | allowed_degree_names
        )

        for area_name in allowed_area_names:
            area_def = next(a for a in areas if a["name"] == area_name)

            audit(
                area_def=area_def,
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
        msg = {"stnum": student["stnum"], "action": "start", "area": area_def['name']}
        print(json.dumps(msg))
    else:
        print(f"auditing #{student['stnum']} for {area_def['name']}", file=sys.stderr)

    area = AreaOfStudy.load(area_def)

    area.validate()

    this_transcript = []
    attributes_to_attach = area.attributes.get("courses", {})
    for c in transcript:
        attributes = attributes_to_attach.get(
            c.course(), []
        ) or attributes_to_attach.get(c.course_shorthand(), [])
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


def summarize(*, name, stnum, area, result, count, elapsed, iterations):
    times = [decimal.Decimal(t) for t in iterations]

    # chunked_times = [
    #     t.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_UP) for t in times
    # ]
    # counter = collections.Counter(chunked_times)
    # print(counter)

    avg_iter_s = sum(times) / max(len(times), 1)
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

        action_desc = ""
        action = rule["action"]
        if action["operator"] == Operator.GreaterThanOrEqualTo.name:
            action_desc = f"at least {action['compare_to']}"
        elif action["operator"] == Operator.GreaterThan.name:
            action_desc = f"at least {action['compare_to']}"
        elif action["operator"] == Operator.LessThanOrEqualTo.name:
            action_desc = f"at least {action['compare_to']}"
        elif action["operator"] == Operator.LessThan.name:
            action_desc = f"at least {action['compare_to']}"
        elif action["operator"] == Operator.EqualTo.name:
            action_desc = f"at least {action['compare_to']}"

        if action["source"] == "courses":
            word = "course" if action["compare_to"] == 1 else "courses"
        else:
            word = "items"

        yield f"{prefix} There must be {action_desc} matching {word} (have: {len(rule['claims'])}; need: {action['compare_to']})"

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
