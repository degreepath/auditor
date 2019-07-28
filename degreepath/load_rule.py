from typing import Union, Dict
from .constants import Constants

from .rule.count import CountRule
from .rule.course import CourseRule
from .rule.query import QueryRule
from .rule.reference import ReferenceRule

Rule = Union[CourseRule, CountRule, QueryRule, ReferenceRule]


def load_rule(data: Dict, c: Constants) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data, c)

    elif QueryRule.can_load(data):
        return QueryRule.load(data, c)

    elif CountRule.can_load(data):
        return CountRule.load(data, c)

    elif ReferenceRule.can_load(data):
        return ReferenceRule.load(data, c)

    raise ValueError(f"expected Course, Query, Count, Both, Either, or Reference; found none of those (in {data}, {type(data)})")
