import attr
from typing import List, Sequence, Any, Tuple, Dict, Union, Optional, Iterator, cast, TYPE_CHECKING
import logging

from ..base import Solution, BaseQueryRule
from ..base.query import QuerySource
from ..result.query import QueryResult
from ..rule.assertion import AssertionRule
from ..rule.conditional_assertion import ConditionalAssertionRule
from ..result.assertion import AssertionResult
from ..data.clausable import Clausable
from ..clause import apply_clause
from ..claim import Claim

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data.course import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)
debug: Optional[bool] = None


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AuditResult:
    claimed_items: Tuple[Clausable, ...] = tuple()
    successful_claims: Tuple[Claim, ...] = tuple()
    failed_claims: Tuple[Claim, ...] = tuple()


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QuerySolution(Solution, BaseQueryRule):
    output: Tuple[Clausable, ...]
    overridden: bool

    @staticmethod
    def from_rule(
        *,
        rule: BaseQueryRule,
        output: Tuple[Clausable, ...],
        overridden: bool = False,
        inserted: Tuple[str, ...] = tuple(),
        force_inserted: Tuple[str, ...] = tuple(),
    ) -> 'QuerySolution':
        return QuerySolution(
            source=rule.source,
            assertions=rule.assertions,
            limit=rule.limit,
            where=rule.where,
            allow_claimed=rule.allow_claimed,
            attempt_claims=rule.attempt_claims,
            record_claims=rule.record_claims,
            output=output,
            path=rule.path,
            overridden=overridden,
            inserted=rule.inserted + inserted,
            force_inserted=rule.force_inserted + force_inserted,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "output": [x.to_dict() for x in self.output],
        }

    def audit(self, *, ctx: 'RequirementContext') -> QueryResult:
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)
        if debug: logger.debug("auditing data for %s", self.path)

        if self.overridden:
            return QueryResult.from_solution(
                solution=self,
                resolved_assertions=tuple(),
                successful_claims=tuple(),
                failed_claims=tuple(),
                overridden=self.overridden,
            )

        if self.source is QuerySource.Courses:
            audit_result = self.audit_courses(ctx)
        elif self.source is QuerySource.Claimed:
            audit_result = self.audit_claimed_courses(ctx)
        elif self.source is QuerySource.Areas:
            audit_result = self.audit_areas(ctx)
        elif self.source is QuerySource.MusicPerformances:
            audit_result = self.audit_music_performances(ctx)
        elif self.source is QuerySource.MusicAttendances:
            audit_result = self.audit_music_attendances(ctx)

        resolved_assertions = tuple(self.apply_assertions(audit_result.claimed_items, ctx=ctx))

        logger.debug("done auditing data for %s", self.path)

        return QueryResult.from_solution(
            solution=self,
            resolved_assertions=resolved_assertions,
            successful_claims=audit_result.successful_claims,
            failed_claims=audit_result.failed_claims,
        )

    def audit_courses(self, ctx: 'RequirementContext') -> AuditResult:
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        claimed_items: List[Clausable] = []
        successful_claims: List[Claim] = []
        failed_claims: List[Claim] = []

        if debug: logger.debug("auditing courses [at %s]", self.path)

        output: Sequence['CourseInstance'] = cast(Sequence['CourseInstance'], self.output)
        if self.attempt_claims:
            for course in output:
                was_forced = course.clbid in self.force_inserted
                claim = ctx.make_claim(course=course, path=self.path, allow_claimed=self.allow_claimed or was_forced)

                if claim.failed:
                    if debug: logger.debug('%r exists, but has already been claimed by other rules [at %s]', course, self.path)
                    failed_claims.append(claim)
                else:
                    if debug: logger.debug('%r exists, and is available [at %s]', course, self.path)
                    successful_claims.append(claim)
                    claimed_items.append(course)

        elif self.record_claims:
            for course in output:
                claim = ctx.make_claim(course=course, path=self.path, allow_claimed=True)
                assert claim.failed is False
                successful_claims.append(claim)
                claimed_items.append(course)

        else:
            if debug:
                for _c in output:
                    logger.debug('%r exists, and is available [at %s]', _c, self.path)
            claimed_items = list(output)

        if debug: logger.debug("done auditing courses for %s", self.path)

        return AuditResult(
            claimed_items=tuple(claimed_items),
            successful_claims=tuple(successful_claims),
            failed_claims=tuple(failed_claims),
        )

    def audit_claimed_courses(self, ctx: 'RequirementContext') -> AuditResult:
        claimed_items: List[Clausable] = []
        successful_claims: List[Claim] = []

        output: List['CourseInstance'] = ctx.all_claimed()
        if self.where:
            output = [item for item in output if apply_clause(self.where, item)]

        for clbid in self.inserted:
            matched_course = ctx.forced_course_by_clbid(clbid, path=self.path)
            output.append(matched_course)

        for course in output:
            claim = ctx.make_claim(course=course, path=self.path, allow_claimed=True)

            assert claim.failed is False

            if self.record_claims:
                successful_claims.append(claim)

            claimed_items.append(course)

        return AuditResult(
            claimed_items=tuple(claimed_items),
            successful_claims=tuple(successful_claims),
            failed_claims=tuple(),
        )

    def audit_areas(self, ctx: 'RequirementContext') -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def audit_music_performances(self, ctx: 'RequirementContext') -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def audit_music_attendances(self, ctx: 'RequirementContext') -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def apply_assertions(self, data: Sequence[Clausable], *, ctx: 'RequirementContext') -> Iterator[AssertionResult]:
        for a in self.assertions:
            assertion_result = self.apply_assertion(a, ctx=ctx, data=data)
            if assertion_result:
                yield assertion_result

    def apply_assertion(self, maybe_asrt: Union[AssertionRule, ConditionalAssertionRule], *, ctx: 'RequirementContext', data: Sequence[Clausable] = tuple()) -> Optional[AssertionResult]:
        global debug
        if debug is None:
            debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        assertion = maybe_asrt.resolve_conditional(data) if isinstance(maybe_asrt, ConditionalAssertionRule) else maybe_asrt
        if assertion is None:
            return None

        assert isinstance(assertion, AssertionRule), TypeError(f"expected a query assertion; found {assertion} ({type(assertion)})")

        waive = ctx.get_waive_exception(assertion.path)
        if waive:
            if debug: logger.debug("forced override on %s", self.path)
            return assertion.override()

        override_value = ctx.get_value_exception(assertion.path)
        if override_value:
            if debug: logger.debug("override: new value on %s", self.path)
            assertion = assertion.set_expected_value(override_value.value)

        if assertion.where:
            filtered_output = [item for item in data if apply_clause(assertion.where, item)]
        else:
            filtered_output = list(data)

        inserted_clbids = []
        for insert in ctx.get_insert_exceptions(assertion.path):
            if debug: logger.debug("inserted %s into %s", insert.clbid, self.path)
            matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)
            filtered_output.append(matched_course)
            inserted_clbids.append(matched_course.clbid)

        return assertion.resolve(tuple(filtered_output), overridden=False, inserted=tuple(inserted_clbids))

    def all_courses(self, ctx: 'RequirementContext') -> List['CourseInstance']:
        if self.source in (QuerySource.Courses, QuerySource.Claimed):
            return cast(List['CourseInstance'], [c for c in self.output])
        else:
            return []
