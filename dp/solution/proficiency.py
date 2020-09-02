import attr
from typing import Optional, TYPE_CHECKING
import logging

from ..base import Solution, BaseProficiencyRule
from ..result.proficiency import ProficiencyResult
from .course import CourseSolution

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ProficiencySolution(Solution, BaseProficiencyRule):
    @staticmethod
    def from_rule(*, rule: BaseProficiencyRule, course_solution: Optional[CourseSolution], overridden: bool = False) -> 'ProficiencySolution':
        return ProficiencySolution(
            proficiency=rule.proficiency,
            course=course_solution,
            path=rule.path,
            overridden=overridden,
        )

    @staticmethod
    def overridden_from_rule(*, rule: BaseProficiencyRule) -> 'ProficiencySolution':
        return ProficiencySolution(
            proficiency=rule.proficiency,
            course=rule.course,
            path=rule.path,
            overridden=True,
        )

    def audit(self, *, ctx: 'RequirementContext') -> ProficiencyResult:
        if self.overridden:
            return ProficiencyResult.overridden_from_solution(solution=self)

        proficiency_status = ctx.music_proficiencies.status(of=self.proficiency, exam_only=False)
        course_result = self.course.audit(ctx=ctx) if isinstance(self.course, CourseSolution) else self.course

        logger.debug('%s proficiency in "%s" is %s', self.path, self.proficiency, proficiency_status)
        return ProficiencyResult.from_solution(solution=self, course_result=course_result, status=proficiency_status)
