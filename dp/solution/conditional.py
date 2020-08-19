import attr
from typing import Optional, Union, TYPE_CHECKING
import logging

from ..base import BaseConditionalRule, Solution, Rule
from ..result.conditional import ConditionalResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalSolution(Solution, BaseConditionalRule):
    when_true: Union[Rule, Solution]
    when_false: Optional[Union[Rule, Solution]]

    def audit(self, *, ctx: 'RequirementContext') -> ConditionalResult:
        logger.debug('auditing conditional rule %s', self.path)

        if self.condition.result is True and isinstance(self.when_true, Solution):
            return ConditionalResult.from_solution(source=self, when_true=self.when_true.audit(ctx=ctx))

        elif self.condition.result is False and self.when_false and isinstance(self.when_false, Solution):
            return ConditionalResult.from_solution(source=self, when_false=self.when_false.audit(ctx=ctx))

        else:
            return ConditionalResult.from_solution(source=self)
