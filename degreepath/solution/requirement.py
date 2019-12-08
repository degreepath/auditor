import attr
from typing import Optional, Union, TYPE_CHECKING

from ..base import BaseRequirementRule, Solution, RuleState, Rule
from ..result.requirement import RequirementResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext


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
            audited_by=rule.audited_by,
            is_contract=rule.is_contract,
            path=rule.path,
            overridden=overridden,
            in_gpa=rule.in_gpa,
            is_independent=rule.is_independent,
        )

    def state(self) -> RuleState:
        if self.audited_by or self.result is None:
            return RuleState.Solution

        return self.result.state()

    def ok(self) -> bool:
        if self.result is None:
            return False

        return self.result.ok()

    def audit(self, *, ctx: 'RequirementContext') -> RequirementResult:
        if self.overridden:
            return RequirementResult.from_solution(
                solution=self,
                result=self.result,
                overridden=self.overridden,
            )

        if self.result is None:
            return RequirementResult.from_solution(solution=self, result=None)

        if isinstance(self.result, Rule):
            return RequirementResult.from_solution(solution=self, result=self.result)

        return RequirementResult.from_solution(solution=self, result=self.result.audit(ctx=ctx))
