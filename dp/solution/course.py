import attr
from typing import List, Optional, TYPE_CHECKING
import logging

from ..base import Solution, BaseCourseRule
from ..result.course import CourseResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data.course import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseSolution(Solution, BaseCourseRule):
    matched_course: Optional['CourseInstance'] = None
    was_forced: bool = False

    @staticmethod
    def from_rule(*, rule: BaseCourseRule, course: Optional['CourseInstance'], was_inserted: bool = False, was_forced: bool = False, overridden: bool = False) -> 'CourseSolution':
        return CourseSolution(
            course=rule.course,
            clbid=rule.clbid,
            hidden=rule.hidden,
            grade=rule.grade,
            allow_claimed=rule.allow_claimed,
            path=rule.path,
            overridden=overridden,
            ap=rule.ap,
            institution=rule.institution,
            name=rule.name,
            inserted=rule.inserted or was_inserted,
            grade_option=rule.grade_option,
            optional=rule.optional,
            year=rule.year,
            term=rule.term,
            section=rule.section,
            sub_type=rule.sub_type,
            was_forced=was_forced,
            matched_course=course,
        )

    def audit(self, *, ctx: 'RequirementContext') -> CourseResult:
        if self.overridden:
            return CourseResult.from_solution(solution=self, overridden=self.overridden)

        if self.matched_course is None:
            logger.debug('no courses matching %r [at %s]', self.identifier(), self.path)
            return CourseResult.from_solution(solution=self, claim_attempt=None, overridden=False)

        if self.from_claimed and not ctx.has_claim(clbid=self.matched_course.clbid):
            logger.debug('no pre-claimed courses matching %r [at %s]', self.identifier(), self.path)
            return CourseResult.from_solution(solution=self, claim_attempt=None, overridden=False)

        logger.debug('attempting claim for %r [at %s]', self.matched_course, self.path)
        claim = ctx.make_claim(course=self.matched_course, path=self.path, allow_claimed=self.was_forced or self.allow_claimed)

        if self.from_claimed:
            assert claim.failed is False

        if claim.failed:
            logger.debug('%r exists, but has already been claimed by other rules [at %s]', self.matched_course, self.path)
            return CourseResult.from_solution(solution=self, claim_attempt=claim, overridden=False)

        logger.debug('%r exists, and is available [at %s]', self.matched_course, self.path)
        return CourseResult.from_solution(solution=self, claim_attempt=claim, overridden=False)

    def all_courses(self, ctx: 'RequirementContext') -> List['CourseInstance']:
        return list(ctx.find_courses(rule=self, from_claimed=self.from_claimed))
