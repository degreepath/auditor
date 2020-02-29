from typing import Optional, Tuple, Dict, Any, Iterable, TYPE_CHECKING
import attr
from decimal import Decimal
import logging

from ..grades import GradeCode
from .clausable import Clausable
from .course_enums import GradeOption, SubType, CourseType, TranscriptCode, CourseTypeSortOrder

from .course_filters import clause_application_lookup

if TYPE_CHECKING:  # pragma: no cover
    from ..clause import SingleClause

logger = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True, order=False, hash=False)
class CourseInstance(Clausable):
    clbid: str
    attributes: Tuple[str, ...]
    credits: Decimal
    crsid: str
    course_type: CourseType
    gereqs: Tuple[str, ...]
    gpa_points: Decimal
    grade_code: GradeCode
    grade_option: GradeOption
    grade_points: Decimal
    institution: str
    is_in_gpa: bool
    is_in_progress: bool
    is_in_progress_this_term: bool
    is_in_progress_in_future: bool
    is_incomplete: bool
    is_repeat: bool
    is_stolaf: bool
    is_lab: bool
    level: int
    name: str
    number: str
    section: Optional[str]
    sub_type: SubType
    subject: str
    term: str
    transcript_code: TranscriptCode
    year: int
    yearterm: str

    identity_: str
    is_chbi_: Optional[int]

    def __str__(self) -> str:
        return self.identity_

    def __repr__(self) -> str:
        return f'Course("{self.identity_}")'

    def __hash__(self) -> int:
        return hash(self.clbid)

    def sort_order(self) -> Tuple[int, int, str, str]:
        key = CourseTypeSortOrder[self.course_type]
        return (key, self.year, self.term, self.clbid)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attributes": list(self.attributes),
            "clbid": self.clbid,
            "credits": str(self.credits),
            "crsid": self.crsid,
            "course_type": self.course_type.value,
            "gereqs": list(self.gereqs),
            "gpa_points": str(self.gpa_points),
            "grade_code": self.grade_code.value,
            "grade_option": self.grade_option.value,
            "grade_points": str(self.grade_points),
            "institution_short": self.institution,
            "flag_gpa": self.is_in_gpa,
            "flag_in_progress": self.is_in_progress,
            "flag_incomplete": self.is_incomplete,
            "flag_repeat": self.is_repeat,
            "flag_stolaf": self.is_stolaf,
            "flag_lab": self.is_lab,
            "level": self.level,
            "name": self.name,
            "number": self.number,
            "section": self.section,
            "subject": self.subject,
            "sub_type": self.sub_type.value,
            "term": self.term,
            "year": self.year,
            "transcript_code": self.transcript_code.value,
            "type": "course",
        }

    def attach_attrs(self, attributes: Iterable['str'] = tuple()) -> 'CourseInstance':
        attributes = tuple(attributes)

        if not attributes:
            attributes = tuple()

        return attr.evolve(self, attributes=tuple(attributes))

    def course(self) -> str:
        return self.identity_

    def verbose(self) -> str:
        return f'{self.course_with_term()} "{self.name}" {self.credits} {self.grade_code.value} #{int(self.clbid)}'

    def course_with_term(self) -> str:
        if self.sub_type is SubType.Lab:
            suffix = ".L"
        elif self.sub_type is SubType.Flac:
            suffix = ".F"
        elif self.sub_type is SubType.Discussion:
            suffix = ".D"
        else:
            suffix = ""

        return f"{self.subject} {self.number}{self.section or ''}{suffix} {self.year}-{self.term}"

    def apply_single_clause(self, clause: 'SingleClause') -> bool:
        # logger.debug("clause/compare/key=%s", clause.key)
        applicator = clause_application_lookup.get(clause.key, None)
        assert applicator is not None, TypeError(f'{clause.key} is not a known clause key')
        return applicator(self, clause)
