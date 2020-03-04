import argparse
import glob
import json
import os
import sys
from typing import Dict, Iterator, Tuple, Optional
from os.path import abspath, join

from dp.dotenv import load as load_dotenv

load_dotenv()


def cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('student', help="use `-` to read from stdin")
    parser.add_argument('area_code', metavar='CODE', action='store', nargs='?', default=None)
    args = parser.parse_args()

    if args.student == '-':
        student_files = [line.strip() for line in sys.stdin.readlines() if line.strip()]
        area_code = args.area_code
    else:
        all_files = [args.student, *args.area_codes]
        student_files = [f for f in all_files if f.endswith('.json')]
        area_codes = [f for f in all_files if not f.endswith('.json')]
        area_code = area_codes[0]

    root = os.getenv('AREA_ROOT')
    assert root, ValueError('the environment variable AREA_ROOT must be set to a path')

    for file_glob in student_files:
        for student_file in glob.iglob(file_glob):
            with open(student_file, 'r', encoding='utf-8') as infile:
                student = json.load(infile)

            for stnum, catalog, code in expand_student(student=student, area_code=area_code):
                file_path = join(root, catalog, code + '.yaml')
                print(abspath(student_file), abspath(file_path))


def expand_student(*, student: Dict, area_code: Optional[str] = None, catalog: Optional[str] = None) -> Iterator[Tuple[str, str, str]]:
    stnum = student['stnum']

    areas = [a for a in student['areas'] if a['kind'] != 'emphasis']
    area_dict = {a['code']: a for a in student['areas']}

    if catalog is None:
        try:
            catalog = str(int(student['catalog']))
        except ValueError:
            # If the catalog isn't a year, just go ahead and skip this audit
            return

    if area_code:
        items = {area_code}
    else:
        items = set(a['code'] for a in areas)

    for area_code in items:
        area_pointer = area_dict.get(area_code, {'code': area_code, 'catalog': catalog})

        # fetch the more-specific catalog field from the area reference, if given
        area_catalog = area_pointer.get('catalog', catalog)

        # convert the year catalog "2019" into "2019-20"
        area_catalog = area_catalog + '-' + str(int(area_catalog) + 1)[2:]

        yield (stnum, area_catalog, area_code)


if __name__ == '__main__':
    cli()
