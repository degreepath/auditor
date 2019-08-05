from typing import Optional, Tuple, List, Dict
import dataclasses
import decimal
import logging

from ..clause import Clause, SingleClause, AndClause, OrClause
from .course_enums import CourseStatus, SubType, TranscriptCode, Grade, GradeType
from ..lib import grade_to_grade_points

logger = logging.getLogger(__name__)
Decimal = decimal.Decimal


@dataclasses.dataclass(frozen=True, order=True)
class CourseInstance:
    attributes: Tuple[str, ...]
    clbid: str
    credits: decimal.Decimal
    crsid: str
    gereqs: Tuple[str, ...]
    grade: Grade
    grade_points: Decimal
    grade_type: GradeType
    institution: str
    in_gpa: bool
    level: int
    name: str
    number: str
    section: Optional[str]
    status: CourseStatus
    subject: Tuple[str, ...]
    subtype: SubType
    term: int
    transcript_code: TranscriptCode
    _identity: str
    _shorthand: str

    def to_dict(self):
        return {
            "attributes": list(self.attributes),
            "clbid": self.clbid,
            "credits": str(self.credits),
            "crsid": self.crsid,
            "gereqs": list(self.gereqs),
            "grade": self.grade.value,
            "grade_points": str(self.grade_points),
            "grade_type": self.grade_type.value,
            "institution": self.institution,
            "level": self.level,
            "name": self.name,
            "number": self.number,
            "section": self.section,
            "status": self.status.value,
            "subject": list(self.subject),
            "subtype": self.subtype.value,
            "term": self.term,
            "transcript_code": self.transcript_code.value,
            "type": "course",
        }

    def attach_attrs(self, attributes=None):
        if attributes is None:
            attributes = tuple()

        return dataclasses.replace(self, attributes=tuple(attributes))

    def course(self):
        return self._identity

    def course_shorthand(self):
        return self._shorthand

    def course_with_term(self):
        return f"{self._shorthand}{self.section or ''} {str(self.term)[0:4]}-{str(self.term)[4]}"

    def __str__(self):
        return self._shorthand

    def __repr__(self):
        return f'Course("{self._shorthand}")'

    def year(self):
        return int(str(self.term)[0:4])

    def semester(self):
        return int(str(self.term)[4])

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

    def apply_single_clause(self, clause: SingleClause):
        logger.debug("clause/compare/key=%s", clause.key)

        if clause.key == 'clbid':
            return clause.compare(self.clbid)
        elif clause.key == 'crsid':
            return clause.compare(self.crsid)
        elif clause.key == 'grade':
            return clause.compare(self.grade_points)
        elif clause.key == 'level':
            return clause.compare(self.level)
        elif clause.key == 'attributes':
            return clause.compare(self.attributes)
        elif clause.key == 'course':
            return clause.compare(self._identity) or clause.compare(self._shorthand)
        elif clause.key == 'semester':
            return clause.compare(self.semester())

        # TODO: replace this with explicit key accesses
        if clause.key in self.__dict__:
            return clause.compare(self.__dict__[clause.key])
        else:
            keys = list(self.__dict__.keys())
            logger.debug("clause/compare[%s]: not found in %s", clause.key, keys)
            return False


def load_course(data: Dict) -> Optional[CourseInstance]:  # noqa: C901
    attributes = data.get('attributes', tuple())
    clbid = data['clbid']
    course = data['course']
    credits = data['credits']
    crsid = data['crsid']
    gereqs = data['gereqs']
    grade = data['grade']
    graded = data['graded']
    incomplete = data['incomplete']
    institution = data.get('institution', "St. Olaf College")
    is_repeat = data['is_repeat']
    name = data['name']
    number = data['number']
    section = data['section']
    subjects = data['subjects']
    subtype = data['subtype']
    term = data['term']
    transcript_code = data.get('transcript_code', None) or None

    grade = Grade(grade)
    grade_points = grade_to_grade_points(grade)
    subtype = SubType(subtype)
    grade_type = GradeType(graded)
    transcript_code = TranscriptCode(transcript_code)

    status = CourseStatus.Ok
    if grade is Grade._IP:
        status = CourseStatus.InProgress
    if transcript_code is TranscriptCode.RepeatedLater or is_repeat:
        status = CourseStatus.Repeat
    if incomplete:
        status = CourseStatus.Incomplete

    if transcript_code is TranscriptCode.TakenAtCarleton:
        institution = 'Carleton College'

    clbid = clbid
    term = int(term)
    credits = decimal.Decimal(credits)

    verbatim_subject_field = subjects
    subject = subjects if subjects is not None else tuple([course.split(" ")[0]])
    subject = tuple(expand_subjects(subject))
    # we want to keep the original shorthand course identity for matching purposes

    number = str(number if number is not None else course.split(" ")[1])
    section = section or None

    try:
        level = int(number) // 100 * 100
    except Exception:
        level = 0

    attributes = tuple(attributes) if attributes else tuple()
    gereqs = tuple(gereqs) if gereqs else tuple()

    if subtype is SubType.Lab:
        course_identity = f"{'/'.join(subject)} {number}.L"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.L"
    elif subtype is SubType.FLAC:
        course_identity = f"{'/'.join(subject)} {number}.F"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.F"
    elif subtype is SubType.Discussion:
        course_identity = f"{'/'.join(subject)} {number}.D"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.D"
    else:
        course_identity = f"{'/'.join(subject)} {number}"
        course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}"

    in_gpa = True
    if str(term)[-1] == '9':
        in_gpa = False
    elif institution not in ('St. Olaf College', 'Carleton College'):
        in_gpa = False
    elif grade_type is not GradeType.GR:
        in_gpa = False
    elif grade in (Grade._NG, Grade._W):
        in_gpa = False
    elif status in (CourseStatus.Repeat, CourseStatus.InProgress):
        in_gpa = False

    return CourseInstance(
        attributes=attributes,
        clbid=clbid,
        credits=credits,
        crsid=crsid,
        in_gpa=in_gpa,
        gereqs=gereqs,
        grade=grade,
        grade_type=grade_type,
        grade_points=grade_points,
        institution=institution,
        level=level,
        name=name,
        number=number,
        section=section,
        status=status,
        subject=subject,
        subtype=subtype,
        term=term,
        transcript_code=transcript_code,
        _identity=course_identity,
        _shorthand=course_identity_short,
    )


def course_from_str(s: str, **kwargs):
    return load_course({
        "attributes": tuple(),
        "clbid": f"<clbid={str(hash(s))} term={str(kwargs.get('term', 'na'))}>",
        "course": s,
        "credits": '1.00',
        "crsid": f"<crsid={str(hash(s))}>",
        "gereqs": tuple(),
        "grade": 'B',
        "graded": "Graded",
        "incomplete": False,
        "institution": "St. Olaf College",
        "is_repeat": False,
        "name": s,
        "number": s.split(' ')[1],
        "section": "",
        "subjects": tuple([s.split(' ')[0]]),
        "subtype": "",
        "term": 20001,
        "transcript_code": None,
        **kwargs,
    })


def expand_subjects(subjects: List[str]):
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
