from dataclasses import dataclass
from typing import List
import logging

from ..base import Solution, BaseCourseRule
from ..result.course import CourseResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CourseSolution(Solution, BaseCourseRule):
    @staticmethod
    def from_rule(*, rule: BaseCourseRule):
        return CourseSolution(
            course=rule.course,
            hidden=rule.hidden,
            grade=rule.grade,
            allow_claimed=rule.allow_claimed,
        )

    def __repr__(self):
        return self.course

    def audit(self, *, ctx, path: List):
        path = [*path, f"$c->{self.course}"]

        matched_course = ctx.find_course(self.course)
        if matched_course is None:
            logger.debug('%s course "%s" does not exist in the transcript', path, self.course)
            return CourseResult.from_solution(solution=self, claim_attempt=None)

        if self.grade is not None and matched_course.grade_points < self.grade:
            logger.debug('%s course "%s" exists, but the grade of %s is below the allowed minimum grade of %s', path, self.course, matched_course.grade_points, self.grade)
            return CourseResult.from_solution(solution=self, claim_attempt=None, min_grade_not_met=matched_course)

        claim = ctx.make_claim(course=matched_course, path=path, clause=self)

        if claim.failed():
            logger.debug('%s course "%s" exists, but has already been claimed by %s', path, self.course, claim.conflict_with)
            return CourseResult.from_solution(solution=self, claim_attempt=claim)

        logger.debug('%s course "%s" exists, and has not been claimed', path, self.course)

        return CourseResult.from_solution(solution=self, claim_attempt=claim)
