from __future__ import annotations
from enum import Enum
from typing import Dict, Union
from dataclasses import dataclass

# from .action import Rule as ActionRule
from .both import Rule as BothRule
from .count import Rule as CountRule
from .course import Rule as CourseRule
from .either import Rule as EitherRule
from .given import Rule as GivenRule
from .reference import Rule as ReferenceRule
from ..types import OptReqList


RuleTypeUnion = Union[
    CourseRule,
    CountRule,
    EitherRule,
    BothRule,
    GivenRule,
    # ActionRule
]


class RuleTypeEnum(Enum):
    Course = "course"
    Count = "count"
    Either = "either"
    Both = "both"
    Given = "given"
    Action = "action"
    Reference = "reference"


@dataclass(frozen=True)
class Rule:
    variant: RuleTypeEnum
    rule: RuleTypeUnion

    @staticmethod
    def load(data: Union[Dict, str]) -> Rule:
        if isinstance(data, str):
            variant = RuleTypeEnum.Course
            rule = CourseRule(course=data)

        elif CourseRule.can_load(data):
            variant = RuleTypeEnum.Course
            rule = CourseRule.load(data)

        elif GivenRule.can_load(data):
            variant = RuleTypeEnum.Given
            rule = GivenRule.load(data)

        elif CountRule.can_load(data):
            variant = RuleTypeEnum.Count
            rule = CountRule.load(data)

        elif BothRule.can_load(data):
            variant = RuleTypeEnum.Both
            rule = BothRule.load(data)

        elif EitherRule.can_load(data):
            variant = RuleTypeEnum.Either
            rule = EitherRule.load(data)

        elif ReferenceRule.can_load(data):
            variant = RuleTypeEnum.Reference
            rule = ReferenceRule.load(data)

        # elif ActionRule.can_load(data):
        #     variant = RuleTypeEnum.Action
        #     rule = ActionRule.load(data)

        else:
            raise ValueError(
                "expected Course, Given, Count, Both, Either, or Do; found none of those"
            )

        return Rule(rule=rule, variant=variant)

    def validate(self, *, requirements: OptReqList = None, saves: OptSaveList = None):
        if requirements is None:
            requirements = []

        if saves is None:
            saves = []

        if self.variant == RuleTypeEnum.Course:
            self.rule.validate()
        # elif self.variant == RuleTypeEnum.Action:
        #     self.rule.validate(requirements=requirements, saves=saves)
        elif self.variant == RuleTypeEnum.Given:
            self.rule.validate(requirements=requirements, saves=saves)
        elif self.variant == RuleTypeEnum.Count:
            self.rule.validate(requirements=requirements, saves=saves)
        elif self.variant == RuleTypeEnum.Both:
            self.rule.validate(requirements=requirements, saves=saves)
        elif self.variant == RuleTypeEnum.Either:
            self.rule.validate(requirements=requirements, saves=saves)
        elif self.variant == RuleTypeEnum.Reference:
            self.rule.validate(requirements=requirements, saves=saves)
        else:
            raise ValueError(
                f"panic! unknown type of rule was constructed {self.variant}"
            )
