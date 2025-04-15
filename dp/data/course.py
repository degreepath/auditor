from typing import Optional, Tuple, Dict, Sequence, Any, Iterable, Callable, Union, cast, TYPE_CHECKING
import attr
from decimal import Decimal, ROUND_DOWN
import logging

from .clausable import Clausable, ClausableIdentifier
from .course_enums import GradeCode, GradeOption, SubType, CourseType, TranscriptCode, CourseTypeSortOrder
from ..lib import str_to_grade_points
from ..exception import CourseOverrideException, ExceptionAction, CourseCreditOverride, CourseSubjectOverride

if TYPE_CHECKING:  # pragma: no cover
    from ..predicate_clause import Predicate

logger = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True, order=False, hash=False, repr=False)
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
    is_during_covid: bool
    level: int
    name: str
    number: str
    schedid: str
    section: Optional[str]
    sub_type: SubType
    subject: str
    su_grade_code: Optional[GradeCode]
    term: str
    transcript_code: TranscriptCode
    year: str
    yearterm: str

    identity_: str
    is_chbi_: Optional[int]
    hash_cache_: Optional[int] = None

    def to_identifier(self) -> ClausableIdentifier:
        return ClausableIdentifier(type="class", key="scedid", value=self.schedid)

    def __str__(self) -> str:
        return self.verbose()

    def __repr__(self) -> str:
        return f'Course({self.verbose()!r})'

    def __hash__(self) -> int:
        if self.hash_cache_ is None:
            object.__setattr__(self, 'hash_cache_', hash(self.clbid))
        return cast(int, self.hash_cache_)

    def sort_order(self) -> Tuple[int, str, str, str]:
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

    def attach_attrs(self, attributes: Iterable[str] = tuple()) -> 'CourseInstance':
        attributes = tuple(attributes)

        if not attributes:
            attributes = tuple()

        return attr.evolve(self, attributes=tuple(attributes))

    def unique_clbid_via_schedid(self) -> 'CourseInstance':
        return attr.evolve(self, clbid=f"{self.clbid}:{self.schedid}")

    def course(self) -> str:
        return self.identity_

    def verbose(self) -> str:
        attrs = ''
        if self.attributes:
            attrs = ' ' + ' '.join('#' + a for a in sorted(self.attributes))
        if self.institution == 'STOLAF':
            return f'{self.course_with_term()} "{self.name}" {self.credits} {self.grade_code.value} id={self.clbid}{attrs}'
        else:
            return f'{self.course_with_term()} "{self.name}" [{self.institution}] {self.credits} {self.grade_code.value} #{self.clbid}{attrs}'

    def pretty(self) -> str:
        if self.institution == 'STOLAF':
            return f'{self.course_with_term()} "{self.name}"'
        else:
            return f'[{self.institution}] {self.course_with_term()} "{self.name}"'

    def course_with_term(self) -> str:
        if self.sub_type is SubType.Lab:
            suffix = ".L"
        elif self.sub_type is SubType.Flac:
            suffix = ".F"
        elif self.sub_type is SubType.Discussion:
            suffix = ".D"
        else:
            suffix = ""

        return f"{self.subject} {self.number}{self.section or ''}{suffix} {self.year_term()}"

    def year_term(self) -> str:
        return f"{self.year}-{self.term}"

    def apply_predicate(self, clause: 'Predicate') -> bool:
        # logger.debug("clause/compare/key=%s", clause.key)
        applicator = clause_application_lookup.get(clause.key, None)
        assert applicator is not None, TypeError(f'{clause.key} is not a known clause key')
        return applicator(self, clause)


def apply_predicate__attributes(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.attributes)


def apply_predicate__gereqs(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.gereqs)


def apply_predicate__ap(course: CourseInstance, clause: 'Predicate') -> bool:
    return course.course_type is CourseType.AP and clause.compare(course.name)


def apply_predicate__number(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.number)


def apply_predicate__institution(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.institution)


def apply_predicate__course(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.identity_)


def apply_predicate__subject(course: CourseInstance, clause: 'Predicate') -> bool:
    # CH/BI 125 and 126 are "CHEM" courses, while 127/227 are "BIO".
    # So we pretend that that is the case, but only when checking subject codes.
    if course.is_chbi_ is not None:
        if course.is_chbi_ in (125, 126):
            return clause.compare('CHEM')
        else:
            return clause.compare('BIO')
    else:
        return clause.compare(course.subject)


def apply_predicate__grade(course: CourseInstance, clause: 'Predicate') -> bool:
    value = course.grade_code

    if course.is_during_covid:
        # if the course was taken during COVID, we pass through the internal grade code
        if course.grade_code is GradeCode._S and course.su_grade_code is not None:
            value = course.su_grade_code

        return clause.compare_in_covid(value)
    else:
        return clause.compare(value)


def apply_predicate__credits(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.credits)


def apply_predicate__level(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.level)


def apply_predicate__semester(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.term)


def apply_predicate__type(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.sub_type.name)


def apply_predicate__course_type(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.course_type.name)


def apply_predicate__lab(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.is_lab)


def apply_predicate__grade_option(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.grade_option)


def apply_predicate__is_stolaf(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.is_stolaf)


def apply_predicate__is_in_gpa(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.is_in_gpa)


def apply_predicate__is_in_progress(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.is_in_progress)


def apply_predicate__year(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.year)


def apply_predicate__clbid(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.clbid)


def apply_predicate__crsid(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.crsid)


def apply_predicate__name(course: CourseInstance, clause: 'Predicate') -> bool:
    return clause.compare(course.name)


clause_application_lookup: Dict[str, Callable[[CourseInstance, 'Predicate'], bool]] = {
    'ap': apply_predicate__ap,
    'attributes': apply_predicate__attributes,
    'attribute': apply_predicate__attributes,
    'clbid': apply_predicate__clbid,
    'course': apply_predicate__course,
    'course_type': apply_predicate__course_type,
    'credits': apply_predicate__credits,
    'crsid': apply_predicate__crsid,
    'gereqs': apply_predicate__gereqs,
    'grade': apply_predicate__grade,
    'grade_option': apply_predicate__grade_option,
    'institution': apply_predicate__institution,
    'is_in_gpa': apply_predicate__is_in_gpa,
    'is_in_progress': apply_predicate__is_in_progress,
    'is_stolaf': apply_predicate__is_stolaf,
    'lab': apply_predicate__lab,
    'level': apply_predicate__level,
    'name': apply_predicate__name,
    'number': apply_predicate__number,
    'semester': apply_predicate__semester,
    'subject': apply_predicate__subject,
    'type': apply_predicate__type,
    'year': apply_predicate__year,
}


def load_course(  # noqa: C901
    data: Union[Dict, CourseInstance],
    *,
    current_term: Optional[str] = None,
    overrides: Sequence[CourseOverrideException] = tuple(),
    credits_overrides: Optional[Dict[str, str]] = None,
) -> CourseInstance:  # noqa: C901
    if not credits_overrides:
        credits_overrides = {}

    if isinstance(data, CourseInstance):
        return data

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
    institution = data['institution_short']
    level = data['level']
    name = data['name']
    number = data['number']
    schedid = data.get('schedid', None)
    section = data['section']
    sub_type = data['sub_type']
    subject = data['subject']
    su_grade_code = data.get('su_grade_code', '?')
    term = data['term']
    transcript_code = data['transcript_code']
    year = data['year']

    applicable_overrides = {o.type: o for o in overrides if o.clbid == clbid}
    subject_override = applicable_overrides.get(ExceptionAction.CourseSubject, None)
    credits_override = applicable_overrides.get(ExceptionAction.CourseCredits, None)

    # find a default credits override, if one exists in the area spec
    credits_override_key = f"name={name}"
    if not credits_override and credits_override_key in credits_overrides:
        amount = Decimal(credits_overrides[credits_override_key])
        credits_override = CourseCreditOverride(path=tuple(), clbid=clbid, type=ExceptionAction.CourseCredits, credits=amount)

    if credits_override:
        credits = cast(CourseCreditOverride, credits_override).credits

    if subject_override:
        subject = cast(CourseSubjectOverride, subject_override).subject

    year = int(year)
    credits = Decimal(credits)
    section = section or None
    level = int(level)

    grade_code = GradeCode(grade_code)
    grade_points = Decimal(grade_points)
    grade_option = GradeOption(grade_option)
    sub_type = SubType(sub_type)
    course_type = CourseType(course_type)
    transcript_code = TranscriptCode(transcript_code)

    if su_grade_code == '?':
        su_grade_code = None
    else:
        su_grade_code = GradeCode(su_grade_code)

    in_progress_this_term = False
    in_progress_in_future = False

    if current_term and grade_code in (GradeCode._IP, GradeCode._I):
        if f"{year}{term}" <= current_term:
            in_progress_this_term = True
        elif f"{year}{term}" > current_term:
            in_progress_in_future = True

    # GPA points are the (truncated to two decimal places!) result of GP * credits.
    # If someone gets an A- in a 0.25-credit course, they are supposed to
    # receive 0.92 gpa points, because `0.25 * 3.7 => 0.925` but we truncate
    # everything to do with GPA at 2 decimal places.
    gpa_points = Decimal(grade_points * credits).quantize(Decimal('1.00'), rounding=ROUND_DOWN)

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

    yearterm = f"{year}{term}"

    is_during_covid = yearterm == "20193"

    return CourseInstance(
        attributes=attributes,
        clbid=clbid,
        credits=credits,
        crsid=crsid,
        course_type=course_type,
        gereqs=gereqs,
        gpa_points=gpa_points,
        grade_code=grade_code,
        grade_option=grade_option,
        grade_points=grade_points,
        institution=institution,
        is_in_gpa=flag_gpa,
        is_in_progress=flag_in_progress,
        is_in_progress_this_term=in_progress_this_term,
        is_in_progress_in_future=in_progress_in_future,
        is_incomplete=flag_incomplete,
        is_repeat=flag_repeat,
        is_stolaf=flag_stolaf,
        is_lab=sub_type is SubType.Lab,
        is_during_covid=is_during_covid,
        level=level,
        name=name,
        number=number,
        schedid=schedid,
        section=section,
        sub_type=sub_type,
        subject=subject,
        su_grade_code=su_grade_code,
        term=term,
        transcript_code=transcript_code,
        year=year,
        identity_=course_identity,
        is_chbi_=is_chbi,
        yearterm=yearterm,
    )


def course_from_str(s: str, *, in_progress: bool = False, **kwargs: Any) -> CourseInstance:
    number = s.split(' ')[1]

    assert type(kwargs.get('term', '')) is str
    assert type(kwargs.get('year', 0)) is int

    if in_progress:
        flag_in_progress = True
        grade_code = 'IP'
    else:
        flag_in_progress = False
        grade_code = kwargs.get('grade_code', 'B')

    grade_points = kwargs.get('grade_points', str_to_grade_points(grade_code))

    return load_course({
        "attributes": tuple(),
        "clbid": f"<clbid={str(hash(s))} term={str(kwargs.get('year', 'na'))}/{str(kwargs.get('term', 'na'))}>",
        "course": s,
        "course_type": "SE",
        "credits": '1.00',
        "crsid": f"<crsid={str(hash(s))}>",
        "flag_gpa": True,
        "flag_in_progress": flag_in_progress,
        "flag_incomplete": False,
        "flag_repeat": False,
        "flag_stolaf": True,
        "gereqs": tuple(),
        "grade_option": GradeOption.Grade,
        "institution_short": "STOLAF",
        "level": int(number) // 100 * 100,
        "name": s,
        "number": s.split(' ')[1],
        "section": "",
        "sub_type": SubType.Normal,
        "subject": s.split(' ')[0],
        "term": "1",
        "transcript_code": "",
        "year": "2000",
        **kwargs,
        "grade_code": grade_code,
        "grade_points": grade_points,
    }, overrides=[], credits_overrides={})
