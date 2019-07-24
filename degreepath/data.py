import dataclasses
import enum
from typing import Optional, Tuple, Any
import decimal
import logging

from .lib import grade_from_str, expand_subjects
from .clause import Clause, SingleClause, AndClause, OrClause


class AreaStatus(enum.Enum):
    certified = enum.auto()
    declared = enum.auto()


class AreaKind(enum.Enum):
    major = enum.auto()
    concentration = enum.auto()
    emphasis = enum.auto()


@dataclasses.dataclass(frozen=True)
class AreaPointer:
    code: int
    status: AreaStatus
    kind: AreaKind
    name: str
    degree: str

    def to_dict(self):
        return {
            "type": "area",
            "code": self.code,
            "status": self.status.name,
            "kind": self.kind.name,
            "degree": self.degree,
            "name": self.name,
        }

    @staticmethod
    def from_dict(*, code, status, kind, name, degree) -> Optional[Any]:
        return AreaPointer(
            code=int(code),
            status=AreaStatus[status],
            kind=AreaKind[kind],
            name=name,
            degree=degree,
        )

    def apply_clause(self, clause: Clause) -> bool:
        if isinstance(clause, AndClause):
            logging.debug("clause/and/compare %s", clause)
            return all(self.apply_clause(subclause) for subclause in clause)

        elif isinstance(clause, OrClause):
            logging.debug("clause/or/compare %s", clause)
            return any(self.apply_clause(subclause) for subclause in clause)

        elif isinstance(clause, SingleClause):
            if clause.key == 'code':
                return clause.compare(self.code)
            elif clause.key == 'status':
                return clause.compare(self.status.name)
            elif clause.key == 'kind' or clause.key == 'type':
                return clause.compare(self.kind.name)
            elif clause.key == 'name':
                return clause.compare(self.name)
            elif clause.key == 'degree':
                return clause.compare(self.degree)

            raise TypeError(f"expected to get one of {list(self.__dict__.keys())}; got {clause.key}")

        raise TypeError(f"expected a clause; found {type(clause)}")


@dataclasses.dataclass(frozen=True, order=True)
class Term:
    term: int

    def __post_init__(self):
        if not isinstance(self.term, int):
            raise TypeError(f'expected {self.term} ({type(self.term)}) to be an int')

    def year(self):
        return int(str(self.term)[0:4])

    def semester(self):
        return int(str(self.term)[4])

    def to_dict(self):
        return {"type": "term", "year": self.year(), "semester": self.semester()}


class CourseStatus(enum.Enum):
    Ok = enum.auto()
    InProgress = enum.auto()
    DidNotComplete = enum.auto()
    Repeated = enum.auto()
    NotTaken = enum.auto()


@dataclasses.dataclass(frozen=True)
class CourseInstance:
    credits: decimal.Decimal
    subject: Tuple[str, ...]
    number: str
    section: Optional[str]

    transcript_code: Optional[str]
    clbid: str
    gereqs: Tuple[str, ...]
    term: Term

    is_lab: bool
    is_flac: bool
    is_ace: bool
    is_topic: bool

    name: str
    grade: decimal.Decimal

    gradeopt: str
    level: int
    attributes: Tuple[str, ...]

    status: CourseStatus

    identity: str
    shorthand: str
    institution: str

    crsid: str
    subtype: str

    def to_dict(self):
        return {
            **self.__dict__,
            "credits": str(self.credits),
            "grade": str(self.grade),
            "term": self.term.to_dict(),
            "status": self.status.name,
            "type": "course",
        }

    @staticmethod
    def from_dict(
        *,
        attributes=None,
        clbid,
        course,
        credits,
        crsid,
        gereqs,
        grade,
        graded,
        incomplete,
        institution="St. Olaf College",
        is_repeat,
        name,
        number=None,
        section,
        semester,
        subjects=None,
        subtype,
        term,
        transcript_code=None,
        year,
    ) -> Optional[Any]:
        status = CourseStatus.Ok

        if grade == "IP":
            status = CourseStatus.InProgress

        if transcript_code == "":
            transcript_code = None

        if transcript_code == "R":
            status = CourseStatus.Repeated

        if incomplete:
            status = CourseStatus.DidNotComplete

        if number == "":
            return None

        # TODO: handle did-not-complete courses

        clbid = clbid
        term = Term(int(term))

        gradeopt = graded

        is_lab = subtype == 'L'
        # TODO: export is_flac/is_ace
        is_flac = name.startswith("FLC - ")
        is_ace = False
        # TODO: export the course type
        is_topic = name.startswith("Top: ")

        grade = grade_from_str(grade)
        credits = decimal.Decimal(credits)

        verbatim_subject_field = subjects
        subject = subjects if subjects is not None else tuple([course.split(" ")[0]])
        subject = tuple(expand_subjects(subject))
        # we want to keep the original shorthand course identity for matching purposes

        number = str(number if number is not None else course.split(" ")[1])
        section = section if section != "" else None

        try:
            level = int(number) // 100 * 100
        except Exception:
            level = 0

        attributes = tuple(attributes) if attributes is not None else tuple()
        gereqs = tuple(gereqs) if gereqs is not None else tuple()

        if is_lab:
            course_identity = f"{'/'.join(subject)} {number}.L"
            course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.L"
        elif is_flac:
            course_identity = f"{'/'.join(subject)} {number}.F"
            course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}.F"
        else:
            course_identity = f"{'/'.join(subject)} {number}"
            course_identity_short = f"{'/'.join(verbatim_subject_field)} {number}"

        return CourseInstance(
            attributes=attributes,
            clbid=clbid,
            credits=credits,
            crsid=crsid,
            gereqs=gereqs,
            grade=grade,
            gradeopt=gradeopt,
            identity=course_identity,
            institution=institution,
            is_ace=is_ace,
            is_flac=is_flac,
            is_lab=is_lab,
            is_topic=is_topic,
            level=level,
            name=name,
            number=number,
            section=section,
            shorthand=course_identity_short,
            status=status,
            subject=subject,
            subtype=subtype,
            term=term,
            transcript_code=transcript_code,
        )

    @staticmethod
    def from_s(s: str, **kwargs):
        return CourseInstance.from_dict(**{
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
            "semester": 1,
            "subjects": tuple([s.split(' ')[0]]),
            "subtype": "x",
            "term": 20001,
            "transcript_code": None,
            "year": 2000,
            **kwargs,
        })

    def attach_attrs(self, attributes=None):
        if attributes is None:
            attributes = tuple()

        return dataclasses.replace(self, attributes=tuple(attributes))

    def course(self):
        return self.identity

    def course_shorthand(self):
        return self.shorthand

    def __str__(self):
        return f"CourseInstance( {self.course()} )"

    def apply_clause(self, clause: Clause) -> bool:
        if isinstance(clause, AndClause):
            logging.debug("clause/and/compare %s", clause)
            return all(self.apply_clause(subclause) for subclause in clause)

        elif isinstance(clause, OrClause):
            logging.debug("clause/or/compare %s", clause)
            return any(self.apply_clause(subclause) for subclause in clause)

        elif isinstance(clause, SingleClause):
            if clause.key == 'clbid':
                return clause.compare(self.clbid)
            elif clause.key == 'crsid':
                return clause.compare(self.crsid)

            # TODO: replace this with explicit key accesses
            if clause.key in self.__dict__:
                logging.debug("clause/compare/key=%s", clause.key)
                return clause.compare(self.__dict__[clause.key])
            else:
                keys = list(self.__dict__.keys())
                logging.debug("clause/compare[%s]: not found in %s", clause.key, keys)
                return False

        raise TypeError(f"expected a clause; found {type(clause)}")
