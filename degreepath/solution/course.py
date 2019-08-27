import attr
from typing import Optional, TYPE_CHECKING
import logging

from ..base import Solution, BaseCourseRule
from ..result.course import CourseResult
from ..exception import InsertionException
from ..claim import ClaimAttempt

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseSolution(Solution, BaseCourseRule):
    overridden: bool

    @staticmethod
    def from_rule(*, rule: BaseCourseRule, overridden: bool = False) -> 'CourseSolution':
        return CourseSolution(
            course=rule.course,
            hidden=rule.hidden,
            grade=rule.grade,
            allow_claimed=rule.allow_claimed,
            path=rule.path,
            overridden=overridden,
        )

    def audit(self, *, ctx: 'RequirementContext') -> CourseResult:
        if self.overridden:
            return CourseResult.from_solution(solution=self, overridden=self.overridden)

        claim: Optional[ClaimAttempt] = None

        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            logger.debug('inserting %s into %s due to override', exception.clbid, self)
            matched_course = ctx.forced_course_by_clbid(exception.clbid)

            claim = ctx.make_claim(course=matched_course, path=self.path, clause=self)

            if not claim.failed():
                logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())
                return CourseResult.from_solution(solution=self, claim_attempt=claim, overridden=True)

        for matched_course in ctx.find_all_courses(self.course):
            if self.grade is not None and matched_course.grade_points < self.grade:
                logger.debug('%s course "%s" exists, but the grade of %s is below the allowed minimum grade of %s', self.path, self.course, matched_course.grade_points, self.grade)
                continue

            claim = ctx.make_claim(course=matched_course, path=self.path, clause=self)

            if not claim.failed():
                logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())
                return CourseResult.from_solution(solution=self, claim_attempt=claim)

            logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, matched_course.course(), claim.conflict_with)

        logger.debug('%s course "%s" could not be claimed', self.path, self.course)
        return CourseResult.from_solution(solution=self, claim_attempt=claim)
