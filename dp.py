import json
import sys
import time
import argparse
import logging
import coloredlogs
import traceback

import yaml

from degreepath import load_course, Constants, AreaOfStudy, summarize, AreaPointer, pretty_ms

logger = logging.getLogger(__name__)
logformat = "%(levelname)s %(name)s %(message)s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_files", nargs="+", required=True)
    parser.add_argument("--student", dest="student_files", nargs="+", required=True)
    parser.add_argument("--loglevel", dest="loglevel", choices=("warn", "debug", "info"))
    parser.add_argument("--json", action='store_true')
    parser.add_argument("--raw", action='store_true')
    parser.add_argument("--print-every", action='store_true')
    parser.add_argument("--color", action='store_true')
    args = parser.parse_args()

    if args.loglevel == "warn":
        coloredlogs.install(level="WARNING", fmt=logformat)
    elif args.loglevel == "debug":
        coloredlogs.install(level="DEBUG", fmt=logformat)
    elif args.loglevel == "info":
        coloredlogs.install(level="INFO", fmt=logformat)

    if not args.student_files:
        print("no students to process", file=sys.stderr)

    for student_file in args.student_files:
        with open(student_file, "r", encoding="utf-8") as infile:
            student = json.load(infile)

        area_pointers = tuple([AreaPointer.from_dict(**a) for a in student['areas']])

        transcript = [load_course(row) for row in student["courses"]]

        for area_file in args.area_files:
            with open(area_file, "r", encoding="utf-8") as infile:
                area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)

            print(f"auditing #{student['stnum']} against {area_file}", file=sys.stderr)

            constants = Constants(matriculation_year=student['matriculation'])

            try:
                (result, count, elapsed, iterations) = audit(
                    spec=area_spec,
                    transcript=transcript,
                    constants=constants,
                    area_pointers=area_pointers,
                    args=args,
                )

                if args.json:
                    if result:
                        print(json.dumps(result.to_dict()))
                    else:
                        print(json.dumps(result))
                elif args.raw:
                    print(result)
                else:
                    print()
                    if result:
                        print("".join(summarize(result=result.to_dict(), count=count, elapsed=elapsed, transcript=transcript, iterations=iterations)))
                    else:
                        print(result)

            except Exception:
                traceback.print_exc()
                print(f"failed: #{student['stnum']}", file=sys.stderr)

                break


def audit(*, spec, transcript, constants, area_pointers, args):
    area = AreaOfStudy.load(specification=spec, c=constants)
    area.validate()

    this_transcript = []
    attributes_to_attach = area.attributes.get("courses", {})
    for c in transcript:
        attrs_by_course = set(attributes_to_attach.get(c.course(), []))
        attrs_by_shorthand = set(attributes_to_attach.get(c.course_shorthand(), []))
        attrs_by_term = set(attributes_to_attach.get(c.course_with_term(), []))

        c = c.attach_attrs(attributes=attrs_by_course | attrs_by_shorthand | attrs_by_term)
        this_transcript.append(c)

    this_transcript = tuple(this_transcript)

    best_sol = None
    total_count = 0
    iterations = []
    start = time.perf_counter()
    iter_start = time.perf_counter()

    for sol in area.solutions(transcript=this_transcript, areas=area_pointers):
        total_count += 1

        if total_count % 1_000 == 0:
            recent_iters = iterations[-1_000:]
            avg_iter_s = sum(recent_iters) / max(len(recent_iters), 1)
            avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)
            print(f"... {total_count:,} at {avg_iter_time} per", file=sys.stderr)

        result = sol.audit(transcript=this_transcript, areas=area_pointers)

        if args.print_every:
            print("".join(summarize(result=result.to_dict(), count=total_count, elapsed='', transcript=this_transcript, iterations=[])))

        if best_sol is None:
            best_sol = result

        if result.rank() > best_sol.rank():
            best_sol = result

        if result.ok():
            best_sol = result
            iter_end = time.perf_counter()
            iterations.append(iter_end - iter_start)
            break

        iter_end = time.perf_counter()
        iterations.append(iter_end - iter_start)

        iter_start = time.perf_counter()

    if not iterations:
        print("no audits completed", file=sys.stderr)
        return (None, 0, '0s', [])

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    return (best_sol, total_count, elapsed, iterations)


if __name__ == "__main__":
    main()
