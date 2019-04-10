from __future__ import annotations
from dataclasses import dataclass, field, InitVar
from enum import Enum
from typing import Dict, Union, List, Optional, Any, Sequence, Iterator
import re
import itertools
import logging
import decimal
import copy


@dataclass(frozen=True)
class CountRule:
    count: int
    of: List[Rule]

    def to_dict(self):
        return {
            "type": "count",
            "count": self.count,
            "of": [item.to_dict() for item in self.of],
        }

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "count" in data and "of" in data:
            return True
        if "all" in data:
            return True
        if "any" in data:
            return True
        if "both" in data:
            return True
        if "either" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> CountRule:
        if "all" in data:
            of = data["all"]
            count = len(of)
        elif "any" in data:
            of = data["any"]
            count = 1
        elif "both" in data:
            of = data["both"]
            count = 2
            if len(of) != 2:
                raise Exception(f"expected two items in both; found {len(of)} items")
        elif "either" in data:
            of = data["either"]
            count = 1
            if len(of) != 2:
                raise Exception(f"expected two items in both; found {len(of)} items")
        else:
            of = data["of"]
            if data["count"] == "all":
                count = len(of)
            elif data["count"] == "any":
                count = 1
            else:
                count = int(data["count"])

        return CountRule(count=count, of=[load_rule(r) for r in of])

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.count, int), f"{self.count} should be an integer"
        assert self.count >= 0
        assert self.count <= len(self.of)

        for rule in self.of:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List):
        path = [*path, f".of({self.count}/{len(self.of)})"]
        logging.debug(f"{path}\n\tneed {self.count} of {len(self.of)} items")

        did_iter = False

        lo = self.count
        hi = len(self.of) + 1

        assert lo < hi

        # for n in range(lo, hi):
        for combo in itertools.combinations(self.of, lo):
            did_iter = True

            with_solutions = [
                rule.solutions(ctx=ctx, path=[*path, f"$of[{i}]"])
                for i, rule in enumerate(combo)
            ]

            for i, ruleset in enumerate(itertools.product(*with_solutions)):
                msg = f"{[*path, f'$of/product#{i}']}\n\t{ruleset}"
                yield CountSolution(items=list(ruleset), choices=self.of, rule=self)

        if not did_iter:
            # be sure that we always yield something
            yield CountSolution(items=[], choices=self.of, rule=self)


@dataclass(frozen=True)
class CountSolution:
    items: List[Any]
    choices: List[Any]
    rule: CountRule

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "type": "count",
            "of": [item.to_dict() for item in self.items],
        }

    def audit(self, *, ctx) -> Result:
        lo = self.rule.count
        hi = len(self.items) + 1

        assert lo < hi

        best_combo = None
        best_combo_passed_count = None

        for n in range(lo, hi):
            for combo in itertools.combinations(self.items, n):
                results = [r.audit(ctx=ctx) for r in combo]
                passed_count = sum(1 for r in results if r.ok())

                if best_combo is None:
                    best_combo = results
                    best_combo_passed_count = passed_count

                if passed_count > best_combo_passed_count:
                    best_combo = results
                    best_combo_passed_count = passed_count

                if passed_count == len(results):
                    best_combo = results
                    best_combo_passed_count = passed_count
                    break

        assert best_combo

        return CountResult(items=best_combo, choices=self.choices)



@dataclass(frozen=True)
class CountResult:
    items: List
    choices: List

    def to_dict(self):
        return {'ok': self.ok(), 'rank': self.rank(), 'items': [x.to_dict() for x in self.items], 'choices': [x.to_dict() for x in self.choices]}

    def ok(self) -> bool:
        return all(r.ok() for r in self.items)

    def rank(self):
        return sum(r.rank() for r in self.items)


@dataclass(frozen=True)
class CourseResult:
    course: str
    status: CourseStatus
    success: bool

    def to_dict(self):
        return {'ok': self.ok(), 'rank': self.rank(), 'course': self.course, 'status': self.status}

    def ok(self) -> bool:
        return self.success

    def rank(self):
        return 1 if self.ok() else 0


Result = Union[CountResult, CourseResult]



@dataclass(frozen=True)
class CourseRule:
    course: str

    def to_dict(self):
        return {"type": "course", "course": self.course}

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> CourseRule:
        return CourseRule(course=data["course"])

    def validate(self, *, ctx: RequirementContext):
        method_a = re.match(r"[A-Z]{3,5} [0-9]{3}", self.course)
        method_b = re.match(r"[A-Z]{2}/[A-Z]{2} [0-9]{3}", self.course)
        method_c = re.match(r"(IS|ID) [0-9]{3}", self.course)
        assert (
            method_a or method_b or method_c
        ) is not None, f"{self.course}, {method_a}, {method_b}, {method_c}"

    def solutions(self, *, ctx: RequirementContext, path: List):
        logging.debug(f'{path} reference to course "{self.course}"')

        yield CourseSolution(course=self.course, rule=self)


@dataclass(frozen=True)
class CourseSolution:
    course: str
    rule: CourseRule

    def to_dict(self):
        return {**self.rule.to_dict(), "type": "course", "course": self.course}

    def audit(self, *, ctx):
        found_course = ctx.find_course(self.course)

        if found_course:
            return CourseResult(course=self.course, status=found_course.status, success=True)

        logging.debug(
            f'course "{self.course}" does not exist in the transcript'
        )
        return CourseResult(course=self.course, status=CourseStatus.NotTaken, success=False)


@dataclass(frozen=True)
class Term:
    term: int

    def year(self):
        return int(str(self.term)[0:4])

    def semester(self):
        return int(str(self.term)[5])

    def to_dict(self):
        return {"type": "term"}


def grade_from_str(s: str) -> decimal.Decimal:
    grades = {
        'A+': '4.30',
        'A': '4.00',
        'A-': '3.70',
        'B+': '3.30',
        'B': '3.00',
        'B-': '2.70',
        'C+': '2.30',
        'C': '2.00',
        'C-': '1.70',
        'D+': '1.30',
        'D': '1.00',
        'D-': '0.70',
        'F': '0.00',
    }

    return decimal.Decimal(grades.get(s, '0.00'))


def expand_subjects(subjects: List[str]):
    shorthands = {
        'PS': 'PSCI',
        'ES': 'ENVST',
        "AS": "ASIAN",
        "RE": "REL",
        'BI': 'BIO',
        'CH': "CHEM",
    }

    for subject in subjects:
        for code in subject.split('/'):
            yield shorthands.get(code, code)


Rule = Union[CourseRule, CountRule]


def load_rule(data: Dict) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data)
    elif CountRule.can_load(data):
        return CountRule.load(data)

    raise ValueError(
        f"expected Course, Given, Count, Both, Either, or Do; found none of those ({data})"
    )


@dataclass(frozen=False)
class RequirementContext:
    transcript: List[CourseInstance] = field(default_factory=list)

    def find_course(self, c: str) -> Optional[CourseInstance]:
        try:
            return next(
                course
                for course in self.transcript
                if course.status != CourseStatus.DidNotComplete and course.course() == c
            )
        except StopIteration:
            return None


class CourseStatus(Enum):
    Ok = 0
    InProgress = 1
    DidNotComplete = 2
    Repeated = 3
    NotTaken = 4


@dataclass(frozen=True)
class CourseInstance:
    credits: decimal.Decimal
    subject: List[str]
    number: int
    section: Optional[str]

    transcript_code: str
    clbid: int
    gereqs: List[str]
    term: Term

    is_lab: bool
    is_flac: bool
    is_ace: bool

    name: str
    grade: decimal.Decimal

    gradeopt: str
    level: int
    attributes: List[str]

    status: CourseStatus

    def to_dict(self):
        return {**self.__dict__, "type": "course"}

    @staticmethod
    def from_dict(*, grade, transcript_code=None, graded, credits, subjects=None, course, number=None, attributes=None, name, section, clbid, gereqs, term, lab, is_repeat, incomplete, semester, year) -> CourseInstance:
        status = CourseStatus.Ok

        if grade == 'IP':
            status = CourseStatus.InProgress

        if transcript_code == '':
            transcript_code = None

        if transcript_code == 'R':
            status = CourseStatus.Repeated

        if incomplete:
            status = CourseStatus.DidNotComplete

        # TODO: handle did-not-complete courses

        clbid = int(clbid)
        term = Term(term)

        gradeopt = graded

        is_lab = lab
        is_flac = False
        is_ace = False

        grade = grade_from_str(grade)

        credits = decimal.Decimal(credits).quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_DOWN)

        subject = subjects if subjects is not None else [course.split(" ")[0]]
        subject = list(expand_subjects(subject))
        # we want to keep the original shorthand course identity for matching purposes

        number = number if number is not None else course.split(" ")[1]
        number = int(number)

        section = section if section != '' else None

        level = number // 100 * 100

        attributes = attributes if attributes is not None else []

        return CourseInstance(
            status=status, credits=credits, subject=subject, number=number,
            section=section, transcript_code=transcript_code, clbid=clbid,
            gereqs=gereqs, term=term, is_lab=is_lab, name=name, grade=grade,
            gradeopt=gradeopt, level=level, attributes=attributes,
            is_flac=is_flac, is_ace=is_ace,
        )

    def attach_attrs(self, attributes=None):
        if attributes is None:
            attributes = []

        return dataclass.replace(self, attributes=attributes)

    def course(self):
        return f"{'/'.join(self.subject)} {self.number}"

    def __str__(self):
        return f"{self.course()}"


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""

    name: str
    kind: str
    degree: Optional[str]
    catalog: str

    result: Rule

    attributes: Dict

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.kind,
            "degree": self.degree,
            "catalog": self.catalog,
            "result": self.result.to_dict(),
            "attributes": self.attributes,
        }

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        result = load_rule(data["result"])

        return AreaOfStudy(
            name=data["name"],
            catalog=data["catalog"],
            degree=data.get("degree", None),
            kind=data["type"],
            result=result,
            attributes=data.get("attributes", {}),
        )

    def validate(self):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        assert isinstance(self.kind, str)
        assert self.kind in ["degree", "major", "concentration"]

        assert isinstance(self.catalog, str)
        assert self.catalog.strip() != ""

        if self.kind != "degree":
            assert isinstance(self.degree, str)
            assert self.degree.strip() != ""
            assert self.degree in ["Bachelor of Arts", "Bachelor of Music"]

        ctx = RequirementContext(
            transcript=[],
        )

        self.result.validate(ctx=ctx)

    def solutions(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logging.debug(f"{path}\n\tevaluating area.result")

        ctx = RequirementContext(
            transcript=transcript,
        )

        new_path = [*path, ".result"]
        for sol in self.result.solutions(ctx=ctx, path=new_path):
            yield AreaSolution(solution=sol, area=self)

        logging.debug(f"{path}\n\tall solutions generated")


@dataclass(frozen=True)
class AreaSolution:
    solution: Any
    area: AreaOfStudy

    def to_dict(self):
        return {
            **self.area.to_dict(),
            "type": "area",
            "result": self.solution.to_dict(),
        }

    def audit(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logging.debug(f"{path}\n\tauditing area.result")

        ctx = RequirementContext(
            transcript=transcript,
        )

        new_path = [*path, ".result"]

        return self.solution.audit(ctx=ctx)
