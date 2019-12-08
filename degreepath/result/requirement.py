import attr
from typing import Optional
import logging

from ..base import Base, Result, BaseRequirementRule, RuleState

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RequirementResult(Result, BaseRequirementRule):
    overridden: bool

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
            in_gpa=solution.in_gpa,
            is_independent=solution.is_independent,
            result=result,
            overridden=overridden,
        )

    def state(self) -> RuleState:
        if self.result is None:
            return RuleState.Result

        return self.result.state()

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return self.overridden

        if self.result is None:
            return False

        return self.result.ok()
