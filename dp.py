import glob
import json
import sys
import time
import datetime
import argparse

import yaml

from degreepath import CourseInstance, AreaOfStudy, summarize
from degreepath.ms import pretty_ms


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


if __name__ == "__main__":
    main()
