import attr
from typing import Tuple, Union, TYPE_CHECKING
import logging

from ..base import Solution, BaseCountRule, Rule, Result
from ..result.count import CountResult
from ..result.assertion import AssertionResult
from .query import apply_clause_to_query_rule

if TYPE_CHECKING:
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountSolution(Solution, BaseCountRule):
    overridden: bool

    @staticmethod
    def from_rule(*, rule: BaseCountRule, count: int, items: Tuple[Union[Rule, Solution, Result], ...], overridden: bool = False) -> 'CountSolution':
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
                items=tuple(self.items),
                audit_results=tuple(self.audit_clauses),
                overridden=self.overridden,
            )

        results = [r.audit(ctx=ctx) if isinstance(r, Solution) else r for r in self.items]

        audit_results = []
        for clause in self.audit_clauses:
            exception = ctx.get_waive_exception(clause.path)
            if exception:
                logger.debug("forced override on %s", self.path)
                audit_results.append(AssertionResult(
                    where=clause.where,
                    assertion=clause.assertion,
                    path=clause.path,
                    overridden=True,
                ))
                continue

            matched_items = [item for sol in results for item in sol.matched(ctx=ctx)]

            if clause.where is not None:
                matched_items = [
                    item for item in matched_items
                    if item.apply_clause(clause.where)
                ]

            for insert in ctx.get_insert_exceptions(clause.path):
                logger.debug("inserted %s into %s", insert.clbid, self.path)
                matched_course = ctx.forced_course_by_clbid(insert.clbid)
                matched_items.append(matched_course)

            result = clause.assertion.compare_and_resolve_with(
                value=matched_items,
                map_func=apply_clause_to_query_rule,
            )

            audit_results.append(AssertionResult(
                where=clause.where,
                assertion=result,
                path=clause.path,
                overridden=False,
            ))

        return CountResult.from_solution(
            solution=self,
            items=tuple(results),
            audit_results=tuple(audit_results),
        )
