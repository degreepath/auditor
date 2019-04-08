from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Union, List, Optional, TextIO, Any, Sequence, Iterator
import re
import json
import jsonpickle
import itertools
import logging
import yaml
import shlex
import sys


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

    def validate(self):
        ...
        # TODO: check for input items here

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f"{path} ActionRule#solutions")
        yield ActionSolution(result=None)


@dataclass(frozen=True)
class ActionSolution:
    result: Optional[bool]


@dataclass(frozen=True)
class CountRule:
    count: int
    of: List[Rule]

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

        return CountRule(count=count, of=[Rule.load(r) for r in of])

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.count, int), f"{self.count} should be an integer"
        assert self.count >= 0
        assert self.count <= len(self.of)

        for rule in self.of:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        path = [*path, f".of({self.count}/{len(self.of)})"]
        logging.debug(f"{path}\n\tneed {self.count} of {len(self.of)} items")

        did_iter = False

        for combo in itertools.combinations(self.of, self.count):
            did_iter = True

            with_solutions = [
                rule.solutions(ctx=ctx, path=[*path, f"$of[{i}]"])
                for i, rule in enumerate(combo)
            ]

            for i, ruleset in enumerate(itertools.product(*with_solutions)):
                msg = f"{[*path, f'$of/product#{i}']}\n\t{ruleset}"
                yield CountSolution(items=list(ruleset))

        if not did_iter:
            # be sure that we always yield something
            yield CountSolution(items=[])


@dataclass(frozen=True)
class CountSolution:
    items: List[Solution]

    def audit(self):
        ...


@dataclass(frozen=True)
class CourseRule:
    course: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> CourseRule:
        return CourseRule(course=data["course"])

    def validate(self):
        method_a = re.match(r"[A-Z]{3,5} [0-9]{3}", self.course)
        method_b = re.match(r"[A-Z]{2}/[A-Z]{2} [0-9]{3}", self.course)
        method_c = re.match(r"(IS|ID) [0-9]{3}", self.course)
        assert (
            method_a or method_b or method_c
        ) is not None, f"{self.course}, {method_a}, {method_b}, {method_c}"

    def solutions(self, *, path: List[str]):
        logging.debug(f'{path}\n\treference to course "{self.course}"')

        yield CourseSolution(course=self.course)


@dataclass(frozen=True)
class CourseSolution:
    course: str

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

        saves = ctx.saves
        requirements = ctx.child_requirements

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
                    name in ctx.child_requirements
                ), f"expected to find '{name}' once, but could not find it {dbg}"

        elif self.mode == "saves":
            # TODO: assert that the result type of all mentioned saves is the same
            if not self.saves or not saves:
                raise ValueError("expected self.saves and args.saves to be lists")
            for name in self.saves:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert (
                    name in ctx.saves
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

    def solutions_when_student(self, *, ctx, path):
        if self.source.itemtype == "courses":
            data = ctx.transcript
        else:
            raise KeyError(f"{self.source.itemtype} not yet implemented")

        yield data

    def solutions_when_saves(self, *, ctx, path):
        saves = [ctx.saves[s].solutions(ctx=ctx, path=path) for s in self.source.saves]

        for p in itertools.product(*saves):
            data = [item for save_result in p for item in save_result.stored()]
            yield data

    def solutions_when_reqs(self, *, ctx, path):
        reqs = [
            ctx.child_requirements[s].solutions(ctx=ctx, path=path)
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
                yield FromSolution(output=data, action=None)
                return
            elif self.store:
                raise Exception("not implemented yet")

            assert self.action is not None

            for n in self.action.range(items=data):
                did_iter = True
                for combo in itertools.combinations(data, n):
                    yield FromSolution(output=combo, action=self.action)

        if not did_iter:
            # be sure we always yield something
            logging.info("did not yield anything; yielding empty collection")
            yield FromSolution(output=[], action=self.action)


@dataclass(frozen=True)
class SaveRule:
    innards: FromRule
    name: str

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
    output: Sequence[Union[CourseInstance, Term, Grade, Semester]]
    action: Optional[FromAssertion]

    def stored(self):
        return self.output


@dataclass(frozen=True)
class Term:
    pass


@dataclass(frozen=True)
class Grade:
    pass


@dataclass(frozen=True)
class Semester:
    pass


@dataclass(frozen=True)
class ReferenceRule:
    requirement: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "requirement" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> ReferenceRule:
        return ReferenceRule(requirement=data["requirement"])

    def validate(self, *, ctx: RequirementContext):
        if self.requirement not in ctx.child_requirements:
            reqs = ", ".join(ctx.child_requirements.keys())
            raise AssertionError(
                f"expected a requirement named '{self.requirement}', but did not find one [options: {reqs}]"
            )

        ctx.child_requirements[self.requirement].validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f'{path}\n\treference to requirement "{self.requirement}"')

        requirement = ctx.child_requirements[self.requirement]

        logging.debug(f'{path}\n\tfound requirement "{self.requirement}"')

        yield from requirement.solutions(
            ctx=ctx, path=[*path, f"$ref->{self.requirement}"]
        )


RuleTypeUnion = Union[CourseRule, CountRule, FromRule, ActionRule, ReferenceRule]


@dataclass(frozen=True)
class Rule:
    rule: RuleTypeUnion

    @staticmethod
    def load(data: Dict) -> Rule:
        if CourseRule.can_load(data):
            return Rule(rule=CourseRule.load(data))
        elif FromRule.can_load(data):
            return Rule(rule=FromRule.load(data))
        elif CountRule.can_load(data):
            return Rule(rule=CountRule.load(data))
        elif ReferenceRule.can_load(data):
            return Rule(rule=ReferenceRule.load(data))
        elif ActionRule.can_load(data):
            return Rule(rule=ActionRule.load(data))

        dbg = json.dumps(data)
        raise ValueError(
            f"expected Course, Given, Count, Both, Either, or Do; found none of those ({dbg})"
        )

    def validate(self, *, ctx: RequirementContext):
        if isinstance(self.rule, CourseRule):
            self.rule.validate()
        elif isinstance(self.rule, ActionRule):
            self.rule.validate()
        elif isinstance(self.rule, FromRule):
            self.rule.validate(ctx=ctx)
        elif isinstance(self.rule, CountRule):
            self.rule.validate(ctx=ctx)
        elif isinstance(self.rule, ReferenceRule):
            self.rule.validate(ctx=ctx)
        else:
            raise ValueError(f"panic! unknown type of rule was constructed {self.rule}")

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f"{path} finding solutions for {self.rule}")

        if isinstance(self.rule, CourseRule):
            yield from self.rule.solutions(path=path)
        elif isinstance(self.rule, ActionRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, FromRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, CountRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, ReferenceRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        else:
            raise ValueError(
                f"panic! unknown type of rule was constructed {self.rule} (at {path})"
            )

        logging.debug(f"{path} all solutions found for {self.rule}")


@dataclass(frozen=True)
class Solution:
    rule: RuleTypeUnion


@dataclass(frozen=True)
class RequirementContext:
    transcript: List[CourseInstance]
    saves: Dict[str, SaveRule]
    child_requirements: Dict[str, Requirement]


@dataclass(frozen=True)
class CourseInstance:
    data: Dict[str, Any]

    @staticmethod
    def from_s(course: str) -> CourseInstance:
        return CourseInstance.from_dict(course=course)

    @staticmethod
    def from_dict(**kwargs) -> CourseInstance:
        data = {
            "course": kwargs["course"],
            "subject": [kwargs["course"].split(" ")[0]],
            "number": int(kwargs["course"].split(" ")[1]),
            "level": int(kwargs["course"].split(" ")[1]) // 100 * 100,
            "attributes": kwargs.get("attributes", []),
        }
        return CourseInstance(data=data)

    def update(self, **kwargs):
        return CourseInstance(data={**self.data, **kwargs})

    def course(self):
        return self.data["course"]

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
            if clause.key in self.data:
                logging.debug(f'single-clause, key "{clause.key}" exists')
                return clause.compare(self.data[clause.key])
            logging.debug(
                f'single-clause, key "{clause.key}" not found in {list(self.data.keys())}'
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

    @staticmethod
    def load(name: str, data: Dict[str, Any]) -> Requirement:
        children = {
            name: Requirement.load(name, r)
            for name, r in data.get("requirements", {}).items()
        }

        result = data.get("result", None)
        if result is not None:
            result = Rule.load(result)

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
                saves={name: s for name, s in validated_saves.items()},
                child_requirements=children,
            )
            save.validate(ctx=new_ctx)
            validated_saves[save.name] = save

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            saves={name: s for name, s in self.saves.items() or {}},
            child_requirements=children,
        )

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
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
            saves={s.name: s for s in self.saves.values()},
            child_requirements={r.name: r for r in self.requirements.values()},
        )

        path = [*path, ".result"]
        for sol in self.result.solutions(ctx=new_ctx, path=path):
            yield RequirementSolution(solution=sol)


@dataclass(frozen=True)
class RequirementSolution:
    solution: Any

    def matched(self):
        return self.solution


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

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        requirements = {
            name: Requirement.load(name, r) for name, r in data["requirements"].items()
        }
        result = Rule.load(data["result"])

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
            transcript=[], saves={}, child_requirements=self.requirements
        )

        self.result.validate(ctx=ctx)

    def solutions(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logging.debug(f"{path}\n\tevaluating area.result")

        ctx = RequirementContext(
            transcript=transcript,
            saves={},
            child_requirements={name: r for name, r in self.requirements.items()},
        )

        new_path = [*path, ".result"]
        yield from self.result.solutions(ctx=ctx, path=new_path)

        logging.debug(f"{path}\n\tall solutions generated")


def load(stream: TextIO) -> AreaOfStudy:
    data = yaml.load(stream=stream, Loader=yaml.SafeLoader)

    return AreaOfStudy.load(data)


def take(iterable, n):
    for i, item in enumerate(iterable):
        yield item
        if i + 1 >= n:
            break


def count(iterable, print_every=None):
    counter = 0
    for item in iterable:
        counter += 1
        if print_every is not None and counter % print_every == 0:
            print(f"... {counter}")
    return counter


if __name__ == "__main__":
    # import click
    import glob
    import time
    import coloredlogs
    import pprint

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logformat = "%(levelname)s %(message)s"
    coloredlogs.install(level="DEBUG", logger=logger, fmt=logformat)

    # @click.command()
    def main():
        """Audits a student against their areas of study."""

        with open("./student.yaml", "r", encoding="utf-8") as infile:
            data = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            transcript = [CourseInstance.from_dict(**row) for row in data["courses"]]

        # for file in glob.iglob("./gobbldygook-area-data/2018-19/*/*.yaml"):
        for file in [
            # "./gobbldygook-area-data/2018-19/major/computer-science.yaml",
            # "./gobbldygook-area-data/2018-19/major/asian-studies.yaml",
            "./gobbldygook-area-data/2018-19/major/womens-and-gender-studies.yaml"
            # "./sample-simple-area.yaml"
        ]:
            print(f"processing {file}")
            with open(file, "r", encoding="utf-8") as infile:
                area = load(infile)

            area.validate()

            this_transcript = [
                c.update(attributes=area.attributes["courses"].get(c.course(), []))
                for c in transcript
            ]

            # pprint.pprint(this_transcript)

            outname = f'./tmp/{area.kind}/{area.name.replace("/", "_")}.json'
            with open(outname, "w", encoding="utf-8") as outfile:
                jsonpickle.set_encoder_options("json", sort_keys=True, indent=4)
                outfile.write(jsonpickle.encode(area, unpicklable=True))

            start = time.perf_counter()

            # the_count = 0
            # for sol in area.solutions(transcript=this_transcript):
            #     the_count += 1
            #     # pprint.pprint(sol)

            the_count = count(area.solutions(transcript=transcript), print_every=1_000)

            print(f"{the_count} possible solutions")
            end = time.perf_counter()
            print(f"time: {end - start}")
            print()

    main()
