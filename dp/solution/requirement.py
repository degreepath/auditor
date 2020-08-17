import attr
from typing import Optional, Union, TYPE_CHECKING
import logging

from ..base import BaseRequirementRule, Solution, RuleState, Rule
from ..result.requirement import RequirementResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


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

    def audit(self, *, ctx: 'RequirementContext') -> RequirementResult:
        logger.debug('auditing requirement %s', self.path)

        if self.overridden:
            return RequirementResult.from_solution(
                solution=self,
                result=self.result,
                overridden=self.overridden,
            )

        if self.result is None:
            return RequirementResult.from_solution(solution=self, result=None)

        if isinstance(self.result, Rule):
            # TODO: determine when this happens
            return RequirementResult.from_solution(solution=self, result=self.result)

        return RequirementResult.from_solution(solution=self, result=self.result.audit(ctx=ctx))
