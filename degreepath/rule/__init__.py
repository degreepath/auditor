from typing import Union, Dict
from ..constants import Constants

from .count import CountRule
from .course import CourseRule
from .action import ActionRule
from .given import FromRule, str_assertion
from .reference import ReferenceRule
from .audited import AuditedRule

Rule = Union[CourseRule, CountRule, ReferenceRule, FromRule, AuditedRule]


def load_rule(data: Dict, c: Constants) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data, c)
    elif FromRule.can_load(data):
        return FromRule.load(data, c)
    elif CountRule.can_load(data):
        return CountRule.load(data, c)
    elif ReferenceRule.can_load(data):
        return ReferenceRule.load(data, c)
    # elif ActionRule.can_load(data):
    #     return ActionRule.load(data)
    elif AuditedRule.can_load(data):
        return AuditedRule.load(data, c)

    raise ValueError(f"expected Course, Given, Count, Both, Either, or Audited; found none of those ({data})")
