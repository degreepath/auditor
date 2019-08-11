from dataclasses import dataclass
from typing import Any, Optional

from ..base import Result, BaseCourseRule


@dataclass(frozen=True)
class CourseResult(Result, BaseCourseRule):
    claim_attempt: Optional[Any]  # Optional[ClaimAttempt]
    min_grade_not_met: Optional[Any] = None  # Optional[CourseInstance]
    overridden: bool = False

    @staticmethod
    def from_solution(
        *,
        solution: BaseCourseRule,
        claim_attempt=None,
        min_grade_not_met=None,
        overridden: bool = False,
    ):
        return CourseResult(
            course=solution.course,
            hidden=solution.hidden,
            grade=solution.grade,
            allow_claimed=solution.allow_claimed,
            claim_attempt=claim_attempt,
            min_grade_not_met=min_grade_not_met,
            path=solution.path,
            overridden=overridden,
        )

    def to_dict(self):
        return {
            **super().to_dict(),
            "min_grade_not_met": self.min_grade_not_met.to_dict() if self.min_grade_not_met else None,
        }

    def claims(self):
        if self.claim_attempt:
            return [self.claim_attempt]
        else:
            return []

    def state(self):
        return "result"

    def was_overridden(self):
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.claim_attempt is not None and self.claim_attempt.failed() is False and self.min_grade_not_met is None

    def rank(self):
        return 1 if self.ok() else 0

    def max_rank(self):
        return 1
