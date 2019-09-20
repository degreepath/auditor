import argparse
import glob
import json
import os
import sys
from typing import Sequence, Iterator, Tuple, Optional, Union
from os.path import abspath, join

import dotenv

dotenv.load_dotenv(verbose=True)


def cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('student', help="use `-` to read from stdin")
    parser.add_argument('area_codes', metavar='CODE', action='store', nargs='*', default=tuple())
    args = parser.parse_args()

    if args.student == '-':
        student_files = [l.strip() for l in sys.stdin.readlines() if l.strip()]
    else:
        student_files = [args.student]

    for file in student_files:
        for (name, path) in main(files=file, area_codes=args.area_codes):
            print(name, path)


def main(
    files: str,
    area_codes: Sequence[str] = tuple(),
    catalog: Optional[int] = None,
    root: Optional[str] = os.getenv('AREA_ROOT'),
) -> Iterator[Tuple[str, str]]:
    if not root:
        raise ValueError('the environment variable AREA_ROOT must be set to a path')

    for student_file in glob.iglob(files):
        with open(student_file, 'r', encoding='utf-8') as infile:
            student = json.load(infile)

        areas = [a for a in student['areas'] if a['kind'] != 'emphasis']

        stu_catalog: Optional[Union[str, int]] = None
        if catalog is not None:
            stu_catalog = catalog
        elif student['catalog'] == '' or student['catalog'] == 'None':
            stu_catalog = None
        else:
            stu_catalog = int(student['catalog'])

        if stu_catalog is None:
            continue

        stu_catalog = str(stu_catalog) + '-' + str(stu_catalog + 1)[2:]

        items = set(a['code'] for a in areas).union(area_codes)
        items = items.intersection(area_codes or items)

        for filename in items:
            file_path = join(root, stu_catalog, filename + '.yaml')
            yield (abspath(student_file), abspath(file_path))


if __name__ == '__main__':
    cli()
