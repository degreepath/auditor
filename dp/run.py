from typing import Iterator, Dict, Union, cast
import pathlib
import json
import csv
import sys

import yaml

from .area import AreaOfStudy
from .exception import load_exception, CourseOverrideException, load_migrations
from .lib import grade_point_average_items, grade_point_average
from .data.student import Student
from .audit import audit, Message, Arguments


def run(args: Arguments, *, student: Dict, area_spec: Dict) -> Iterator[Message]:
    area_code = area_spec['code']

    credit_assignments = area_spec.get('credit', {})

    exceptions_migrations = load_migrations(area_spec.get('exceptions-migrations', []))

    exceptions = [
        load_exception(e, exceptions_migrations)
        for e in student.get("exceptions", [])
        if e['area_code'] == area_code
    ]
    course_overrides = [e for e in exceptions if isinstance(e, CourseOverrideException)]

    loaded = Student.load(student, code=area_code, overrides=course_overrides, credits_overrides=credit_assignments)

    if args.transcript_only:
        writer = csv.writer(sys.stdout)
        writer.writerow(['course', 'name', 'clbid', 'type', 'credits', 'term', 'type', 'grade', 'in_gpa'])
        for c in loaded.courses:
            writer.writerow([
                c.course(), c.name, c.clbid, c.course_type.value, str(c.credits), f"{c.year}-{c.term}",
                c.sub_type.name, c.grade_code.value, 'Y' if c.is_in_gpa else 'N',
            ])
        return

    if args.gpa_only:
        gpa_only(loaded)
        return

    area = AreaOfStudy.load(
        specification=area_spec,
        c=loaded.constants(),
        student=loaded,
        exceptions=exceptions,
    )
    area.validate()

    yield from audit(
        area=area,
        student=loaded,
        exceptions=exceptions,
        args=args,
    )


def load_student(filename: str) -> Dict:
    with open(filename, "r", encoding="utf-8") as infile:
        return cast(Dict, json.load(infile))


def load_area(filename: Union[str, pathlib.Path]) -> Dict:
    try:
        with open(filename, "r", encoding="utf-8") as infile:
            return cast(Dict, yaml.load(stream=infile, Loader=yaml.SafeLoader))

    except FileNotFoundError:
        filepath = pathlib.Path(filename)

        return {
            'name': filepath.stem,
            'type': 'error',
            'code': filepath.stem,

            'result': {
                'all': [{
                    'name': 'Error',
                    'message': f'The {filepath.stem!r} area specification for this catalog year has not yet been transcribed.',
                    'department_audited': True,
                }],
            },
        }


def gpa_only(student: Student) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(['course', 'term', 'grade', 'points'])

    courses = student.courses_with_failed

    terms = sorted({c.year_term() for c in courses})

    cumulative = set()

    for term in terms:
        term_courses = {c for c in courses if c.year_term() == term}
        applicable = set(grade_point_average_items(term_courses))

        if not applicable:
            writer.writerow([term, ' ', '0 courses', ' '])
            continue
        else:
            # writer.writerow([term, ' ', f"{len(applicable)} courses", ' '])
            writer.writerow([term, ' ', ' ', ' '])

        ordered = sorted(applicable, key=lambda c: (c.year, c.term, c.course(), c.clbid))
        for c in ordered:
            writer.writerow([c.course(), c.year_term(), c.grade_code.value, str(c.grade_points)])

        writer.writerow([' ', ' ', 'gpa:', str(grade_point_average(term_courses))])

        for c in applicable:
            cumulative.add(c)

        writer.writerow([' ', ' ', 'cum. gpa:', str(grade_point_average(cumulative))])

    writer.writerow(['overall', '---', 'gpa:', str(grade_point_average(courses))])
