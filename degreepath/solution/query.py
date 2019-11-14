import attr
from typing import List, Sequence, Any, Tuple, Dict, TYPE_CHECKING
import logging

from ..base import Solution, BaseQueryRule
from ..result.query import QueryResult
from ..rule.assertion import AssertionRule
from ..result.assertion import AssertionResult
from ..data import CourseInstance, AreaPointer, Clausable

if TYPE_CHECKING:  # pragma: no cover
    from ..claim import ClaimAttempt  # noqa: F401
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QuerySolution(Solution, BaseQueryRule):
    output: Tuple[Clausable, ...]
    overridden: bool

    @staticmethod
    def from_rule(*, rule: BaseQueryRule, output: Tuple[Clausable, ...], overridden: bool = False) -> 'QuerySolution':
        return QuerySolution(
            source=rule.source,
            assertions=rule.assertions,
            limit=rule.limit,
            where=rule.where,
            allow_claimed=rule.allow_claimed,
            attempt_claims=rule.attempt_claims,
            output=output,
            path=rule.path,
            overridden=overridden,
            inserted=rule.inserted,
            load_potentials=rule.load_potentials,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "output": [x.to_dict() for x in self.output],
        }

    def audit(self, *, ctx: 'RequirementContext') -> QueryResult:  # noqa: C901
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        if self.overridden:
            return QueryResult.from_solution(
                solution=self,
                resolved_assertions=tuple(),
                successful_claims=tuple(),
                failed_claims=tuple(),
                success=self.overridden,
                overridden=self.overridden,
            )

        claimed_items: List[Clausable] = []
        successful_claims: List['ClaimAttempt'] = []
        failed_claims: List['ClaimAttempt'] = []

        for item in self.output:
            if isinstance(item, CourseInstance):
                if self.attempt_claims:
                    claim = ctx.make_claim(course=item, path=self.path, allow_claimed=self.allow_claimed)

                    if claim.failed:
                        if debug: logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, item.clbid, claim.conflict_with)
                        failed_claims.append(claim)
                    else:
                        if debug: logger.debug('%s course "%s" exists, and is available', self.path, item.clbid)
                        successful_claims.append(claim)
                        claimed_items.append(item)
                else:
                    if debug: logger.debug('%s course "%s" exists, and is available', self.path, item.clbid)
                    claimed_items.append(item)

            elif isinstance(item, AreaPointer):
                if debug: logger.debug('%s item "%s" exists, and is available', self.path, item)
                claimed_items.append(item)

            else:
                raise TypeError(f'expected CourseInstance or AreaPointer; got {type(item)}')

        inserted_clbids = []
        for insert in ctx.get_insert_exceptions(self.path):
            matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)
            claim = ctx.make_claim(course=matched_course, path=self.path, allow_claimed=insert.forced)

            if claim.failed:
                if debug: logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, insert.clbid, claim.conflict_with)
                failed_claims.append(claim)
            else:
                if debug: logger.debug('%s course "%s" exists, and is available', self.path, insert.clbid)
                successful_claims.append(claim)
                claimed_items.append(matched_course)
                inserted_clbids.append(matched_course.clbid)

        resolved_assertions = tuple(
            self.apply_assertion(a, ctx=ctx, output=claimed_items)
            for a in self.assertions
        )

        resolved_result = all(a.ok() for a in resolved_assertions)

        if debug:
            if resolved_result:
                logger.debug("%s might possibly succeed", self.path)
            else:
                logger.debug("%s did not succeed", self.path)

        return QueryResult.from_solution(
            solution=self,
            resolved_assertions=resolved_assertions,
            successful_claims=tuple(successful_claims),
            failed_claims=tuple(failed_claims),
            success=resolved_result,
            inserted=tuple(inserted_clbids),
        )

    def apply_assertion(self, clause: AssertionRule, *, ctx: 'RequirementContext', output: Sequence[Clausable] = tuple()) -> AssertionResult:
        if not isinstance(clause, AssertionRule):
            raise TypeError(f"expected a query assertion; found {clause} ({type(clause)})")

        waive = ctx.get_waive_exception(clause.path)
        if waive:
            logger.debug("forced override on %s", self.path)
            return AssertionResult(
                where=clause.where,
                assertion=clause.assertion,
                path=clause.path,
                message=clause.message,
                overridden=True,
                inserted=tuple(),
            )

        override_value = ctx.get_value_exception(clause.path)
        if override_value:
            logger.debug("override: new value on %s", self.path)
            clause = clause.override_expected_value(override_value.value)

        if clause.where is not None:
            filtered_output = [item for item in output if clause.where.apply(item)]
        else:
            filtered_output = list(output)

        inserted_clbids = []
        for insert in ctx.get_insert_exceptions(clause.path):
            logger.debug("inserted %s into %s", insert.clbid, self.path)
            matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)
            filtered_output.append(matched_course)
            inserted_clbids.append(matched_course.clbid)

        result = clause.assertion.compare_and_resolve_with(tuple(filtered_output))
        return AssertionResult(
            where=clause.where,
            assertion=result,
            path=clause.path,
            message=clause.message,
            overridden=False,
            inserted=tuple(inserted_clbids),
        )
