import logging
import glob
import time
import json
import sys
import pprint
import decimal
import collections

import click
import coloredlogs
import yaml
import jsonpickle

from degreepath import CourseInstance, AreaOfStudy, CourseStatus

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logformat = "%(levelname)s %(name)s: %(message)s"
coloredlogs.install(level="INFO", logger=logger, fmt=logformat)


def load_area(stream):
    data = yaml.load(stream=stream, Loader=yaml.SafeLoader)

    return AreaOfStudy.load(data)


def take(iterable, n):
    for i, item in enumerate(iterable):
        yield item
        if i + 1 >= n:
            break


def count(iterable, print_every=None):
    counter = 0
    for item in iterable:
        counter += 1
        if print_every is not None and counter % print_every == 0:
            print(f"... {counter}")
    return counter


@click.command()
@click.argument("student_file", nargs=-1, type=click.Path(exists=True))
def main(student_file):
    """Audits a student against their areas of study."""

    target = "Exercise Science"
    file_glob = glob.iglob("./gobbldygook-area-data/2015-16/*/exercise-science.yaml")

    # target = "Social Work"
    # file_glob = glob.iglob("./gobbldygook-area-data/2018-19/*/swrk.yaml")

    students = []
    for file in student_file:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        if target in data["majors"]:
            students.append(data)

    area_files = []
    for f in file_glob:
        with open(f, "r", encoding="utf-8") as infile:
            area_files.append(yaml.load(stream=infile, Loader=yaml.SafeLoader))

    for i, data in enumerate(students):
        print(f"auditing {data['stnum']}", file=sys.stderr)

        transcript = []
        for row in data["courses"]:
            try:
                transcript.append(CourseInstance.from_dict(**row))
            except:
                continue

        areas = [m for m in data["majors"] if m == target]

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

            printed_count = False
            best_sol = None
            the_count = 0

            times = []

            iter_start = time.perf_counter()
            for sol in area.solutions(transcript=this_transcript):
                the_count += 1

                if the_count % 1_000 == 0:
                    printed_count = True
                    print(f"... {the_count:,}", file=sys.stderr)

                result = sol.audit(transcript=this_transcript)

                iter_end = time.perf_counter()
                times.append(iter_end - iter_start)
                iter_start = time.perf_counter()

                if best_sol is None:
                    best_sol = result

                if result.rank() > best_sol.rank():
                    best_sol = result

                if result.ok():
                    break

            print()

            end = time.perf_counter()
            elapsed = decimal.Decimal(end - start).quantize(
                decimal.Decimal("0.01"), rounding=decimal.ROUND_UP
            )

            if not times:
                print('no audits completed')
                continue

            # estimate = area.estimate(transcript=this_transcript)
            # print(f"estimated total count: {estimate:,}")
            # print()

            output = "".join(
                summarize(
                    name=data["name"],
                    stnum=data["stnum"],
                    area=area,
                    result=best_sol,
                    count=the_count,
                    elapsed=elapsed,
                    iterations=times,
                )
            )

            subdir = "ok" if best_sol.ok() else "fail"
            filename = f'{data["stnum"]} {data["name"]}.txt'
            with open(f"./output/{subdir}/{filename}", "w") as outfile:
                outfile.write(output)
            print(output)

        if i < len(student_file):
            print()


def summarize(*, name, stnum, area, result, count, elapsed, iterations):
    times = [decimal.Decimal(t) for t in iterations]
    # chunked_times = [t.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_UP) for t in times]
    # counter = collections.Counter(chunked_times)

    avg_iter_time = (sum(times) / len(times)).quantize(
        decimal.Decimal("0.00001"), rounding=decimal.ROUND_UP
    )

    # print(counter)

    endl = "\n"

    yield f'[#{stnum}] {name}\'s "{area.name}" {area.kind}'

    if result.ok():
        yield f" audit was successful."
    else:
        yield f" audit failed."

    yield endl

    yield f"{count:,} attempts in {elapsed}s (avg {avg_iter_time}s per attempt)"
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

        # passed_courses = set(c["course"] for c in rule["items"] if "course" in c)
        # available_courses = set(c["course"] for c in rule["choices"] if "course" in c)
        # other_courses = sorted(available_courses.difference(passed_courses))

        for x in rule["ignored"]:
            yield from print_result(x, indent=indent + 4)
            # yield f"{' ' * (indent + 2)}{c}: skipped"
    elif rule.get('type', None) == 'requirement':
        if "ok" in rule:
            if rule["ok"]:
                emoji = "✅"
            else:
                emoji = "⚠️ "
        else:
            emoji = "🌀"
        # yield json.dumps(rule, indent=2)
        yield f"{prefix}{emoji} Requirement({rule['name']})"
        yield from print_result(rule['result'], indent=indent + 4)
    else:
        yield json.dumps(rule, indent=2)


if __name__ == "__main__":
    main()
