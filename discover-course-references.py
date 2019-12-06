#!/usr/bin/env python3

from typing import Iterator, Iterable, Tuple
from pathlib import Path
import argparse

import yaml

from degreepath import AreaOfStudy, Constants
from degreepath.base import Rule
from degreepath.rule.course import CourseRule
from degreepath.rule.count import CountRule
from degreepath.rule.proficiency import ProficiencyRule
from degreepath.rule.requirement import RequirementRule


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--insert', default=False, action='store_true')
    args = parser.parse_args()

    pairs = set()

    for file in args.files:
        if not file.endswith('.yaml'):
            continue

        code = Path(file).stem

        if '-' in code or '.' in code:
            continue

        with open(file, "r", encoding="utf-8") as infile:
            area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)

        area = AreaOfStudy.load(specification=area_spec, c=Constants(), all_emphases=True)

        for course in find_courses_in_rule(area.result):
            pairs.add((code, course))

    if args.insert:
        insert_to_db(pairs)
        print('done')
    else:
        for pair in sorted(pairs):
            print(pair)


def find_courses_in_rule(rule: Rule) -> Iterator[str]:
    if isinstance(rule, CourseRule):
        if not rule.course:
            return

        if rule.institution or rule.clbid or rule.ap or rule.name:
            return

        if rule.hidden:
            return

        yield rule.course

    elif isinstance(rule, ProficiencyRule):
        if not rule.course:
            return

        yield from find_courses_in_rule(rule.course)

    elif isinstance(rule, CountRule):
        for sub_rule in rule.items:
            yield from find_courses_in_rule(sub_rule)

    elif isinstance(rule, RequirementRule):
        if not rule.result:
            return

        yield from find_courses_in_rule(rule.result)


def insert_to_db(tuples: Iterable[Tuple[str, str]]) -> None:
    import dotenv
    import os
    import psycopg2  # type: ignore

    dotenv.load_dotenv(verbose=True)

    conn = psycopg2.connect(
        host=os.environ.get("PG_HOST"),
        database=os.environ.get("PG_DATABASE"),
        user=os.environ.get("PG_USER"),
    )

    known_tuples = set(tuples)

    with conn.cursor() as curs:
        for code, course in tuples:
            curs.execute('''
                INSERT INTO map_constant_area(area_code, course)
                VALUES (%(code)s, %(course)s)
                ON CONFLICT DO NOTHING
            ''', {'code': code, 'course': course})

        curs.execute('''
            SELECT area_code, course
            FROM map_constant_area
        ''')

        for code, course in curs.fetchall():
            if (code, course) not in known_tuples:
                print('deleting', (code, course))
                curs.execute('''
                    DELETE FROM map_constant_area
                    WHERE area_code = %(code)s
                        AND course = %(course)s
                ''', {'code': code, 'course': course})

        conn.commit()


if __name__ == '__main__':
    main()
