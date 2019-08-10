from dataclasses import dataclass
from typing import Optional
import logging

from ..base import Result, BaseRequirementRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequirementResult(Result, BaseRequirementRule):
    @staticmethod
    def from_solution(*, solution: BaseRequirementRule, result: Optional[Result]):
        return RequirementResult(
            name=solution.name,
            message=solution.message,
            audited_by=solution.audited_by,
            is_contract=solution.is_contract,
            result=result,
        )

    def status(self):
        return "pass" if self.ok() else "problem"

    def state(self):
        if self.audited_by or self.result is None:
            return "result"
        return self.result.state()

    def claims(self):
        if self.audited_by or self.result is None:
            return []
        return self.result.claims()

    def ok(self) -> bool:
        # return True if self.audited_by is not None else _ok
        return self.result.ok() if self.result else False

    def rank(self):
        boost = 1 if self.ok() else 0
        return self.result.rank() + boost if self.result else 0

    def max_rank(self):
        return self.result.max_rank() + 1 if self.result else 0
