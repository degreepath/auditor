import attr
from typing import List, Optional

from ..base import Result, BaseProficiencyRule, BaseCourseRule
from ..status import ResultStatus
from ..claim import Claim


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ProficiencyResult(Result, BaseProficiencyRule):
    @staticmethod
    def from_solution(
        *,
        solution: BaseProficiencyRule,
        status: ResultStatus,
        course_result: Optional[BaseCourseRule],
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
            proficiency_status=ResultStatus.Waived,
            overridden=True,
            course=solution.course,
            path=solution.path,
        )

    def claims(self) -> List[Claim]:
        return self.course.claims() if self.course else []

    def is_waived(self) -> bool:
        return self.overridden
