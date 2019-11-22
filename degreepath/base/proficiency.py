import attr
from typing import Tuple, Dict, Any, Optional
from decimal import Decimal

from .bases import Base
from .course import BaseCourseRule


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseProficiencyRule(Base):
    proficiency: str
    course: Optional[BaseCourseRule]
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

    def rank(self) -> Decimal:
        if self.in_progress():
            return Decimal('0.5')

        if self.ok():
            return Decimal('1')

        return Decimal('0')

    def in_progress(self) -> bool:
        return self.course.in_progress() if self.course else False

    def max_rank(self) -> int:
        return 1
