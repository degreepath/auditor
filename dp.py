import json
import sys
import time
import datetime
import argparse
import logging
import coloredlogs
import traceback

import yaml

from degreepath import CourseInstance, Constants, AreaOfStudy, summarize, AreaPointer
from degreepath.ms import pretty_ms

logger = logging.getLogger()
logformat = "%(levelname)s %(name)s: %(message)s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info"))
    parser.add_argument("--json", action='store_true')
    args = parser.parse_args()

    if args.loglevel == "warn":
        logger.setLevel(logging.WARNING)
        coloredlogs.install(level="WARNING", logger=logger, fmt=logformat)
    elif args.loglevel == "debug":
        logger.setLevel(logging.DEBUG)
        coloredlogs.install(level="DEBUG", logger=logger, fmt=logformat)
    elif args.loglevel == "info":
        logger.setLevel(logging.INFO)
        coloredlogs.install(level="INFO", logger=logger, fmt=logformat)

    if not args.student_files:
        print("no students to process", file=sys.stderr)

    for student_file in args.student_files:
        with open(student_file, "r", encoding="utf-8") as infile:
            student = json.load(infile)

        area_pointers = tuple([AreaPointer.from_dict(**a) for a in student['areas']])

        transcript = []
        for row in student["courses"]:
            instance = CourseInstance.from_dict(**row)
            if instance:
                transcript.append(instance)
            else:
                print("error loading course into transcript", row, file=sys.stderr)

        for area_file in args.area_files:
            with open(area_file, "r", encoding="utf-8") as infile:
                area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)

            print(f"auditing #{student['stnum']} against {area_file}", file=sys.stderr)

            constants = Constants(matriculation_year=student['matriculation'])

            try:
                (result_json, summary) = audit(
                    spec=area_spec,
                    transcript=transcript,
                    constants=constants,
                    area_pointers=area_pointers,
                )

                if args.json:
                    print(json.dumps(result_json))
                else:
                    print("".join(summary))

            except Exception as ex:
                traceback.print_exc()
                print(f"failed: #{student['stnum']}", file=sys.stderr)

                break


def audit(*, spec, transcript, constants, area_pointers):
    area = AreaOfStudy.load(specification=spec, c=constants)
    area.validate()

    this_transcript = []
    attributes_to_attach = area.attributes.get("courses", {})
    for c in transcript:
        attrs_by_course = attributes_to_attach.get(c.course(), [])
        attrs_by_shorthand = attributes_to_attach.get(c.course_shorthand(), [])

        c = c.attach_attrs(attributes=attrs_by_course or attrs_by_shorthand)
        this_transcript.append(c)

    this_transcript = tuple(this_transcript)

    best_sol = None
    total_count = 0
    times = []
    start = time.perf_counter()
    start_time = datetime.datetime.now()
    iter_start = time.perf_counter()

    for sol in area.solutions(transcript=this_transcript, areas=area_pointers):
        total_count += 1

        if total_count % 1_000 == 0:
            print(f"... {total_count:,}", file=sys.stderr)

        result = sol.audit(transcript=this_transcript, areas=area_pointers)

        if best_sol is None:
            best_sol = result

        if result.rank() > best_sol.rank():
            best_sol = result

        if result.ok():
            best_sol = result
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

    result_json = best_sol.to_dict()

    summary = summarize(
        result=result_json,
        count=total_count,
        elapsed=elapsed,
        transcript=this_transcript,
        iterations=times,
    )

    return (result_json, summary)


if __name__ == "__main__":
    main()
