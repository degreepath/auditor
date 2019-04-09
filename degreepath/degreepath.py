from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Union, List, Optional, Any, Sequence, Iterator
import re
import itertools
import logging
import decimal
import copy


@dataclass(frozen=True)
class ActionRule:
    assertion: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> ActionRule:
        return ActionRule(assertion=data["assert"])

    def validate(self, *, ctx: RequirementContext):
        ...
        # TODO: check for input items here

    def solutions(self, *, ctx: RequirementContext, path: List):
        logging.debug(f"{path} ActionRule#solutions")
        yield ActionSolution(result=None)


@dataclass(frozen=True)
class ActionSolution:
    result: Optional[bool]


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

        # TODO: greedy mode?

        for combo in itertools.combinations(self.of, self.count):
            did_iter = True

            with_solutions = [
                rule.solutions(ctx=ctx, path=[*path, f"$of[{i}]"])
                for i, rule in enumerate(combo)
            ]

            for i, ruleset in enumerate(itertools.product(*with_solutions)):
                msg = f"{[*path, f'$of/product#{i}']}\n\t{ruleset}"
                yield CountSolution(items=list(ruleset), rule=self)

        if not did_iter:
            # be sure that we always yield something
            yield CountSolution(items=[], rule=self)


@dataclass(frozen=True)
class CountSolution:
    items: List[Any]
    rule: CountRule

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "type": "count",
            "of": [item.to_dict() for item in self.items],
        }

    def audit(self):
        ...


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
        logging.debug(f'{path}\n\treference to course "{self.course}"')

        yield CourseSolution(course=self.course, rule=self)


@dataclass(frozen=True)
class CourseSolution:
    course: str
    rule: CourseRule

    def to_dict(self):
        return {**self.rule.to_dict(), "type": "course", "course": self.course}

    def audit(self):
        path = [*path, f"$c->{self.course}"]
        if not ctx.has_course(self.course):
            logging.debug(
                f'{path}\n\tcourse "{self.course}" does not exist in the transcript'
            )
            return Solution.fail(self)

        claim = ctx.make_claim(
            course=self.course, key=path, value={"course": self.course}
        )

        if claim.failed():
            logging.debug(
                f'{path}\n\tcourse "{self.course}" exists, but has already been claimed by {claim.conflict.path}'
            )
            return Solution.fail(self)

        logging.debug(
            f'{path}\n\tcourse "{self.course}" exists, and has not been claimed'
        )
        claim.commit()


@dataclass(frozen=True)
class AndClause:
    children: Sequence[Clause]

    def to_dict(self):
        return {"type": "and-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: List[Dict]) -> Clause:
        clauses = []
        for clause in data:
            clauses.append(SingleClause.load(clause))
        return AndClause(children=clauses)

    def __iter__(self):
        yield from self.children


@dataclass(frozen=True)
class OrClause:
    children: Sequence[Clause]

    def to_dict(self):
        return {"type": "or-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: Dict) -> Clause:
        clauses = []
        for clause in data:
            clauses.append(SingleClause.load(clause))
        return OrClause(children=clauses)

    def __iter__(self):
        yield from self.children


@dataclass(frozen=True)
class SingleClause:
    key: str
    expected: Any
    operator: Operator

    def to_dict(self):
        return {
            "type": "single-clause",
            "expected": self.expected,
            "operator": self.operator.name,
        }

    @staticmethod
    def load(data: Dict) -> Clause:
        if "$and" in data:
            return AndClause.load(data["$and"])
        elif "$or" in data:
            return OrClause.load(data["$or"])

        clauses = []
        for key, value in data.items():
            assert len(value.keys()) == 1
            op = list(value.keys())[0]

            operator = Operator(op)
            expected_value = value[op]

            clause = SingleClause(key=key, expected=expected_value, operator=operator)

            clauses.append(clause)

        return AndClause(children=clauses)

    def compare(self, to_value: Any) -> bool:
        logging.debug(f"Clause.compare {self}, to: {to_value}")

        if isinstance(to_value, list):
            logging.debug(f"Entering recursive comparison as to_value was a list")
            return any(self.compare(v) for v in to_value)

        if self.operator == Operator.LessThan:
            return self.expected < to_value
        elif self.operator == Operator.LessThanOrEqualTo:
            return self.expected <= to_value
        elif self.operator == Operator.EqualTo:
            return self.expected == to_value
        elif self.operator == Operator.NotEqualTo:
            return self.expected != to_value
        elif self.operator == Operator.GreaterThanOrEqualTo:
            return self.expected >= to_value
        elif self.operator == Operator.GreaterThan:
            return self.expected > to_value

        raise TypeError(f"unknown comparison function {self.operator}")


Clause = Union[AndClause, OrClause, SingleClause]


@dataclass(frozen=True)
class Limit:
    at_most: int
    where: Clause

    def to_dict(self):
        return {"type": "limit", "at_most": self.at_most, "where": self.where.to_dict()}

    @staticmethod
    def load(data: Dict) -> Limit:
        return Limit(at_most=data["at_most"], where=SingleClause.load(data["where"]))


class Operator(Enum):
    LessThan = "$lt"
    LessThanOrEqualTo = "$lte"
    GreaterThan = "$gt"
    GreaterThanOrEqualTo = "$gte"
    EqualTo = "$eq"
    NotEqualTo = "$neq"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class FromAssertion:
    command: str
    source: str
    operator: Operator
    compare_to: Union[str, int, float]

    def to_dict(self):
        return {
            "type": "from-assertion",
            "command": self.command,
            "source": self.source,
            "operator": self.operator.name,
            "compare_to": self.compare_to,
        }

    @staticmethod
    def load(data: Dict) -> FromAssertion:
        keys = list(data.keys())

        assert (len(keys)) == 1

        rex = re.compile(r"(count|sum|minimum|maximum|stored)\((.*)\)")

        k = keys[0]

        m = rex.match(k)
        if not m:
            raise KeyError(f'expected "{k}" to match {rex}')

        val = data[k]

        assert len(val.keys()) == 1

        op = list(val.keys())[0]

        groups = m.groups()

        command = groups[0]
        source = groups[1]
        operator = Operator(op)
        compare_to = val[op]

        return FromAssertion(
            command=command, source=source, operator=operator, compare_to=compare_to
        )

    def validate(self, *, ctx: RequirementContext):
        assert self.command in [
            "count",
            "sum",
            "minimum",
            "maximum",
            "stored",
        ], f"{self.command}"

        if self.command == "count":
            assert self.source in [
                "courses",
                "areas",
                "performances",
                "terms",
                "semesters",
            ]
        elif self.command == "sum":
            assert self.source in ["grades", "credits"]
        elif self.command == "minimum" or self.command == "maximum":
            assert self.source in ["terms", "semesters", "grades", "credits"]
        elif self.command == "stored":
            # TODO: assert that the stored lookup exists
            pass

    def range(self, *, items: List):
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(
                f"compare_to must be numeric to be used in range(); was {repr(compare_to)} ({type(compare_to)}"
            )

        if self.operator == Operator.LessThanOrEqualTo:
            hi = compare_to
            lo = len(items)

        elif self.operator == Operator.LessThan:
            hi = compare_to - 1
            lo = len(items)

        elif self.operator == Operator.GreaterThan:
            hi = len(items)
            lo = compare_to + 1

        elif self.operator == Operator.GreaterThanOrEqualTo:
            hi = len(items)
            lo = compare_to

        elif self.operator == Operator.EqualTo:
            hi = compare_to + 1
            lo = compare_to

        if hi <= lo:
            logging.info(f"expected hi={hi} > lo={lo}")

        return range(lo, hi)


@dataclass(frozen=True)
class FromInput:
    mode: str
    itemtype: str
    requirements: List[str]
    saves: List[str]

    def to_dict(self):
        return {
            "type": "from-input",
            "mode": self.mode,
            "itemtype": self.itemtype,
            "requirements": self.requirements,
            "saves": self.saves,
        }

    @staticmethod
    def load(data: Dict) -> FromInput:
        saves: List[str] = []
        requirements: List[str] = []

        if "student" in data:
            mode = "student"
            itemtype = data["student"]
        elif "saves" in data:
            mode = "saves"
            saves = data["saves"]
            itemtype = None
        elif "save" in data:
            mode = "saves"
            saves = [data["save"]]
            itemtype = None
        elif "requirements" in data:
            mode = "requirements"
            requirements = data["requirements"]
            itemtype = None
        elif "requirement" in data:
            mode = "requirements"
            requirements = [data["requirement"]]
            itemtype = None
        else:
            raise KeyError(
                f"expected student, saves, or requirements; got {list(data.keys())}"
            )

        return FromInput(
            mode=mode, itemtype=itemtype, requirements=requirements, saves=saves
        )

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.mode, str)

        saves = ctx.save_rules
        requirements = ctx.requirements

        dbg = f"(when validating self={repr(self)}, saves={repr(saves)}, reqs={repr(requirements)})"

        if self.mode == "requirements":
            # TODO: assert that the result type of all mentioned requirements is the same
            if not self.requirements or not requirements:
                raise ValueError(
                    "expected self.requirements and args.requirements to be lists"
                )
            for name in self.requirements:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert (
                    name in ctx.requirements
                ), f"expected to find '{name}' once, but could not find it {dbg}"

        elif self.mode == "saves":
            # TODO: assert that the result type of all mentioned saves is the same
            if not self.saves or not saves:
                raise ValueError("expected self.saves and args.saves to be lists")
            for name in self.saves:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert (
                    name in ctx.save_rules
                ), f"expected to find '{name}' once, but could not find it {dbg}"

        elif self.mode == "student":
            assert self.itemtype in ["courses", "performances", "areas"]

        else:
            raise NameError(f"unknown 'from' type {self.mode}")


@dataclass(frozen=True)
class FromRule:
    source: FromInput
    action: Optional[FromAssertion]
    limit: Optional[Limit]
    where: Optional[Clause]
    store: Optional[str]

    def to_dict(self):
        return {
            "type": "from",
            "source": self.source.to_dict(),
            "action": self.action.to_dict() if self.action else None,
            "where": self.where.to_dict() if self.where else None,
            "store": self.store,
        }

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "from" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> FromRule:
        where = data.get("where", None)
        if where is not None:
            where = SingleClause.load(where)

        limit = data.get("limit", None)
        if limit is not None:
            limit = [Limit.load(l) for l in limit]

        action = None
        if "assert" in data:
            action = FromAssertion.load(data=data["assert"])

        return FromRule(
            source=FromInput.load(data["from"]),
            action=action,
            limit=limit,
            where=where,
            store=data.get("store", None),
        )

    def validate(self, *, ctx: RequirementContext):
        self.source.validate(ctx=ctx)
        if self.action:
            self.action.validate(ctx=ctx)
        if self.store is not None:
            assert self.store in ("courses",)

    def solutions_when_student(self, *, ctx: RequirementContext, path):
        if self.source.itemtype == "courses":
            data = ctx.transcript
        else:
            raise KeyError(f"{self.source.itemtype} not yet implemented")

        yield data

    def solutions_when_saves(self, *, ctx: RequirementContext, path):
        saves = [
            ctx.save_rules[s].solutions(ctx=ctx, path=path) for s in self.source.saves
        ]

        for p in itertools.product(*saves):
            data = [item for save_result in p for item in save_result.stored()]
            yield data

    def solutions_when_reqs(self, *, ctx: RequirementContext, path):
        reqs = [
            ctx.requirements[s].solutions(ctx=ctx, path=path)
            for s in self.source.requirements
        ]

        for p in itertools.product(*reqs):
            data = [item for req_result in p for item in req_result.matched()]
            yield data

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        path = [*path, f".from"]
        logging.debug(f"{path}")

        if self.source.mode == "student":
            iterable = self.solutions_when_student(ctx=ctx, path=path)
        elif self.source.mode == "saves":
            iterable = self.solutions_when_saves(ctx=ctx, path=path)
        elif self.source.mode == "requirements":
            iterable = self.solutions_when_reqs(ctx=ctx, path=path)
        else:
            raise KeyError(f'unknown "from" type "{self.source.mode}"')

        did_iter = False
        for data in iterable:
            if self.where is not None:
                logging.debug(f"fromrule/filter/clause: {self.where}")
                logging.debug(f"fromrule/filter/before: {data}")
                data = [c for c in data if c.apply_clause(self.where)]
                logging.debug(f"fromrule/filter/after: {data}")

            if self.store == "courses":
                logging.debug("storing courses")
                yield FromSolution(output=data, rule=self)
                return
            elif self.store:
                raise Exception("not implemented yet")

            assert self.action is not None

            for n in self.action.range(items=data):
                did_iter = True
                for combo in itertools.combinations(data, n):
                    yield FromSolution(output=combo, rule=self)

        if not did_iter:
            # be sure we always yield something
            logging.info("did not yield anything; yielding empty collection")
            yield FromSolution(output=[], rule=self)


@dataclass(frozen=True)
class SaveRule:
    innards: FromRule
    name: str

    def to_dict(self):
        return {**self.innards.to_dict(), "type": "save", "name": self.name}

    @staticmethod
    def load(name: str, data: Dict) -> SaveRule:
        return SaveRule(innards=FromRule.load(data), name=name)

    def validate(self, *, ctx: RequirementContext):
        assert self.name.strip() != ""

        self.innards.validate(ctx=ctx)

    def solutions(
        self, *, ctx: RequirementContext, path: List[str]
    ) -> Iterator[FromSolution]:
        path = [*path, f'.save["{self.name}"]']
        logging.debug(f"{path} inside a saverule")
        yield from self.innards.solutions(ctx=ctx, path=path)


@dataclass(frozen=True)
class FromSolution:
    output: Sequence[Union[CourseInstance, Term, decimal.Decimal, int]]
    rule: FromRule

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "type": "from",
            "output": [x.to_dict() for x in self.output],
        }

    def stored(self):
        return self.output


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


@dataclass(frozen=True)
class ReferenceRule:
    requirement: str

    def to_dict(self):
        return {"type": "reference", "name": self.requirement}

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "requirement" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> ReferenceRule:
        return ReferenceRule(requirement=data["requirement"])

    def validate(self, *, ctx: RequirementContext):
        if self.requirement not in ctx.requirements:
            reqs = ", ".join(ctx.requirements.keys())
            raise AssertionError(
                f"expected a requirement named '{self.requirement}', but did not find one [options: {reqs}]"
            )

        ctx.requirements[self.requirement].validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f'{path}\n\treference to requirement "{self.requirement}"')

        requirement = ctx.requirements[self.requirement]

        logging.debug(f'{path}\n\tfound requirement "{self.requirement}"')

        yield from requirement.solutions(
            ctx=ctx, path=[*path, f"$ref->{self.requirement}"]
        )


Rule = Union[CourseRule, CountRule, FromRule, ActionRule, ReferenceRule]


def load_rule(data: Dict) -> Rule:
    if CourseRule.can_load(data):
        return CourseRule.load(data)
    elif FromRule.can_load(data):
        return FromRule.load(data)
    elif CountRule.can_load(data):
        return CountRule.load(data)
    elif ReferenceRule.can_load(data):
        return ReferenceRule.load(data)
    elif ActionRule.can_load(data):
        return ActionRule.load(data)

    raise ValueError(
        f"expected Course, Given, Count, Both, Either, or Do; found none of those ({data})"
    )


@dataclass(frozen=False)
class RequirementContext:
    transcript: List[CourseInstance] = field(default_factory=list)
    save_rules: Dict[str, SaveRule] = field(default_factory=dict)
    requirements: Dict[str, Requirement] = field(default_factory=dict)
    requirement_results: Dict[str, RequirementSolution] = field(default_factory=dict)

    def record_save(self, save_stuff):
        ...

    def record_requirement(self, req_stuff):
        ...


class CourseStatus(Enum):
    Ok = 0
    InProgress = 1
    DidNotComplete = 2
    Repeated = 3


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
        return f"{self.subject.join('/')} {self.number}"

    def __str__(self):
        return f"{self.course()}"

    def apply_clause(self, clause: Clause) -> bool:
        if isinstance(clause, AndClause):
            logging.debug(f"and-clause")
            return all(self.apply_clause(subclause) for subclause in clause)
        elif isinstance(clause, OrClause):
            logging.debug(f"or-clause")
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


@dataclass(frozen=True)
class Requirement:
    name: str
    saves: Dict[str, SaveRule]
    requirements: Dict[str, Requirement]
    message: Optional[str] = None
    result: Optional[Rule] = None
    audited_by: Optional[str] = None
    contract: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "saves": {name: s.to_dict() for name, s in self.saves.items()},
            "requirements": {
                name: r.to_dict() for name, r in self.requirements.items()
            },
            "message": self.message,
            "result": self.result.to_dict(),
            "audited_by": self.audited_by,
            "contract": self.contract,
        }

    @staticmethod
    def load(name: str, data: Dict[str, Any]) -> Requirement:
        children = {
            name: Requirement.load(name, r)
            for name, r in data.get("requirements", {}).items()
        }

        result = data.get("result", None)
        if result is not None:
            result = load_rule(result)

        saves = {
            name: SaveRule.load(name, s) for name, s in data.get("saves", {}).items()
        }

        audited_by = None
        if data.get("department_audited", False):
            audited_by = "department"
        elif data.get("registrar_audited", False):
            audited_by = "registrar"

        return Requirement(
            name=name,
            message=data.get("message", None),
            requirements=children,
            result=result,
            saves=saves,
            contract=data.get("contract", False),
            audited_by=audited_by,
        )

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        if self.message is not None:
            assert isinstance(self.message, str)
            assert self.message.strip() != ""

        children = self.requirements

        validated_saves: Dict[str, SaveRule] = {}
        for save in self.saves.values():
            new_ctx = RequirementContext(
                transcript=ctx.transcript,
                save_rules={name: s for name, s in validated_saves.items()},
                requirements=children,
            )
            save.validate(ctx=new_ctx)
            validated_saves[save.name] = save

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            save_rules={name: s for name, s in self.saves.items() or {}},
            requirements=children,
        )

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        ctx = copy.deepcopy(ctx)

        path = [*path, f"$req->{self.name}"]

        header = f'{path}\n\trequirement "{self.name}"'

        logging.debug(f"{header} has not been evaluated")
        # TODO: implement caching

        if not self.message:
            logging.debug(f"{header} has no message")

        if not self.audited_by:
            logging.debug(f"{header} is not audited")

        if not self.result:
            logging.debug(f"{header} does not have a result")
            return
        else:
            logging.debug(f"{header} has a result")

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            save_rules={s.name: s for s in self.saves.values()},
            requirements={r.name: r for r in self.requirements.values()},
        )

        path = [*path, ".result"]
        for sol in self.result.solutions(ctx=new_ctx, path=path):
            yield RequirementSolution(solution=sol, requirement=self)


@dataclass(frozen=True)
class RequirementSolution:
    solution: Any
    requirement: Requirement

    def matched(self):
        return self.solution

    def to_dict(self):
        limited_req = {
            k: v
            for k, v in self.requirement.to_dict().items()
            if k not in ["requirements"]
        }
        return {**limited_req, "type": "requirement", "result": self.solution.to_dict()}


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""

    name: str
    kind: str
    degree: Optional[str]
    catalog: str

    result: Rule
    requirements: Dict[str, Requirement]

    attributes: Dict

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.kind,
            "degree": self.degree,
            "catalog": self.catalog,
            "result": self.result.to_dict(),
            "requirements": {
                name: r.to_dict() for name, r in self.requirements.items()
            },
            "attributes": self.attributes,
        }

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        requirements = {
            name: Requirement.load(name, r) for name, r in data.get("requirements", {}).items()
        }
        result = load_rule(data["result"])

        return AreaOfStudy(
            name=data["name"],
            catalog=data["catalog"],
            degree=data.get("degree", None),
            kind=data["type"],
            requirements=requirements,
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
            transcript=[], save_rules={}, requirements=self.requirements
        )

        self.result.validate(ctx=ctx)

    def solutions(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logging.debug(f"{path}\n\tevaluating area.result")

        ctx = RequirementContext(
            transcript=transcript,
            save_rules={},
            requirements={name: r for name, r in self.requirements.items()},
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
            save_rules={},
            requirements={name: r for name, r in self.area.requirements.items()},
        )

        new_path = [*path, ".result"]
