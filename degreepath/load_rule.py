from typing import Union, Dict, Mapping
from .constants import Constants

from .rule.count import CountRule
from .rule.course import CourseRule
from .rule.query import QueryRule
from .rule.requirement import Requirement
from .rule.reference import ReferenceRule

Rule = Union[CourseRule, CountRule, QueryRule, Requirement]


def load_rule(data: Dict, c: Constants, children: Mapping) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data, c, children)

    elif QueryRule.can_load(data):
        return QueryRule.load(data, c, children)

    elif CountRule.can_load(data):
        return CountRule.load(data, c, children)

    elif ReferenceRule.can_load(data):
        return ReferenceRule.load(data, c, children)

    raise ValueError(f"expected Course, Query, Count, Both, Either, or Reference; found none of those (in {data}, {type(data)})")
