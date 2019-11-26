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
    parser.add_argument('area_codes', metavar='CODE', action='store', nargs='*', default=list())
    args = parser.parse_args()

    if args.student == '-':
        student_files = [l.strip() for l in sys.stdin.readlines() if l.strip()]
        area_codes = args.area_codes
    else:
        all_files = [args.student] + args.area_codes
        student_files = [f for f in all_files if f.endswith('.json')]
        area_codes = [f for f in all_files if not f.endswith('.json')]

    for file in student_files:
        for (name, path) in main(files=file, area_codes=area_codes):
            print(name, path)


def main(
    files: str,
    area_codes: Sequence[str] = tuple(),
    catalog: Optional[Union[str, int]] = None,
    root: Optional[str] = os.getenv('AREA_ROOT'),
) -> Iterator[Tuple[str, str]]:
    if not root:
        raise ValueError('the environment variable AREA_ROOT must be set to a path')

    for student_file in glob.iglob(files):
        yield from run_student(student_file=student_file, area_codes=area_codes, catalog=catalog, root=root)


def run_student(
    *,
    student_file: str,
    area_codes: Sequence[str] = tuple(),
    catalog: Optional[Union[str, int]] = None,
    root: str,
) -> Iterator[Tuple[str, str]]:
    with open(student_file, 'r', encoding='utf-8') as infile:
        student = json.load(infile)

    areas = [a for a in student['areas'] if a['kind'] != 'emphasis']
    area_dict = {a['code']: a for a in student['areas']}

    if catalog is not None:
        catalog = catalog
    elif student['catalog'] == '' or student['catalog'] == 'None':
        catalog = None
    else:
        catalog = int(student['catalog'])

    if catalog is None:
        return

    items = set(a['code'] for a in areas).union(area_codes)
    items = items.intersection(area_codes or items)

    for area_code in items:
        area_pointer = area_dict.get(area_code, {'code': area_code, 'catalog': catalog})
        area_catalog = area_pointer.get('catalog', catalog)
        if '-' not in str(area_catalog):
            area_catalog = fmt_catalog(area_pointer.get('catalog', catalog))

        file_path = join(root, area_catalog, area_code + '.yaml')
        yield (abspath(student_file), abspath(file_path))


def fmt_catalog(catalog: int) -> str:
    return str(catalog) + '-' + str(catalog + 1)[2:]


if __name__ == '__main__':
    cli()
