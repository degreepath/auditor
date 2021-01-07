import attr
from typing import Tuple, Union, TYPE_CHECKING
import logging

from ..base.bases import Rule, Solution, Result
from ..base.count import BaseCountRule
from ..result.count import CountResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..rule.count import CountRule

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountSolution(Solution, BaseCountRule):
    # reason: type narrowing
    items: Tuple[Union[Rule, Solution, Result], ...]

    @staticmethod
    def from_rule(*, rule: 'CountRule', count: int, items: Tuple[Union[Rule, Solution, Result], ...], overridden: bool = False) -> 'CountSolution':
        return CountSolution(
            count=count,
            items=items,
            audit_clauses=rule.audit_clauses,
            at_most=rule.at_most,
            path=rule.path,
            overridden=overridden,
        )

    def audit(self, *, ctx: 'RequirementContext') -> CountResult:
        if self.overridden:
            return CountResult.from_solution(
                solution=self,
                items=self.items,
                audit_results=self.audit_clauses,
                overridden=self.overridden,
            )

        results = tuple(r.audit(ctx=ctx) if isinstance(r, Solution) else r for r in self.items)
        matched_items = tuple(item for sol in results for item in sol.matched())
        audit_results = tuple(a.audit_and_resolve(data=matched_items, ctx=ctx) for a in self.audit_clauses)

        return CountResult.from_solution(solution=self, items=results, audit_results=audit_results)
