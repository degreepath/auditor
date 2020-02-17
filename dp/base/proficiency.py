import attr
from typing import List, Tuple, Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from .bases import Base
from .course import BaseCourseRule
from ..status import ResultStatus, WAIVED_AND_DONE

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data.course import CourseInstance  # noqa: F401


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

    def rank(self) -> Tuple[Decimal, Decimal]:
        status = self.status()

        if status in (ResultStatus.Done, ResultStatus.Waived):
            return Decimal(1), Decimal(1)

        if status is ResultStatus.PendingCurrent:
            return Decimal('0.75'), Decimal(1)

        if status is ResultStatus.PendingRegistered:
            return Decimal('0.5'), Decimal(1)

        return Decimal(0), Decimal(1)

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        if self.proficiency_status in WAIVED_AND_DONE:
            return self.proficiency_status

        if self.course:
            return self.course.status()

        return ResultStatus.Empty

    def all_courses(self, ctx: 'RequirementContext') -> List['CourseInstance']:
        return self.course.all_courses(ctx=ctx) if self.course else []
