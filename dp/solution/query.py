import attr
from typing import List, Sequence, Any, Tuple, Dict, Optional, cast, TYPE_CHECKING
import logging

from ..base import Solution, BaseQueryRule
from ..base.query import QuerySource
from ..result.query import QueryResult
from ..data.clausable import Clausable
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
    @staticmethod
    def from_rule(
        *,
        rule: BaseQueryRule,
        output: Tuple[Clausable, ...],
        inserted: Tuple[str, ...] = tuple(),
        force_inserted: Tuple[str, ...] = tuple(),
    ) -> 'QuerySolution':
        return QuerySolution(
            source=rule.source,
            data_type=rule.data_type,
            assertions=rule.assertions,
            limit=rule.limit,
            where=rule.where,
            allow_claimed=rule.allow_claimed,
            attempt_claims=rule.attempt_claims,
            record_claims=rule.record_claims,
            path=rule.path,
            overridden=rule.overridden,
            inserted=rule.inserted + inserted,
            force_inserted=rule.force_inserted + force_inserted,
            output=output,
            successful_claims=tuple(),
            failed_claims=tuple(),
        )

    def audit(self, *, ctx: 'RequirementContext') -> QueryResult:
        logger.debug("auditing data for %s", self.path)

        if self.overridden:
            return QueryResult.from_solution(
                solution=self,
                successful_claims=tuple(),
                failed_claims=tuple(),
                overridden=self.overridden,
                assertions=self.assertions,
            )

        if self.source is QuerySource.Courses:
            collected_result = self.collect_courses(ctx)
        elif self.source is QuerySource.Claimed:
            collected_result = self.collect_claimed_courses(ctx)
        elif self.source is QuerySource.Areas:
            collected_result = self.collect_areas()
        elif self.source is QuerySource.MusicPerformances:
            collected_result = self.collect_music_performances()
        elif self.source is QuerySource.MusicAttendances:
            collected_result = self.collect_music_attendances()
        else:
            raise TypeError(f'invalid source type {self.source!r}')

        # Skip checking any assertions if nothing has been claimed. This is
        # not a performance optimization; instead, this ensures that
        # less-than assertions don't turn green when there's nothing for them
        # to assert against, for example:
        #
        # Requirement: Performance Studies [needs-more-items]
        #     [needs-more-items] Given all 0 courses matching subject == MUSPF and credits == 1.0 and level ∈ [100, 200] and name == '' and institution == STOLAF
        #         There must be:
        #           - count(terms) ≥ 6 [empty]
        #           - count(terms) where level == 100 ≤ 4 [done]
        #
        # when in fact we would expect
        #
        # Requirement: Performance Studies [needs-more-items]
        #     [needs-more-items] Given all 0 courses matching subject == MUSPF and credits == 1.0 and level ∈ [100, 200] and name == '' and institution == STOLAF
        #         There must be:
        #           - count(terms) ≥ 6 [empty]
        #           - count(terms) where level == 100 ≤ 4 [empty]
        #
        # since there were no courses matching the filter.
        has_non_primary_lt_clause = any(a.is_lt_clause() for a in self.assertions) and not all(a.is_lt_clause() for a in self.assertions)
        if self.source is QuerySource.Courses and len(collected_result.claimed_items) == 0 and has_non_primary_lt_clause:
            assertions = self.assertions
        else:
            assertions = tuple(a.audit_and_resolve(collected_result.claimed_items, ctx=ctx) for a in self.assertions)

        logger.debug("done auditing data for %s", self.path)

        return QueryResult.from_solution(
            solution=self,
            assertions=assertions,
            successful_claims=collected_result.successful_claims,
            failed_claims=collected_result.failed_claims,
        )

    def collect_courses(self, ctx: 'RequirementContext') -> AuditResult:
        global debug
        if debug is None:
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

    def collect_claimed_courses(self, ctx: 'RequirementContext') -> AuditResult:
        claimed_items: List[Clausable] = []
        successful_claims: List[Claim] = []

        output: List['CourseInstance'] = ctx.all_claimed()
        if self.where:
            output = [item for item in output if self.where.apply(item)]

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

    def collect_areas(self) -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def collect_music_performances(self) -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def collect_music_attendances(self) -> AuditResult:
        return AuditResult(claimed_items=tuple(self.output))

    def all_courses(self, ctx: 'RequirementContext') -> List['CourseInstance']:
        if self.source in (QuerySource.Courses, QuerySource.Claimed):
            return cast(List['CourseInstance'], list(self.output))
        else:
            return []
