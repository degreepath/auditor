import attr
from typing import TYPE_CHECKING
import logging

from ..base import Solution, BaseCourseRule
from ..result.course import CourseResult
from ..exception import InsertionException

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

        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            logger.debug('inserting %s into %s due to override', exception.clbid, self)
            matched_course = ctx.forced_course_by_clbid(exception.clbid)

        else:
            _matched_course = ctx.find_course(self.course)

            if _matched_course is None:
                logger.debug('%s course "%s" does not exist in the transcript', self.path, self.course)
                return CourseResult.from_solution(solution=self, claim_attempt=None)

            matched_course = _matched_course

            if self.grade is not None and matched_course.grade_points < self.grade:
                logger.debug('%s course "%s" exists, but the grade of %s is below the allowed minimum grade of %s', self.path, self.course, matched_course.grade_points, self.grade)
                return CourseResult.from_solution(solution=self, claim_attempt=None, min_grade_not_met=matched_course)

        claim = ctx.make_claim(course=matched_course, path=self.path, clause=self)

        if claim.failed():
            logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, matched_course.course(), claim.conflict_with)
            return CourseResult.from_solution(solution=self, claim_attempt=claim)

        logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())

        return CourseResult.from_solution(solution=self, claim_attempt=claim)
