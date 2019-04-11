from typing import Union, Dict

from .count import CountRule
from .course import CourseRule


Rule = Union[CourseRule, CountRule]


def load_rule(data: Dict) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data)
    elif CountRule.can_load(data):
        return CountRule.load(data)

    raise ValueError(
        f"expected Course, Given, Count, Both, Either, or Do; found none of those ({data})"
    )
