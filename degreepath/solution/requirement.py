from dataclasses import dataclass
from typing import List, Optional

from ..base import BaseRequirementRule, Solution
from ..result.requirement import RequirementResult


@dataclass(frozen=True)
class RequirementSolution(Solution, BaseRequirementRule):
    result: Optional[Solution]

    @staticmethod
    def from_rule(*, rule: BaseRequirementRule, solution: Optional[Solution]):
        return RequirementSolution(
            result=solution,
            name=rule.name,
            message=rule.message,
            audited_by=rule.audited_by,
            is_contract=rule.is_contract,
            path=rule.path,
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

    def audit(self, *, ctx):
        if self.result is None:
            return RequirementResult.from_solution(solution=self, result=None)

        return RequirementResult.from_solution(solution=self, result=self.result.audit(ctx=ctx))
