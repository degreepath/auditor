from typing import Optional, Union

import attr

from ..base.bases import Solution, Rule, RuleState
from ..base.requirement import BaseRequirementRule
from ..context import RequirementContext
from ..result.requirement import RequirementResult


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RequirementSolution(Solution, BaseRequirementRule):
    result: Optional[Union[Rule, Solution]]
    overridden: bool

    @staticmethod
    def from_rule(*, rule: BaseRequirementRule, solution: Optional[Union[Rule, Solution]], overridden: bool = False) -> 'RequirementSolution':
        return RequirementSolution(
            result=solution,
            name=rule.name,
            message=rule.message,
            is_audited=rule.is_audited,
            is_contract=rule.is_contract,
            disjoint=rule.disjoint,
            path=rule.path,
            overridden=overridden,
            in_gpa=rule.in_gpa,
        )

    def state(self) -> RuleState:
        if self.is_audited or self.result is None:
            return RuleState.Solution

        return self.result.state()

    def audit(self, *, ctx: RequirementContext) -> RequirementResult:
        if self.overridden:
            return RequirementResult.from_solution(
                solution=self,
                result=self.result,
                overridden=self.overridden,
            )

        if self.result is None:
            return RequirementResult.from_solution(solution=self, result=None)

        if isinstance(self.result, Rule):
            # TODO determine when this happens
            return RequirementResult.from_solution(solution=self, result=self.result)

        return RequirementResult.from_solution(solution=self, result=self.result.audit(ctx=ctx))
