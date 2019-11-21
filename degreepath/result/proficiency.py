import attr
from typing import List, TYPE_CHECKING

from ..base import Result, BaseProficiencyRule, BaseCourseRule
from ..status import ResultStatus

if TYPE_CHECKING:  # pragma: no cover
    from ..claim import ClaimAttempt  # noqa: F401
    from ..data import CourseInstance  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ProficiencyResult(Result, BaseProficiencyRule):
    proficiency_status: ResultStatus

    @staticmethod
    def from_solution(
        *,
        solution: BaseProficiencyRule,
        status: ResultStatus,
        course_result: BaseCourseRule,
        overridden: bool = False,
    ) -> 'ProficiencyResult':
        return ProficiencyResult(
            proficiency=solution.proficiency,
            proficiency_status=status,
            overridden=overridden,
            course=course_result,
            path=solution.path,
        )

    @staticmethod
    def overridden_from_solution(*, solution: BaseProficiencyRule) -> 'ProficiencyResult':
        return ProficiencyResult(
            proficiency=solution.proficiency,
            proficiency_status=ResultStatus.Pass,
            overridden=True,
            course=solution.course,
            path=solution.path,
        )

    def claims(self) -> List['ClaimAttempt']:
        return self.course.claims()

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        return self.proficiency_status is ResultStatus.Pass or self.course.ok()
