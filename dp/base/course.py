import attr
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal

from .bases import Base
from ..data.course_enums import GradeOption
from ..status import ResultStatus


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseCourseRule(Base):
    course: Optional[str] = None
    clbid: Optional[str] = None
    ap: Optional[str] = None
    institution: Optional[str] = None
    name: Optional[str] = None
    hidden: bool = False
    grade: Optional[Decimal] = None
    grade_option: Optional[GradeOption] = None
    allow_claimed: bool = False
    from_claimed: bool = False
    path: Tuple[str, ...] = tuple()
    inserted: bool = False
    overridden: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "course": self.course,
            "clbid": self.clbid,
            "hidden": self.hidden,
            "grade": str(self.grade) if self.grade is not None else None,
            "claims": [c.to_dict() for c in self.claims()],
            "ap": self.ap,
            "institution": self.institution,
            "name": self.name,
        }

    def type(self) -> str:
        return "course"

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

        matched = self.matched()
        has_ip_courses = any(c.is_in_progress for c in matched)
        has_enrolled_courses = any(c.is_in_progress_this_term for c in matched)
        has_registered_courses = any(c.is_in_progress_in_future for c in matched)

        if has_ip_courses and has_enrolled_courses and (not has_registered_courses):
            return ResultStatus.PendingCurrent
        elif has_ip_courses and has_registered_courses:
            return ResultStatus.PendingRegistered

        return ResultStatus.Empty

    def identifier(self) -> str:
        items = {'course': self.course, 'ap': self.ap, 'name': self.name, 'institution': self.institution}
        return ' '.join(f"{k}:{v}" for k, v in items.items())
