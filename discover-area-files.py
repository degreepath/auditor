import argparse
import glob
import json
import os
from os.path import abspath, join

import dotenv

dotenv.load_dotenv(verbose=True)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('student')
    parser.add_argument('area_codes', metavar='CODE', action='store', nargs='*', default=tuple())
    args = parser.parse_args()

    for (name, path) in main(files=args.student, area_codes=args.area_codes):
        print(name, path)


def main(files, area_codes=tuple(), root=os.getenv('AREA_ROOT')):
    for student_file in glob.iglob(files):
        with open(student_file, 'r', encoding='utf-8') as infile:
            student = json.load(infile)

        areas = student['areas']
        catalog = student['catalog']
        if catalog is None:
            continue
        catalog = str(catalog) + '-' + str(catalog + 1)[2:]

        items = set(a['code'] for a in areas).union(area_codes)
        items = items.intersection(area_codes or items)

        for filename in items:
            file_path = join(root, catalog, filename + '.yaml')
            yield (abspath(student_file), abspath(file_path))


if __name__ == '__main__':
    cli()
