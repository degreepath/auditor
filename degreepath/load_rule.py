from typing import Dict, Sequence
from .constants import Constants

from .base import Rule
from .rule.count import CountRule
from .rule.course import CourseRule
from .rule.query import QueryRule
from .rule.requirement import RequirementRule


def load_rule(data: Dict, c: Constants, children: Dict, emphases: Sequence[Dict] = tuple()) -> Rule:
    if emphases:
        assert CountRule.can_load(data)
        return CountRule.load(data, c, children, emphases)

    if CourseRule.can_load(data):
        return CourseRule.load(data, c, children)

    elif QueryRule.can_load(data):
        return QueryRule.load(data, c, children)

    elif CountRule.can_load(data):
        return CountRule.load(data, c, children)

    elif "requirement" in data:
        return RequirementRule.load(name=data["requirement"], data=children[data["requirement"]], c=c)

    raise ValueError(f"expected Course, Query, Count, or Reference; found none of those (in {data}, {type(data)})")
