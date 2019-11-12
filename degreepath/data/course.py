from typing import Optional, Tuple, Dict, Any, Iterable, Callable, TYPE_CHECKING
import attr
from decimal import Decimal
import logging

from .clausable import Clausable
from .course_enums import GradeCode, GradeOption, SubType, CourseType, TranscriptCode, CourseTypeSortOrder
from ..lib import str_to_grade_points

if TYPE_CHECKING:  # pragma: no cover
    from ..clause import SingleClause

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, order=False, hash=True)
class CourseInstance(Clausable):
    clbid: str
    attributes: Tuple[str, ...]
    credits: Decimal
    crsid: str
    course_type: CourseType
    gereqs: Tuple[str, ...]
    grade_code: GradeCode
    grade_option: GradeOption
    grade_points: Decimal
    grade_points_gpa: Decimal
    is_in_gpa: bool
    is_in_progress: bool
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

    identity_: str
    is_chbi_: Optional[int]

    def __str__(self) -> str:
        return self.identity_

    def __repr__(self) -> str:
        return f'Course("{self.identity_}")'

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
            "grade_code": self.grade_code.value,
            "grade_option": self.grade_option.value,
            "grade_points": str(self.grade_points),
            "grade_points_gpa": str(self.grade_points_gpa),
            "is_in_gpa": self.is_in_gpa,
            "is_in_progress": self.is_in_progress,
            "is_incomplete": self.is_incomplete,
            "is_repeat": self.is_repeat,
            "is_stolaf": self.is_stolaf,
            "is_lab": self.is_lab,
            "level": self.level,
            "name": self.name,
            "number": self.number,
            "section": self.section,
            "subject": self.subject,
            "sub_type": self.sub_type.value,
            "term": self.term,
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

    def course_with_term(self) -> str:
        if self.sub_type is SubType.Lab:
            suffix = ".L"
        elif self.sub_type is SubType.Flac:
            suffix = ".F"
        elif self.sub_type is SubType.Discussion:
            suffix = ".D"
        else:
            suffix = ""

        return f"{self.subject} {self.number}{self.section or ' '}{suffix} {self.year}-{self.term}"

    def apply_single_clause(self, clause: 'SingleClause') -> bool:
        logger.debug("clause/compare/key=%s", clause.key)
        applicator = clause_application_lookup.get(clause.key, None)
        assert applicator is not None, TypeError(f'{clause.key} is not a known clause key')
        return applicator(self, clause)


def apply_single_clause__attributes(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.attributes)


def apply_single_clause__gereqs(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.gereqs)


def apply_single_clause__ap(course: CourseInstance, clause: 'SingleClause') -> bool:
    return course.course_type is CourseType.AP and clause.compare(course.name)


def apply_single_clause__number(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.number)


def apply_single_clause__course(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.identity_)


def apply_single_clause__subject(course: CourseInstance, clause: 'SingleClause') -> bool:
    # CH/BI 125 and 126 are "CHEM" courses, while 127/227 are "BIO".
    # So we pretend that that is the case, but only when checking subject codes.
    if course.is_chbi_ is not None:
        if course.is_chbi_ in (125, 126):
            return clause.compare('CHEM')
        else:
            return clause.compare('BIO')
    else:
        return clause.compare(course.subject)


def apply_single_clause__grade(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.grade_points)


def apply_single_clause__grade_code(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.grade_code.value)


def apply_single_clause__credits(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.credits)


def apply_single_clause__level(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.level)


def apply_single_clause__semester(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.term)


def apply_single_clause__su(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.grade_option is GradeOption.SU)


def apply_single_clause__pn(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.grade_option is GradeOption.PN)


def apply_single_clause__type(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.sub_type.name)


def apply_single_clause__course_type(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.course_type.name)


def apply_single_clause__lab(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.is_lab)


def apply_single_clause__grade_option(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.grade_option)


def apply_single_clause__is_stolaf(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.is_stolaf)


def apply_single_clause__is_in_gpa(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.is_in_gpa)


def apply_single_clause__is_in_progress(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.is_in_progress)


def apply_single_clause__year(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.year)


def apply_single_clause__clbid(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.clbid)


def apply_single_clause__crsid(course: CourseInstance, clause: 'SingleClause') -> bool:
    return clause.compare(course.crsid)


clause_application_lookup: Dict[str, Callable[[CourseInstance, 'SingleClause'], bool]] = {
    'attributes': apply_single_clause__attributes,
    'gereqs': apply_single_clause__gereqs,
    'ap': apply_single_clause__ap,
    'number': apply_single_clause__number,
    'course': apply_single_clause__course,
    'subject': apply_single_clause__subject,
    'grade': apply_single_clause__grade,
    'grade_code': apply_single_clause__grade_code,
    'credits': apply_single_clause__credits,
    'level': apply_single_clause__level,
    'semester': apply_single_clause__semester,
    's/u': apply_single_clause__su,
    'p/n': apply_single_clause__pn,
    'type': apply_single_clause__type,
    'course_type': apply_single_clause__course_type,
    'lab': apply_single_clause__lab,
    'grade_option': apply_single_clause__grade_option,
    'is_stolaf': apply_single_clause__is_stolaf,
    'is_in_gpa': apply_single_clause__is_in_gpa,
    'is_in_progress': apply_single_clause__is_in_progress,
    'year': apply_single_clause__year,
    'clbid': apply_single_clause__clbid,
    'crsid': apply_single_clause__crsid,
}


def load_course(data: Dict[str, Any]) -> CourseInstance:  # noqa: C901
    attributes = data.get('attributes', tuple())
    clbid = data['clbid']
    course_type = data['course_type']
    credits = data['credits']
    crsid = data['crsid']
    flag_gpa = data['flag_gpa']
    flag_incomplete = data['flag_incomplete']
    flag_in_progress = data['flag_in_progress']
    flag_repeat = data['flag_repeat']
    flag_stolaf = data['flag_stolaf']
    gereqs = data['gereqs']
    grade_code = data['grade_code']
    grade_option = data['grade_option']
    grade_points = data['grade_points']
    grade_points_gpa = data['grade_points_gpa']
    level = int(data['level'])
    name = data['name']
    number = data['number']
    section = data['section']
    sub_type = data['sub_type']
    subject = data.get('subject', data['subjects'])
    term = data['term']
    transcript_code = data['transcript_code']
    year = data['year']

    clbid = clbid
    term = int(term)
    credits = Decimal(credits)
    section = section or None

    subject = subject[0] if isinstance(subject, list) else subject

    grade_code = GradeCode(grade_code)
    grade_points = Decimal(grade_points)
    grade_points_gpa = Decimal(grade_points_gpa)
    grade_option = GradeOption(grade_option)
    sub_type = SubType(sub_type)
    course_type = CourseType(course_type)
    transcript_code = TranscriptCode(transcript_code)

    attributes = tuple(attributes) if attributes else tuple()
    gereqs = tuple(gereqs) if gereqs else tuple()

    if sub_type is SubType.Lab:
        suffix = ".L"
    elif sub_type is SubType.Flac:
        suffix = ".F"
    elif sub_type is SubType.Discussion:
        suffix = ".D"
    else:
        suffix = ""

    course_identity = f"{subject} {number}{suffix}"
    is_chbi = None
    if course_identity == 'CH/BI 125':
        is_chbi = 125
    elif course_identity == 'CH/BI 126':
        is_chbi = 126
    elif course_identity == 'CH/BI 127':
        is_chbi = 127
    elif course_identity == 'CH/BI 227':
        is_chbi = 227

    return CourseInstance(
        attributes=attributes,
        clbid=clbid,
        credits=credits,
        crsid=crsid,
        course_type=course_type,
        gereqs=gereqs,
        grade_code=grade_code,
        grade_option=grade_option,
        grade_points=grade_points,
        grade_points_gpa=grade_points_gpa,
        is_in_gpa=flag_gpa,
        is_in_progress=flag_in_progress,
        is_incomplete=flag_incomplete,
        is_repeat=flag_repeat,
        is_stolaf=flag_stolaf,
        is_lab=sub_type is SubType.Lab,
        level=level,
        name=name,
        number=number,
        section=section,
        sub_type=sub_type,
        subject=subject,
        term=term,
        transcript_code=transcript_code,
        year=year,
        identity_=course_identity,
        is_chbi_=is_chbi,
    )


def course_from_str(s: str, **kwargs: Any) -> CourseInstance:
    number = s.split(' ')[1]

    grade_code = kwargs.get('grade_code', 'B')
    grade_points = kwargs.get('grade_points', str_to_grade_points(grade_code))
    grade_points_gpa = kwargs.get('grade_points_gpa', grade_points)

    return load_course({
        "attributes": tuple(),
        "clbid": f"<clbid={str(hash(s))} term={str(kwargs.get('term', 'na'))}>",
        "course": s,
        "course_type": "SE",
        "credits": '1.00',
        "crsid": f"<crsid={str(hash(s))}>",
        "flag_gpa": True,
        "flag_in_progress": False,
        "flag_incomplete": False,
        "flag_repeat": False,
        "flag_stolaf": True,
        "gereqs": tuple(),
        "grade_option": GradeOption.Grade,
        "level": int(number) // 100 * 100,
        "name": s,
        "number": s.split(' ')[1],
        "section": "",
        "sub_type": SubType.Normal,
        "subjects": s.split(' ')[0],
        "term": "1",
        "transcript_code": "",
        "year": 2000,
        **kwargs,
        "grade_code": grade_code,
        "grade_points": grade_points,
        "grade_points_gpa": grade_points_gpa,
    })
