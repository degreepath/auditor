import attr
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from ..base import Result, BaseCourseRule

if TYPE_CHECKING:  # pragma: no cover
    from ..claim import ClaimAttempt  # noqa: F401
    from ..data import CourseInstance  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseResult(Result, BaseCourseRule):
    claim_attempt: Optional['ClaimAttempt']
    min_grade_not_met: Optional['CourseInstance']
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseCourseRule,
        claim_attempt: Optional['ClaimAttempt'] = None,
        min_grade_not_met: Optional['CourseInstance'] = None,
        overridden: bool = False,
    ) -> 'CourseResult':
        return CourseResult(
            course=solution.course,
            clbid=solution.clbid,
            hidden=solution.hidden,
            grade=solution.grade,
            grade_option=solution.grade_option,
            allow_claimed=solution.allow_claimed,
            claim_attempt=claim_attempt,
            min_grade_not_met=min_grade_not_met,
            path=solution.path,
            overridden=overridden,
            ap=solution.ap,
            institution=solution.institution,
            name=solution.name,
            inserted=solution.inserted,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "min_grade_not_met": self.min_grade_not_met.to_dict() if self.min_grade_not_met else None,
        }

    def claims(self) -> List['ClaimAttempt']:
        if self.claim_attempt:
            return [self.claim_attempt]
        else:
            return []

    def was_overridden(self) -> bool:
        return self.inserted or self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        if self.claim_attempt is None:
            return False

        if self.claim_attempt.failed is True:
            return False

        if self.min_grade_not_met is not None:
            return False

        if self.claim_attempt.claim.course.is_in_progress is True:
            return False

        return True
