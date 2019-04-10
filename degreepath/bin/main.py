import logging
import glob
import time
import json
import sys
import pprint
import decimal

import click
import coloredlogs
import yaml
import jsonpickle

from degreepath.esth import CourseInstance, AreaOfStudy

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logformat = "%(levelname)s %(message)s"
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
@click.argument('student_file', nargs=-1, type=click.Path(exists=True))
def main(student_file):
    """Audits a student against their areas of study."""


    for file in student_file:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        if 'Exercise Science' not in data['majors']:
            continue


    area_files = []
    for f in glob.iglob("./gobbldygook-area-data/2015-16/*/exercise-science.yaml"):
        with open(f, "r", encoding="utf-8") as infile:
            area_files.append(yaml.load(stream=infile, Loader=yaml.SafeLoader))


    for file in student_file:
        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        if 'Exercise Science' not in data['majors']:
            continue

        print(f"auditing {file}", file=sys.stderr)

        transcript = []
        for row in data["courses"]:
            try:
                transcript.append(CourseInstance.from_dict(**row))
            except:
                continue

        areas = [m for m in data['majors'] if m == 'Exercise Science']

        for area_name in areas:
            area = AreaOfStudy.load(next(a for a in area_files if a['type'] == 'major' and a['name'] == area_name))

            area.validate()

            this_transcript = []
            for c in transcript:
                if area.attributes.get('courses', None):
                    c = c.attach_attrs(attributes=area.attributes["courses"].get(c.course(), []))
                this_transcript.append(c)

            # outname = f'./tmp/{area.kind}/{data["stnum"]}.{area.name.replace("/", "_")}.json'
            # with open(outname, "w", encoding="utf-8") as outfile:
            #     jsonpickle.set_encoder_options("json", sort_keys=True, indent=4)
            #     outfile.write(jsonpickle.encode(area, unpicklable=True))

            start = time.perf_counter()

            best_sol = None
            the_count = 0
            for sol in area.solutions(transcript=this_transcript):
                the_count += 1

                if the_count % 500 == 0:
                    print(f"... {the_count}", file=sys.stderr)

                result = sol.audit(transcript=this_transcript)

                # print(json.dumps(result.to_dict()))

                if best_sol is None:
                    best_sol = result

                # print(result.rank(), best_sol.rank())

                if result.rank() > best_sol.rank():
                    # print('found better')
                    best_sol = result

                if result.ok():
                    break

            # the_count = count(area.solutions(transcript=transcript), print_every=1_000)

            output = ""

            output += f"{the_count} attempted solutions"

            if best_sol.ok():
                ok = True
                output += f"\n{data['name']}'s \"{area.name}\" {area.kind} audit was successful."
            else:
                ok = False
                output += f"\n{data['name']}'s \"{area.name}\" {area.kind} audit failed."

            dictver = best_sol.to_dict()

            # print(f"The best solution we found was:")
            # print(json.dumps(dictver))

            output += '\nResults:\n'

            output += '\n'.join(print_result(dictver))

            end = time.perf_counter()
            output += f"\ntime: {decimal.Decimal(end - start).quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_UP)}s"

            with open(f'./output/{"ok" if ok else "fail"}/{data["stnum"]}.txt', 'w') as outfile:
                outfile.write(output)


def print_result(rule, indent=0):
    prefix = ' ' * indent
    if 'course' in rule:
        yield f"{prefix}{rule['course']}: {'ok' if rule['ok'] else 'missing'}"
    else:
        yield f"{prefix}{len(rule['items'])} of:"
        for r in rule['items']:
            yield from print_result(r, indent=indent+2)

if __name__ == "__main__":

    main()
