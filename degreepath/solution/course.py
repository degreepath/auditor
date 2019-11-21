import attr
from typing import Optional, TYPE_CHECKING
import logging

from ..base import Solution, BaseCourseRule
from ..result.course import CourseResult
from ..claim import ClaimAttempt

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseSolution(Solution, BaseCourseRule):
    @staticmethod
    def from_rule(*, rule: BaseCourseRule, overridden: bool = False) -> 'CourseSolution':
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
            inserted=rule.inserted,
            grade_option=rule.grade_option,
        )

    def audit(self, *, ctx: 'RequirementContext') -> CourseResult:
        if self.overridden:
            return CourseResult.from_solution(solution=self, overridden=self.overridden)

        claim: Optional[ClaimAttempt] = None

        for insert in ctx.get_insert_exceptions(self.path):
            logger.debug('inserting %s into %s due to override', insert.clbid, self)
            matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)

            claim = ctx.make_claim(course=matched_course, path=self.path, allow_claimed=insert.forced)

            if not claim.failed:
                logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())
                return CourseResult.from_solution(solution=self, claim_attempt=claim, overridden=True)

        # don't forget to update the callsite in rule.course#all_matches when updating this
        for matched_course in ctx.find_courses(course=self.course, ap=self.ap, institution=self.institution, name=self.name, clbid=self.clbid):
            if self.grade is not None and matched_course.is_in_progress is False and matched_course.grade_points < self.grade:
                logger.debug('%s course "%s" exists, but the grade of %s is below the allowed minimum grade of %s', self.path, self.identifier(), matched_course.grade_points, self.grade)
                continue

            if self.grade_option is not None and matched_course.grade_option != self.grade_option:
                logger.debug('%s course "%s" exists, but the course was taken %s, and the area requires that it be taken %s', self.path, self.identifier(), matched_course.grade_option, self.grade_option)
                continue

            claim = ctx.make_claim(course=matched_course, path=self.path, allow_claimed=self.allow_claimed)

            if not claim.failed:
                logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())
                return CourseResult.from_solution(solution=self, claim_attempt=claim)

            logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, matched_course.course(), claim.conflict_with)

        logger.debug('%s course "%s" could not be claimed', self.path, self.identifier())
        return CourseResult.from_solution(solution=self, claim_attempt=claim)
