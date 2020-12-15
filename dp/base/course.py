import attr
from typing import Optional, Tuple, Dict, FrozenSet, Any, TYPE_CHECKING
from decimal import Decimal

from .bases import Base
from ..data.course_enums import GradeOption
from ..status import ResultStatus

if TYPE_CHECKING:  # pragma: no cover
    from ..data.course import CourseInstance  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseCourseRule(Base):
    # how to find the course
    course: Optional[str] = None
    clbid: Optional[str] = None
    crsid: Optional[str] = None
    ap: Optional[str] = None
    institution: Optional[str] = None
    name: Optional[str] = None

    # additional filtering on the course
    grade: Optional[Decimal] = None
    grade_option: Optional[GradeOption] = None
    year: Optional[int] = None
    term: Optional[str] = None
    section: Optional[str] = None
    sub_type: Optional[str] = None

    # logical modifiers
    hidden: bool = False
    allow_claimed: bool = False
    from_claimed: bool = False
    optional: bool = False
    inserted: bool = False
    forced: bool = False
    auto_waived: bool = False
    excluded_clbids: FrozenSet[str] = frozenset()

    # state
    matched_course: Optional['CourseInstance'] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "course": self.course,
            "clbid": self.clbid,
            "crsid": self.crsid,
            "ap": self.ap,
            "institution": self.institution,
            "name": self.name,
            "grade": str(self.grade) if self.grade is not None else None,
            "grade_option": str(self.grade_option) if self.grade_option is not None else None,
            "year": self.year,
            "term": self.term,
            "section": self.section,
            "sub_type": self.sub_type,
            "hidden": self.hidden,
            "allow_claimed": self.allow_claimed,
            "from_claimed": self.from_claimed,
            "optional": self.optional,
            "inserted": self.inserted,
            "forced": self.forced,
            "auto_waived": self.auto_waived,
            "excluded_clbids": sorted(self.excluded_clbids),
            "claims": [c.to_dict() for c in self.claims()],
            "matched_scedid": self.matched_course.schedid if self.matched_course else None,
        }

    def type(self) -> str:
        return "course"

    def rank(self) -> Tuple[Decimal, Decimal]:
        status = self.status()

        if self.optional:
            return Decimal(1), Decimal(1)

        if status in (ResultStatus.Done, ResultStatus.Waived):
            return Decimal(1), Decimal(1)

        if status is ResultStatus.PendingCurrent:
            return Decimal('0.75'), Decimal(1)

        if status is ResultStatus.PendingRegistered:
            return Decimal('0.5'), Decimal(1)

        return Decimal(0), Decimal(1)

    def status(self) -> ResultStatus:
        if self.is_waived():
            return ResultStatus.Waived

        matched = self.matched()
        has_ip_courses = any(c.is_in_progress for c in matched)

        if matched and not has_ip_courses:
            return ResultStatus.Done

        has_enrolled_courses = any(c.is_in_progress_this_term or c.is_incomplete for c in matched)
        has_registered_courses = any(c.is_in_progress_in_future for c in matched)

        if has_ip_courses and has_enrolled_courses and (not has_registered_courses):
            return ResultStatus.PendingCurrent
        elif has_ip_courses and has_registered_courses:
            return ResultStatus.PendingRegistered

        if self.optional:
            return ResultStatus.Waived

        return ResultStatus.Empty

    def identifier(self) -> str:
        items = {'course': self.course, 'ap': self.ap, 'name': self.name, 'institution': self.institution}
        return ', '.join(f"{k}={v}" for k, v in items.items())
