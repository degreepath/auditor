import logging
import glob
import time
import json
import pprint

import click
import coloredlogs
import yaml
import jsonpickle

from degreepath import CourseInstance, AreaOfStudy

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

    area_files = []
    for f in glob.iglob("./gobbldygook-area-data/2018-19/*/exercise-science.yaml"):
        with open(f, "r", encoding="utf-8") as infile:
            area_files.append(yaml.load(stream=infile, Loader=yaml.SafeLoader))


    for file in student_file:
        print(f"auditing {file}")

        with open(file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        transcript = [CourseInstance.from_dict(**row) for row in data["courses"]]

        areas = [m for m in data['majors'] if m == 'Exercise Science']

        for area_name in areas:
            area = AreaOfStudy.load(next(a for a in area_files if a['type'] == 'major' and a['name'] == area_name))

            area.validate()

            this_transcript = []
            for c in transcript:
                if area.attributes.get('courses', None):
                    c = c.attach_attrs(attributes=area.attributes["courses"].get(c.course(), []))
                this_transcript.append(c)

            outname = f'./tmp/{area.kind}/{data["stnum"]}.{area.name.replace("/", "_")}.json'
            with open(outname, "w", encoding="utf-8") as outfile:
                jsonpickle.set_encoder_options("json", sort_keys=True, indent=4)
                outfile.write(jsonpickle.encode(area, unpicklable=True))

            start = time.perf_counter()

            the_count = 0
            for sol in area.solutions(transcript=this_transcript):
                the_count += 1
                # print(sol)
                # print(yaml.dump(sol.to_dict(), indent=4))
                # print()

            # the_count = count(area.solutions(transcript=transcript), print_every=1_000)

            print(f"{the_count} possible solutions")
            end = time.perf_counter()
            print(f"time: {end - start}")
            print()

if __name__ == "__main__":

    main()
