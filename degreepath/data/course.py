from typing import Optional, Tuple, List, Dict, Any, Iterator, Iterable
import dataclasses
import decimal
import logging

from .clausable import Clausable
from .course_enums import GradeCode, GradeOption, SubType
from ..clause import Clause, SingleClause, AndClause, OrClause
from ..lib import str_to_grade_points

logger = logging.getLogger(__name__)
Decimal = decimal.Decimal


@dataclasses.dataclass(frozen=True, order=True)
class CourseInstance(Clausable):
    clbid: str
    attributes: Tuple[str, ...]
    credits: decimal.Decimal
    crsid: str
    gereqs: Tuple[str, ...]
    grade_code: GradeCode
    grade_option: GradeOption
    grade_points: decimal.Decimal
    grade_points_gpa: decimal.Decimal
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
    subject: Tuple[str, ...]
    term: str
    year: int

    _identity: str
    _shorthand: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attributes": list(self.attributes),
            "clbid": self.clbid,
            "credits": str(self.credits),
            "crsid": self.crsid,
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
            "subject": list(self.subject),
            "sub_type": self.sub_type.value,
            "term": self.term,
            "type": "course",
        }

    def attach_attrs(self, attributes: Iterable['str'] = tuple()) -> 'CourseInstance':
        if not attributes:
            attributes = tuple()

        return dataclasses.replace(self, attributes=tuple(attributes))

    def course(self) -> str:
        return self._identity

    def course_shorthand(self) -> str:
        return self._shorthand

    def course_with_term(self) -> str:
        return f"{self._shorthand}{self.section or ''} {self.year}-{self.term}"

    def __str__(self) -> str:
        return self._shorthand

    def __repr__(self) -> str:
        return f'Course("{self._shorthand}")'

    def apply_clause(self, clause: Clause) -> bool:
        if isinstance(clause, AndClause):
            logger.debug("clause/and/compare %s", clause)
            return all(self.apply_clause(subclause) for subclause in clause.children)

        elif isinstance(clause, OrClause):
            logger.debug("clause/or/compare %s", clause)
            return any(self.apply_clause(subclause) for subclause in clause.children)

        elif isinstance(clause, SingleClause):
            return self.apply_single_clause(clause)

        raise TypeError(f"courseinstance: expected a clause; found {type(clause)}")

    def apply_single_clause(self, clause: SingleClause) -> bool:  # noqa: C901
        logger.debug("clause/compare/key=%s", clause.key)

        if clause.key == 'attributes':
            return clause.compare(self.attributes)

        if clause.key == 'gereqs':
            return clause.compare(self.gereqs)

        if clause.key == 'number':
            return clause.compare(self.number)

        if clause.key == 'course':
            return clause.compare(self._identity) or clause.compare(self._shorthand)

        if clause.key == 'subject':
            return clause.compare(self.subject)

        if clause.key == 'grade':
            return clause.compare(self.grade_points)

        if clause.key == 'credits':
            return clause.compare(self.credits)

        if clause.key == 'level':
            return clause.compare(self.level)

        if clause.key == 'semester':
            return clause.compare(self.term)

        if clause.key == 's/u':
            return clause.compare(self.grade_option is GradeOption.SU)

        if clause.key == 'p/n':
            return clause.compare(self.grade_option is GradeOption.PN)

        if clause.key == 'type':
            return clause.compare(self.sub_type.name)

        if clause.key == 'lab':
            return clause.compare(self.is_lab)

        if clause.key == 'grade_option':
            return clause.compare(self.grade_option)

        if clause.key == 'is_stolaf':
            return clause.compare(self.is_stolaf)

        if clause.key == 'year':
            return clause.compare(self.year)

        if clause.key == 'clbid':
            return clause.compare(self.clbid)

        if clause.key == 'crsid':
            return clause.compare(self.crsid)

        raise TypeError(f'{clause.key} is not a known clause key')


def load_course(data: Dict[str, Any]) -> CourseInstance:  # noqa: C901
    attributes = data.get('attributes', tuple())
    clbid = data['clbid']
    course = data['course']
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
    name = data['name']
    number = data['number']
    section = data['section']
    sub_type = data['sub_type']
    subjects = data['subjects']
    term = data['term']
    year = data['year']

    clbid = clbid
    term = int(term)
    credits = decimal.Decimal(credits)
    section = section or None

    grade_code = GradeCode(grade_code)
    grade_points = decimal.Decimal(grade_points)
    grade_option = GradeOption(grade_option)
    sub_type = SubType(sub_type)

    grade_points_gpa = grade_points * credits

    # we want to keep the original shorthand course identity for matching purposes
    verbatim_subject_field = subjects
    subject = subjects if subjects is not None else tuple([course.split(" ")[0]])
    subject = tuple(expand_subjects(subject))

    try:
        level = int(number) // 100 * 100
        level = level if flag_stolaf else 0
    except Exception:
        level = 0

    attributes = tuple(attributes) if attributes else tuple()
    gereqs = tuple(gereqs) if gereqs else tuple()

    if sub_type is SubType.Lab:
        course_identity = f"{'/'.join(subject)} {number}.L"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.L"
    elif sub_type is SubType.Flac:
        course_identity = f"{'/'.join(subject)} {number}.F"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.F"
    elif sub_type is SubType.Discussion:
        course_identity = f"{'/'.join(subject)} {number}.D"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.D"
    else:
        course_identity = f"{'/'.join(subject)} {number}"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}"

    return CourseInstance(
        attributes=attributes,
        clbid=clbid,
        credits=credits,
        crsid=crsid,
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
        year=year,
        _identity=course_identity,
        _shorthand=course_identity_short,
    )


def course_from_str(s: str, **kwargs: Any) -> CourseInstance:
    return load_course({
        "attributes": tuple(),
        "clbid": f"<clbid={str(hash(s))} term={str(kwargs.get('term', 'na'))}>",
        "course": s,
        "credits": '1.00',
        "crsid": f"<crsid={str(hash(s))}>",
        "flag_gpa": True,
        "flag_in_progress": False,
        "flag_incomplete": False,
        "flag_repeat": False,
        "flag_stolaf": True,
        "gereqs": tuple(),
        "grade_code": "B",
        "grade_option": GradeOption.Grade,
        "grade_points": str_to_grade_points("B"),
        "name": s,
        "number": s.split(' ')[1],
        "section": "",
        "sub_type": SubType.Normal,
        "subjects": tuple([s.split(' ')[0]]),
        "term": "1",
        "year": 2000,
        **kwargs,
    })


def expand_subjects(subjects: List[str]) -> Iterator[str]:
    shorthands = {
        "AS": "ASIAN",
        "BI": "BIO",
        "CH": "CHEM",
        "ES": "ENVST",
        "PS": "PSCI",
        "RE": "REL",
    }

    for subject in subjects:
        for code in subject.split("/"):
            yield shorthands.get(code, code)
