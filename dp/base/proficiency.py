import attr
from typing import Tuple, Dict, Any, Optional
from fractions import Fraction

from .bases import Base
from .course import BaseCourseRule
from ..status import ResultStatus


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseProficiencyRule(Base):
    proficiency: str
    course: Optional[BaseCourseRule]
    proficiency_status: ResultStatus = ResultStatus.Empty
    path: Tuple[str, ...] = tuple()
    overridden: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "course": self.course.to_dict() if self.course else None,
            "proficiency": self.proficiency,
        }

    def type(self) -> str:
        return "proficiency"

    def rank(self) -> Fraction:
        status = self.status()

        if status in (ResultStatus.Done, ResultStatus.Waived):
            return Fraction(3, 3)

        if status is ResultStatus.PendingCurrent:
            return Fraction(2, 3)

        if status is ResultStatus.PendingRegistered:
            return Fraction(1, 3)

        return Fraction(0, 3)

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        return self.course.status() if self.course else self.proficiency_status
