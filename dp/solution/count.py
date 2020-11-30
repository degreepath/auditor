import attr
from typing import Tuple, Union, TYPE_CHECKING
import logging

from ..base.bases import Rule, Solution, Result
from ..base.count import BaseCountRule
from ..rule.assertion import AssertionRule
from ..result.assertion import AssertionResult
from ..result.count import CountResult
from ..clause import apply_clause

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..rule.count import CountRule
    from ..data.course import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountSolution(Solution, BaseCountRule):
    items: Tuple[Union[Rule, Solution, Result], ...]
    audit_clauses: Tuple[AssertionRule, ...]
    overridden: bool

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
        audit_results = tuple(self.audit_assertion(assertion, ctx=ctx, input_items=matched_items) for assertion in self.audit_clauses)

        return CountResult.from_solution(solution=self, items=results, audit_results=audit_results)

    def audit_assertion(self, assertion: AssertionRule, *, input_items: Tuple['CourseInstance', ...], ctx: 'RequirementContext') -> AssertionResult:
        exception = ctx.get_waive_exception(assertion.path)
        if exception:
            logger.debug("forced override on %s", self.path)
            return assertion.override()

        if assertion.where:
            matched_items = [item for item in input_items if apply_clause(assertion.where, item)]
        else:
            matched_items = list(input_items)

        inserted_clbids = []
        for insert in ctx.get_insert_exceptions(assertion.path):
            logger.debug("inserted %s into %s", insert.clbid, self.path)
            matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)
            matched_items.append(matched_course)
            inserted_clbids.append(matched_course.clbid)

        return assertion.resolve(tuple(matched_items), overridden=False, inserted=tuple(inserted_clbids))
