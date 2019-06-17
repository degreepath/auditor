from typing import Union, Dict

from .count import CountRule
from .course import CourseRule
from .action import ActionRule
from .given import FromRule
from .reference import ReferenceRule

Rule = Union[CourseRule, CountRule, ReferenceRule, FromRule]


def load_rule(data: Dict) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data)
    elif FromRule.can_load(data):
        return FromRule.load(data)
    elif CountRule.can_load(data):
        return CountRule.load(data)
    elif ReferenceRule.can_load(data):
        return ReferenceRule.load(data)
    # elif ActionRule.can_load(data):
    #     return ActionRule.load(data)

    raise ValueError(
        f"expected Course, Given, Count, Both, Either, or Do; found none of those ({data})"
    )
