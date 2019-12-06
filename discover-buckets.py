#!/usr/bin/env python3

from typing import Iterator, Iterable, Tuple
from pathlib import Path
import argparse

import yaml

from degreepath import AreaOfStudy, Constants
from degreepath.base import Rule
from degreepath.clause import AndClause, OrClause, Clause
from degreepath.rule.query import QueryRule
from degreepath.rule.assertion import AssertionRule, ConditionalAssertionRule
from degreepath.rule.count import CountRule
from degreepath.rule.requirement import RequirementRule


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--insert', default=False, action="store_true")
    args = parser.parse_args()

    tuples = set()

    for file in args.files:
        if not file.endswith('.yaml'):
            continue

        file = Path(file)

        code = file.stem
        catalog = file.parent.stem

        if '-' in code or '.' in code:
            continue

        with open(file, "r", encoding="utf-8") as infile:
            area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)

        area = AreaOfStudy.load(specification=area_spec, c=Constants(), all_emphases=True)

        for bucket in find_buckets_in_rule(area.result):
            tuples.add((code, catalog, bucket))

    if args.insert:
        insert_to_db(tuples)
        print('done')
    else:
        for code, catalog, bucket in sorted(tuples):
            print(f"{code}:{catalog}:{bucket}")


def find_buckets_in_rule(rule: Rule) -> Iterator[str]:
    if isinstance(rule, QueryRule):
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


def insert_to_db(tuples: Iterable[Tuple[str, str, str]]) -> None:
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
        for code, catalog, bucket in tuples:
            curs.execute('''
                INSERT INTO map_attribute_area(attr, area_code, catalog_year)
                VALUES (%(bucket)s, %(code)s, %(catalog)s)
                ON CONFLICT DO NOTHING
            ''', {'code': code, 'catalog': catalog, 'bucket': bucket})

        curs.execute('''
            SELECT area_code, catalog_year, attr
            FROM map_attribute_area
        ''')

        for code, catalog, bucket in curs.fetchall():
            if (code, catalog, bucket) not in known_tuples:
                print('deleting', (code, catalog, bucket))
                curs.execute('''
                    DELETE FROM map_attribute_area
                    WHERE area_code = %(code)s
                        AND catalog_year = %(catalog)s
                        AND attr = %(bucket)s
                ''', {'code': code, 'catalog': catalog, 'bucket': bucket})

        conn.commit()


if __name__ == '__main__':
    main()
