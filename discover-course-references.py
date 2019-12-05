#!/usr/bin/env python3

from typing import Iterator
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

        for c in find_courses_in_rule(area.result):
            pairs.add(f"{code}:{c}")

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


if __name__ == '__main__':
    main()
