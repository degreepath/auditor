import dataclasses
from enum import Enum
from typing import Optional, Tuple
import decimal
import logging

from .lib import grade_from_str, expand_subjects
from .clause import Clause, SingleClause, AndClause, OrClause, str_clause


@dataclasses.dataclass(frozen=True)
class Term:
    term: int

    def year(self):
        return int(str(self.term)[0:4])

    def semester(self):
        return int(str(self.term)[4])

    def to_dict(self):
        return {"type": "term", "year": self.year(), "semester": self.semester()}


class CourseStatus(Enum):
    Ok = 0
    InProgress = 1
    DidNotComplete = 2
    Repeated = 3
    NotTaken = 4


@dataclasses.dataclass(frozen=True)
class CourseInstance:
    credits: decimal.Decimal
    subject: Tuple[str, ...]
    number: str
    section: Optional[str]

    transcript_code: str
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
        grade,
        transcript_code=None,
        graded,
        credits,
        subjects=None,
        course,
        number=None,
        attributes=None,
        name,
        section,
        gereqs,
        term,
        is_repeat,
        incomplete,
        semester,
        year,
        subtype,
        clbid,
        crsid,
        institution="St. Olaf College",
    ) -> Optional:
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
        term = Term(term)

        gradeopt = graded

        is_lab = subtype == 'L'
        # TODO: export is_flac/is_ace
        is_flac = name.startswith("FLC - ")
        is_ace = False

        # TODO: export the course type
        is_topic = name.startswith("Top: ")

        grade = grade_from_str(grade)

        credits = decimal.Decimal(credits).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_DOWN
        )

        subject = subjects if subjects is not None else tuple([course.split(" ")[0]])
        subject = tuple(expand_subjects(subject))
        # we want to keep the original shorthand course identity for matching purposes

        number = number if number is not None else course.split(" ")[1]
        number = str(number)

        section = section if section != "" else None

        try:
            level = int(number) // 100 * 100
        except Exception:
            level = 0

        attributes = tuple(attributes) if attributes is not None else tuple()
        gereqs = tuple(gereqs) if gereqs is not None else tuple()

        if is_lab:
            course_identity = f"{'/'.join(subject)} {number}.L"
            course_identity_short = f"{'/'.join(subjects)} {number}.L"
        elif is_flac:
            course_identity = f"{'/'.join(subject)} {number}.F"
            course_identity_short = f"{'/'.join(subjects)} {number}.F"
        else:
            course_identity = f"{'/'.join(subject)} {number}"
            course_identity_short = f"{'/'.join(subjects)} {number}"

        return CourseInstance(
            status=status,
            credits=credits,
            subject=subject,
            number=number,
            section=section,
            transcript_code=transcript_code,
            clbid=clbid,
            gereqs=gereqs,
            term=term,
            is_lab=is_lab,
            name=name,
            grade=grade,
            gradeopt=gradeopt,
            level=level,
            attributes=attributes,
            is_flac=is_flac,
            is_ace=is_ace,
            is_topic=is_topic,
            identity=course_identity,
            shorthand=course_identity_short,
            institution=institution,
            subtype=subtype,
            crsid=crsid,
        )

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
            logging.debug(f"clause/and/compare {str_clause(clause)}")
            return all(self.apply_clause(subclause) for subclause in clause)
        elif isinstance(clause, OrClause):
            logging.debug(f"clause/or/compare {str_clause(clause)}")
            return any(self.apply_clause(subclause) for subclause in clause)
        elif isinstance(clause, SingleClause):
            if clause.key in self.__dict__:
                logging.debug(f"clause/compare/key={clause.key}")
                return clause.compare(self.__dict__[clause.key])
            else:
                keys = list(self.__dict__.keys())
                logging.debug(f"clause/compare[{clause.key}]: not found in {keys}")
                return False

        raise TypeError(f"expected a clause; found {type(clause)}")
