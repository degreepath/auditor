from dataclasses import dataclass
from typing import Optional
import logging

from ..base import Base, Result, BaseRequirementRule, ResultStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequirementResult(Result, BaseRequirementRule):
    overridden: bool = False

    @staticmethod
    def from_solution(
        *,
        solution: BaseRequirementRule,
        result: Optional[Base],
        overridden: bool = False,
    ) -> 'RequirementResult':
        return RequirementResult(
            name=solution.name,
            message=solution.message,
            audited_by=solution.audited_by,
            is_contract=solution.is_contract,
            path=solution.path,
            result=result,
            overridden=overridden,
        )

    def status(self) -> ResultStatus:
        return ResultStatus.Pass if self.ok() else ResultStatus.Problem

    def state(self):
        if self.result is None:
            return "result"

        return self.result.state()

    def claims(self):
        if self.result is None:
            return []

        return self.result.claims()

    def was_overridden(self):
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return self.overridden

        # return True if self.audited_by is not None else _ok
        return self.result.ok() if self.result else False

    def rank(self):
        boost = 1 if self.ok() else 0
        return self.result.rank() + boost if self.result else 0

    def max_rank(self):
        return self.result.max_rank() + 1 if self.result else 0
