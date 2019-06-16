from __future__ import annotations
import dataclasses
from enum import Enum
from typing import List, Optional, Tuple
import decimal
import logging

from .lib import grade_from_str, expand_subjects
from .clause import Clause, SingleClause, AndClause, OrClause


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
    number: int
    section: Optional[str]

    transcript_code: str
    clbid: str
    gereqs: Tuple[str, ...]
    term: Term

    is_lab: bool
    is_flac: bool
    is_ace: bool

    name: str
    grade: decimal.Decimal

    gradeopt: str
    level: int
    attributes: Tuple[str, ...]

    status: CourseStatus

    identity: str
    shorthand: str

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
        clbid,
        gereqs,
        term,
        lab,
        is_repeat,
        incomplete,
        semester,
        year,
    ) -> Optional[CourseInstance]:
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

        is_lab = lab
        is_flac = False
        is_ace = False

        grade = grade_from_str(grade)

        credits = decimal.Decimal(credits).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_DOWN
        )

        subject = subjects if subjects is not None else tuple([course.split(" ")[0]])
        subject = tuple(expand_subjects(subject))
        # we want to keep the original shorthand course identity for matching purposes

        number = number if number is not None else course.split(" ")[1]
        number = int(number)

        section = section if section != "" else None

        level = number // 100 * 100

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
            identity=course_identity,
            shorthand=course_identity_short,
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
        return f"!!course {self.course()}"

    def apply_clause(self, clause: Clause) -> bool:
        if isinstance(clause, AndClause):
            return all(self.apply_clause(subclause) for subclause in clause)
        elif isinstance(clause, OrClause):
            return any(self.apply_clause(subclause) for subclause in clause)
        elif isinstance(clause, SingleClause):
            if clause.key in self.__dict__:
                logging.debug(f'single-clause, key "{clause.key}" exists')
                return clause.compare(self.__dict__[clause.key])
            logging.debug(
                f'single-clause, key "{clause.key}" not found in {list(self.__dict__.keys())}'
            )
            return False

        raise TypeError(f"expected a clause; found {type(clause)}")
