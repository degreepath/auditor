from dataclasses import dataclass
from typing import Optional, Union, TYPE_CHECKING

from ..base import BaseRequirementRule, Solution, Rule
from ..result.requirement import RequirementResult

if TYPE_CHECKING:
    from ..context import RequirementContext


@dataclass(frozen=True)
class RequirementSolution(Solution, BaseRequirementRule):
    result: Optional[Union[Rule, Solution]]
    overridden: bool = False

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
        )

    def state(self):
        if self.audited_by or self.result is None:
            return "solution"
        return self.result.state()

    def claims(self):
        if self.audited_by or self.result is None:
            return []
        return self.result.claims()

    def ok(self):
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
