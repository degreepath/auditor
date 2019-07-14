import glob
import json
import sys
import time
import datetime
import argparse

import yaml
import dotenv

from degreepath import (
    CourseInstance,
    AreaOfStudy,
    CourseStatus,
    Operator,
    str_clause,
    str_assertion,
    pretty_ms,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    parser.add_argument("--loglevel", dest="loglevel", nargs=1, choices=("warn", "debug", "info"))
    parser.add_argument("--json", action='store_true')
    args = parser.parse_args()

    if args.loglevel:
        import logging
        import coloredlogs

        logger = logging.getLogger()
        logformat = "%(levelname)s %(name)s: %(message)s"

        if args.loglevel == "warn":
            logger.setLevel(logging.WARNING)
            coloredlogs.install(level="WARNING", logger=logger, fmt=logformat)
        elif args.loglevel == "debug":
            logger.setLevel(logging.DEBUG)
            coloredlogs.install(level="DEBUG", logger=logger, fmt=logformat)
        elif args.loglevel == "info":
            logger.setLevel(logging.INFO)
            coloredlogs.install(level="INFO", logger=logger, fmt=logformat)

    areas = []
    for globset in args.area_files:
        for f in glob.iglob(globset):
            with open(f, "r", encoding="utf-8") as infile:
                a = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            areas.append(a)

    students = []
    for file in args.student_files:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)
        students.append(data)

    if not students:
        print("no students to process", file=sys.stderr)

    for student in students:
        transcript = []
        for row in student["courses"]:
            instance = CourseInstance.from_dict(**row)
            if instance:
                transcript.append(instance)
            else:
                print("error loading course into transcript", row, file=sys.stderr)

        for area in areas:
            (result_json, summary) = audit(area_def=area, transcript=transcript, student=student)

            if args.json:
                print(json.dumps(result_json))
            else:
                print("".join(summary))


def audit(*, area_def, transcript, student):
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
    start_time = datetime.datetime.now()
    iter_start = time.perf_counter()

    for sol in area.solutions(transcript=this_transcript):
        total_count += 1

        if total_count % 1_000 == 0:
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
        print("no audits completed", file=sys.stderr)
        return

    print()

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    result_json = result.to_dict()

    summary = summarize(
        stnum=student["stnum"],
        area=area,
        result=result_json,
        count=total_count,
        elapsed=elapsed,
        transcript=this_transcript,
        iterations=times,
    )

    return (result_json, summary)


def summarize(*, stnum, area, transcript, result, count, elapsed, iterations):
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    endl = "\n"

    yield f'#{stnum}\'s "{area.name}" {area.kind}'

    if result['ok']:
        yield f" audit was successful."
    else:
        yield f" audit failed."

    yield f" (rank {result['rank']})"

    yield endl

    word = "attempt" if count == 1 else "attempts"
    yield f"{count:,} {word} in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl

    yield endl

    yield "Results"
    yield endl
    yield "======="

    yield endl
    yield endl

    yield endl.join(print_result(result, transcript))

    yield endl


def print_result(rule, transcript, indent=0):
    prefix = " " * indent

    if rule is None:
        yield f"{prefix}???"
        return

    rule_type = rule["type"]

    if rule_type == "course":
        status = "🌀      "
        if "ok" in rule and rule["ok"]:
            claim = rule["claims"][0]["claim"]
            course = next(c for c in transcript if c.clbid == claim["clbid"])

            if course.status == CourseStatus.Ok:
                status = "💚 [ ok]"
            elif course.status == CourseStatus.DidNotComplete:
                status = "⛔️ [dnf]"
            elif course.status == CourseStatus.InProgress:
                status = "💚 [ ip]"
            elif course.status == CourseStatus.Repeated:
                status = "💚 [rep]"
            elif course.status == CourseStatus.NotTaken:
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
            yield from print_result(r, transcript, indent=indent + 4)

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
            for clm in rule["claims"]:
                course = next(c for c in transcript if c.clbid == clm['claim']["clbid"])
                yield f"{prefix}   {course.shorthand} \"{course.name}\" ({course.clbid})"

        if rule["failures"]:
            yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
            for clm in rule["failures"]:
                course = next(c for c in transcript if c.clbid == clm['claim']["clbid"])
                yield f"{prefix}   {course.shorthand} \"{course.name}\" ({course.clbid})"

        action = rule["action"]
        if 'min' in action:
            yield f"{prefix} There must be {str_assertion(action)} (have: {len(rule['claims'])}; need: {action['min']})"
        else:
            yield f"{prefix} There must be {str_assertion(action)} (have: {len(rule['claims'])}; need: N)"

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
        yield from print_result(rule["result"], transcript, indent=indent + 4)

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
