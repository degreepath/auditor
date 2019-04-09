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
logger.setLevel(logging.DEBUG)
logformat = "%(levelname)s %(message)s"
coloredlogs.install(level="DEBUG", logger=logger, fmt=logformat)


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
@click.argument('student_file', type=click.Path(exists=True))
def main(student_file):
    """Audits a student against their areas of study."""

    with open(student_file, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    print(data)
    transcript = [CourseInstance.from_dict(**row) for row in data["courses"]]
    for c in transcript:
        pprint.pprint(c)
    return

    # for file in glob.iglob("./gobbldygook-area-data/2018-19/*/*.yaml"):
    for file in [
        # "./gobbldygook-area-data/2018-19/major/computer-science.yaml",
        # "./gobbldygook-area-data/2018-19/major/asian-studies.yaml",
        # "./gobbldygook-area-data/2018-19/major/womens-and-gender-studies.yaml"
        # "./sample-simple-area.yaml"
    ]:
        print(f"processing {file}")
        with open(file, "r", encoding="utf-8") as infile:
            area = load_area(infile)

        area.validate()

        this_transcript = [
            c.update(attributes=area.attributes["courses"].get(c.course(), []))
            for c in transcript
        ]


        outname = f'./tmp/{area.kind}/{area.name.replace("/", "_")}.json'
        with open(outname, "w", encoding="utf-8") as outfile:
            jsonpickle.set_encoder_options("json", sort_keys=True, indent=4)
            outfile.write(jsonpickle.encode(area, unpicklable=True))

        start = time.perf_counter()

        the_count = 0
        for sol in area.solutions(transcript=this_transcript):
            the_count += 1
            print(sol)
            print(yaml.dump(sol.to_dict(), indent=4))
            print()

        # the_count = count(area.solutions(transcript=transcript), print_every=1_000)

        print(f"{the_count} possible solutions")
        end = time.perf_counter()
        print(f"time: {end - start}")
        print()

if __name__ == "__main__":

    main()
