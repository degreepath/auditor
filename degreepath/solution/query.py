import attr
from typing import List, Sequence, Any, Tuple, Dict, Union, Optional, Callable, Iterator, cast, TYPE_CHECKING
import logging

from ..base import Solution, BaseQueryRule
from ..base.query import QuerySource
from ..result.query import QueryResult
from ..rule.assertion import AssertionRule, ConditionalAssertionRule
from ..result.assertion import AssertionResult
from ..data import CourseInstance, Clausable

if TYPE_CHECKING:  # pragma: no cover
    from ..claim import ClaimAttempt  # noqa: F401
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AuditResult:
    claimed_items: Tuple[Clausable, ...] = tuple()
    successful_claims: Tuple['ClaimAttempt', ...] = tuple()
    failed_claims: Tuple['ClaimAttempt', ...] = tuple()
    inserted_clbids: Tuple[str, ...] = tuple()


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

    @classmethod
    def is_debug(cls) -> bool:
        return __debug__ and logger.isEnabledFor(logging.DEBUG)

    def audit(self, *, ctx: 'RequirementContext') -> QueryResult:
        debug = self.is_debug()

        if self.overridden:
            return QueryResult.from_solution(
                solution=self,
                resolved_assertions=tuple(),
                successful_claims=tuple(),
                failed_claims=tuple(),
                success=self.overridden,
                overridden=self.overridden,
            )

        audit_mode: Dict[QuerySource, Callable[['RequirementContext'], AuditResult]] = {
            QuerySource.Courses: self.audit_courses,
            QuerySource.Areas: self.audit_areas,
            QuerySource.MusicPerformances: self.audit_music_performances,
            QuerySource.MusicAttendances: self.audit_music_attendances,
        }

        audit_result = audit_mode[self.source](ctx)

        resolved_assertions = tuple(self.apply_assertions(ctx=ctx, input=audit_result.claimed_items))
        resolved_result = all(a.ok() for a in resolved_assertions)

        if debug:
            if resolved_result:
                logger.debug("%s might possibly succeed", self.path)
            else:
                logger.debug("%s did not succeed", self.path)

        return QueryResult.from_solution(
            solution=self,
            resolved_assertions=resolved_assertions,
            successful_claims=audit_result.successful_claims,
            failed_claims=audit_result.failed_claims,
            success=resolved_result,
            inserted=audit_result.inserted_clbids,
        )

    def audit_courses(self, ctx: 'RequirementContext') -> AuditResult:
        debug = self.is_debug()

        claimed_items: List[Clausable] = []
        successful_claims: List['ClaimAttempt'] = []
        failed_claims: List['ClaimAttempt'] = []

        output: Sequence[Clausable] = self.output
        if self.attempt_claims:
            for course in cast(Sequence[CourseInstance], output):
                claim = ctx.make_claim(course=course, path=self.path, allow_claimed=self.allow_claimed)

                if claim.failed:
                    if debug: logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, course.clbid, claim.conflict_with)
                    failed_claims.append(claim)
                else:
                    if debug: logger.debug('%s course "%s" exists, and is available', self.path, course.clbid)
                    successful_claims.append(claim)
                    claimed_items.append(course)
        else:
            if debug: logger.debug('%s courses "%s" exist, and is available', self.path, output)
            claimed_items = list(output)

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

        return AuditResult(
            claimed_items=tuple(claimed_items),
            successful_claims=tuple(successful_claims),
            failed_claims=tuple(failed_claims),
            inserted_clbids=tuple(inserted_clbids),
        )

    def audit_areas(self, ctx: 'RequirementContext') -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def audit_music_performances(self, ctx: 'RequirementContext') -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def audit_music_attendances(self, ctx: 'RequirementContext') -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def apply_assertions(self, *, ctx: 'RequirementContext', input: Sequence[Clausable]) -> Iterator[AssertionResult]:
        for a in self.assertions:
            assertion_result = self.apply_assertion(a, ctx=ctx, input=input)
            if assertion_result:
                yield assertion_result

    def apply_assertion(self, asrt: Union[AssertionRule, ConditionalAssertionRule], *, ctx: 'RequirementContext', input: Sequence[Clausable] = tuple()) -> Optional[AssertionResult]:
        clause = resolve_assertion(asrt, input=input)
        if clause is None:
            return None

        assert isinstance(clause, AssertionRule), TypeError(f"expected a query assertion; found {clause} ({type(clause)})")

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
            _clause = clause.override_expected_value(override_value.value)
            clause = cast(AssertionRule, _clause)

        if clause.where:
            filtered_output = [item for item in input if clause.where.apply(item)]
        else:
            filtered_output = list(input)

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


def resolve_assertion(asrt: Union[AssertionRule, ConditionalAssertionRule], *, input: Sequence[Clausable]) -> Optional[AssertionRule]:
    if isinstance(asrt, ConditionalAssertionRule):
        return asrt.resolve(input)
    else:
        return asrt
