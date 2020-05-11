import attr
from typing import List, Optional, TYPE_CHECKING
import logging

from ..base import Solution, BaseCourseRule
from ..result.course import CourseResult
from ..claim import Claim

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data.course import CourseInstance  # noqa: F401

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
            optional=rule.optional,
            year=rule.year,
            term=rule.term,
            section=rule.section,
            sub_type=rule.sub_type,
        )

    def audit(self, *, ctx: 'RequirementContext') -> CourseResult:
        if self.overridden:
            return CourseResult.from_solution(solution=self, overridden=self.overridden)

        claim: Optional[Claim] = None

        for insert in ctx.get_insert_exceptions(self.path):
            logger.debug('inserting %s into %s due to override', insert.clbid, self)
            matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)

            claim = ctx.make_claim(course=matched_course, path=self.path, allow_claimed=insert.forced or self.allow_claimed)

            if not claim.failed:
                logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())
                return CourseResult.from_solution(solution=self, claim_attempt=claim, overridden=True)

        for matched_course in ctx.find_courses(rule=self, from_claimed=self.from_claimed):
            if self.grade is not None and matched_course.is_in_progress is False and matched_course.grade_points < self.grade:
                logger.debug('%s course "%s" exists, but the grade of %s is below the allowed minimum grade of %s', self.path, self.identifier(), matched_course.grade_points, self.grade)
                continue

            if self.grade_option is not None and matched_course.grade_option != self.grade_option:
                logger.debug('%s course "%s" exists, but the course was taken %s, and the area requires that it be taken %s', self.path, self.identifier(), matched_course.grade_option, self.grade_option)
                continue

            claim = ctx.make_claim(course=matched_course, path=self.path, allow_claimed=self.allow_claimed)

            if self.from_claimed:
                assert claim.failed is False

            if not claim.failed:
                logger.debug('%s course "%s" exists, and has not been claimed', self.path, matched_course.course())
                return CourseResult.from_solution(solution=self, claim_attempt=claim)

            logger.debug('%s course "%s" exists, but has already been claimed by other rules', self.path, matched_course.course())

        logger.debug('%s course "%s" could not be claimed', self.path, self.identifier())
        return CourseResult.from_solution(solution=self, claim_attempt=claim)

    def all_courses(self, ctx: 'RequirementContext') -> List['CourseInstance']:
        return list(ctx.find_courses(rule=self, from_claimed=self.from_claimed))
