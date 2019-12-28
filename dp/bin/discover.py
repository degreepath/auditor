from typing import Iterator, Set, Any
from pathlib import Path
from collections import namedtuple
import argparse
import sys
import os

import yaml

try:
    import dotenv
    dotenv.load_dotenv(verbose=True)
except ImportError:
    pass

try:
    import psycopg2  # type: ignore
except ImportError:
    psycopg2 = None

from dp import AreaOfStudy, Constants
from dp.base import Rule
from dp.clause import AndClause, OrClause, Clause
from dp.rule.assertion import AssertionRule, ConditionalAssertionRule
from dp.rule.course import CourseRule
from dp.rule.count import CountRule
from dp.rule.proficiency import ProficiencyRule
from dp.rule.query import QueryRule
from dp.rule.requirement import RequirementRule

CourseReference = namedtuple('CourseReference', ['code', 'course'])
BucketReference = namedtuple('BucketReference', ['code', 'catalog', 'bucket'])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--insert', default=False, action='store_true')
    args = parser.parse_args()

    courses: Set[CourseReference] = set()
    buckets: Set[BucketReference] = set()

    for file in args.files:
        if not file.endswith('.yaml'):
            continue

        code = Path(file).stem
        catalog = file.parent.stem

        if '-' in code or '.' in code:
            continue

        with open(file, "r", encoding="utf-8") as infile:
            area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)

        area = AreaOfStudy.load(specification=area_spec, c=Constants(), all_emphases=True)

        for course in find_courses_in_rule(area.result):
            courses.add(CourseReference(code=code, course=course))

        for limit in area.limit.limits:
            for bucket in find_buckets_in_clause(limit.where):
                buckets.add(BucketReference(code=code, catalog=catalog, bucket=bucket))

        for bucket in find_buckets_in_rule(area.result):
            buckets.add(BucketReference(code=code, catalog=catalog, bucket=bucket))

    if args.insert:
        insert_to_db(courses=courses, buckets=buckets)
        print('inserted')
    else:
        for course_ref in sorted(courses):
            print(f"course: {course_ref.code}:{course_ref.course}")

        for bucket_ref in sorted(buckets):
            print(f"{bucket_ref.code}:{bucket_ref.catalog}:{bucket_ref.bucket}")


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


def insert_to_db(*, courses: Set[CourseReference], buckets: Set[BucketReference]) -> None:
    if not psycopg2:
        print('could not import module psycopg2', file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
    )

    insert_course_refs(conn, courses)
    insert_bucket_refs(conn, buckets)


def insert_course_refs(conn: Any, courses: Set[CourseReference]) -> None:
    with conn.cursor() as curs:
        for course_ref in courses:
            curs.execute('''
                INSERT INTO map_constant_area(area_code, course)
                VALUES (%(code)s, %(course)s)
                ON CONFLICT DO NOTHING
            ''', course_ref)

        curs.execute('''
            SELECT area_code, course
            FROM map_constant_area
        ''')

        for code, course in curs.fetchall():
            ref = CourseReference(code=code, course=course)
            if ref not in courses:
                print('deleting', ref)
                curs.execute('''
                    DELETE FROM map_constant_area
                    WHERE area_code = %(code)s
                        AND course = %(course)s
                ''', ref)

        conn.commit()


def insert_bucket_refs(conn: Any, buckets: Set[BucketReference]) -> None:
    with conn.cursor() as curs:
        for bucket_ref in buckets:
            curs.execute('''
                INSERT INTO map_attribute_area(attr, area_code, catalog_year)
                VALUES (%(bucket)s, %(code)s, %(catalog)s)
                ON CONFLICT DO NOTHING
            ''', bucket_ref)

        curs.execute('''
            SELECT area_code, catalog_year, attr
            FROM map_attribute_area
        ''')

        for code, catalog, bucket in curs.fetchall():
            ref = BucketReference(code=code, catalog=catalog, bucket=bucket)
            if ref not in buckets:
                print('deleting', ref)
                curs.execute('''
                    DELETE FROM map_attribute_area
                    WHERE area_code = %(code)s
                        AND catalog_year = %(catalog)s
                        AND attr = %(bucket)s
                ''', ref)

        conn.commit()


def find_buckets_in_rule(rule: Rule) -> Iterator[str]:
    if isinstance(rule, QueryRule):
        for limit in rule.limit.limits:
            yield from find_buckets_in_clause(limit.where)

        if rule.where:
            yield from find_buckets_in_clause(rule.where)

        for assertion in rule.assertions:
            yield from find_buckets_in_rule(assertion)

    elif isinstance(rule, AssertionRule):
        if rule.where:
            yield from find_buckets_in_clause(rule.where)

    elif isinstance(rule, ConditionalAssertionRule):
        yield from find_buckets_in_rule(rule.when_yes)
        if rule.when_no:
            yield from find_buckets_in_rule(rule.when_no)

    elif isinstance(rule, CountRule):
        for sub_rule in rule.items:
            yield from find_buckets_in_rule(sub_rule)

    elif isinstance(rule, RequirementRule):
        if not rule.result:
            return

        yield from find_buckets_in_rule(rule.result)


def find_buckets_in_clause(clause: Clause) -> Iterator[str]:
    if isinstance(clause, (AndClause, OrClause)):
        for sub_clause in clause.children:
            yield from find_buckets_in_clause(sub_clause)

    else:
        if clause.key == 'attributes':
            if type(clause.expected) is str:
                yield clause.expected
            elif type(clause.expected) is tuple:
                yield from clause.expected


if __name__ == '__main__':
    main()
