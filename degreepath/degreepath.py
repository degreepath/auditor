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
    do: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "do" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> ActionRule:
        return ActionRule(do=data["do"])

    def validate(self):
        pass

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f"{path} ActionRule#solutions")
        yield ActionSolution(result=None)


@dataclass(frozen=True)
class ActionSolution:
    result: Optional[bool]


@dataclass(frozen=True)
class BothRule:
    a: Rule
    b: Rule

    def __repr__(self):
        return f"(both-rule '{self.a} '{self.b})"

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "both" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> BothRule:
        return BothRule(a=Rule.load(data["both"][0]), b=Rule.load(data["both"][1]))

    def validate(self, *, ctx: RequirementContext):
        self.a.validate(ctx=ctx)
        self.b.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f"{path} BothRule#solutions for {self.a} && {self.b}")
        for a, b in itertools.product(
            self.a.solutions(ctx=ctx, path=[*path, "$both"]),
            self.b.solutions(ctx=ctx, path=[*path, "$both"]),
        ):
            yield BothSolution(a=a, b=b)


@dataclass(frozen=True)
class BothSolution:
    a: Rule
    b: Rule

    def __repr__(self):
        return f"[both '{self.a} '{self.b}]"


@dataclass(frozen=True)
class CountRule:
    count: int
    of: List[Rule]
    greedy: bool = False

    def __repr__(self):
        return f"(count-rule '{self.count} {self.of})"

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "count" in data and "of" in data:
            return True
        if "all" in data:
            return True
        if "any" in data:
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
        for combo in itertools.combinations(self.of, self.count):
            iterable = [
                rule.solutions(ctx=ctx, path=[*path, f"$of[{i}]"])
                for i, rule in enumerate(combo)
            ]

            for i, moar_combo in enumerate(itertools.product(*iterable)):
                logging.debug(
                    f"{[*path, f'product branch #{i}']} CountRule: {moar_combo}"
                )
                yield Solution.ok(CountRule(count=self.count, of=list(moar_combo)))


@dataclass(frozen=True)
class CountSolution:
    items: List[Solution]

    def __repr__(self):
        return f"[count '{len(self.items)} {self.items}]"


@dataclass(frozen=True)
class CourseRule:
    course: str

    def __repr__(self):
        return f"(course-rule '{self.course})"

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

    def solutions(self, *, ctx: RequirementContext, claims: Claims, path: List[str]):
        logging.debug(f'{path}\n\treference to course "{self.course}"')

        path = [*path, f"$c->{self.course}"]
        if not ctx.has_course(self.course):
            logging.debug(f'{path}\n\tcourse "{self.course}" does not exist in the transcript')
            return Solution.fail(self)

        claim = ctx.make_claim(course=self.course, key=path, value={'course': self.course})

        if claim.failed():
            logging.debug(f'{path}\n\tcourse "{self.course}" exists, but has already been claimed by {claim.conflict.path}')
            return Solution.fail(self)

        logging.debug(f'{path}\n\tcourse "{self.course}" exists, and has not been claimed')
        claim.commit()

        yield Solution.ok(self)


@dataclass(frozen=True)
class CourseSolution:
    course: str

    def __repr__(self):
        return f"[c '{self.course}]"


@dataclass(frozen=True)
class EitherRule:
    a: Rule
    b: Rule

    def __repr__(self):
        return f"(either-rule '{self.a} '{self.b})"

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "either" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> EitherRule:
        return EitherRule(
            a=Rule.load(data["either"][0]), b=Rule.load(data["either"][1])
        )

    def validate(self, *, ctx: RequirementContext):
        self.a.validate(ctx=ctx)
        self.b.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f"{path}\n\tEitherRule#solutions for either {self.a} || {self.b}")

        for sol in self.a.solutions(ctx=ctx, path=[*path, "$either->a"]):
            yield EitherSolution(choice=sol, index="a")
        for sol in self.a.solutions(ctx=ctx, path=[*path, "$either->b"]):
            yield EitherSolution(choice=sol, index="b")


@dataclass(frozen=True)
class EitherSolution:
    choice: Solution
    index: str

    def __repr__(self):
        return f"[either '{self.index} {self.choice}]"


@dataclass(frozen=True)
class Filter:
    attribute: Optional[str]
    institution: Optional[str]
    subject: Optional[str]
    level: Optional[str]

    def __repr__(self):
        def contents():
            if self.attribute is not None:
                yield ("attribute", self.attribute)
            if self.institution is not None:
                yield ("institution", self.institution)
            if self.subject is not None:
                yield ("subject", self.subject)
            if self.level is not None:
                yield ("level", self.level)

        body = dict(contents())

        return repr(body)

    @staticmethod
    def load(data: Dict) -> Filter:
        allowed = ["attribute", "institution", "subject", "level"]
        if set(data.keys()).difference(allowed):
            print(data)
            raise KeyError(f"unknown keys {set(data.keys()).difference(allowed)}")
        return Filter(
            attribute=data.get("attribute", None),
            institution=data.get("institution", None),
            subject=data.get("subject", None),
            level=data.get("level", None),
        )

    def apply(self, c: CourseInstance):
        if self.subject is not None:
            if self.subject not in c.subject:
                return False

        if self.attribute is not None:
            if self.attribute not in (c.attributes or []):
                return False

        if self.institution is not None:
            # if self.institution != c.institution
            return False

        if self.level is not None:
            if int(self.level) / 100 != int(c.course.split(" ")[1]) / 100:
                return False

        return True

    def filter(self, courses: List[CourseInstance]) -> List[CourseInstance]:
        return [c for c in courses if self.apply(c)]


@dataclass(frozen=True)
class Limit:
    at_most: int
    where: Filter

    @staticmethod
    def load(data: Dict) -> Limit:
        return Limit(at_most=data["at_most"], where=Filter.load(data["where"]))


class Operator(Enum):
    LessThan = "<"
    LessThanOrEqualTo = "<="
    GreaterThen = ">"
    GreaterThanOrEqualTo = ">="
    EqualTo = "="
    NotEqualTo = "!="


@dataclass(frozen=True)
class GivenAction:
    lhs: Union[str, int, GivenRule]
    op: Operator
    rhs: Union[str, int]

    def __repr__(self):
        return f"(action {self.lhs} {self.op.value} {self.rhs})"


@dataclass(frozen=True)
class GivenRule:
    given: str
    output: str

    action: Optional[GivenAction]

    limit: Optional[Limit] = None
    where: Optional[Filter] = None

    requirements: Optional[List[str]] = None
    saves: Optional[List[str]] = None
    courses: Optional[List[str]] = None
    save: Optional[str] = None

    def __repr__(self):
        return f"(given '{self.given} -> '{self.output} 'limits {self.limit or []} 'filter {self.where} 'action {self.action})"

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "given" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> GivenRule:
        where = data.get("where", None)
        if where is not None:
            where = Filter.load(where)

        limit = data.get("limit", None)
        if limit is not None:
            limit = [Limit.load(l) for l in limit]

        action = None
        if "do" in data:
            actionstr = shlex.split(data["do"])
            action = GivenAction(
                lhs=actionstr[0], op=Operator(actionstr[1]), rhs=actionstr[2]
            )

        return GivenRule(
            given=data["given"],
            output=data["what"],
            action=action,
            limit=limit,
            where=where,
            requirements=data.get("requirements", None),
            save=data.get("save", None),
            saves=data.get("saves", None),
            courses=data.get("courses", None),
        )

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.given, str)

        saves = ctx.saves
        requirements = ctx.child_requirements

        dbg = f"(when validating self={repr(self)}, saves={repr(saves)}, reqs={repr(requirements)})"

        if self.given == "these-requirements":
            if not self.requirements or not requirements:
                raise ValueError(
                    "expected self.requirements and args.requirements to be lists"
                )
            for name in self.requirements:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert (
                    name in ctx.child_requirements
                ), f"expected to find '{name}' once, but could not find it {dbg}"

        elif self.given == "these-saves":
            if not self.saves or not saves:
                raise ValueError("expected self.saves and args.saves to be lists")
            for name in self.saves:
                assert isinstance(name, str), f"expected {name} to be a string"
                assert (
                    name in ctx.saves
                ), f"expected to find '{name}' once, but could not find it {dbg}"

        elif self.given == "save":
            if not saves:
                raise ValueError("expected args.saves to be a list")
            assert (
                self.save in ctx.saves
            ), f"expected to find '{self.save}' once, but could not find it {dbg}"

        elif self.given == "these-courses":
            if not self.courses:
                raise ValueError("expected self.courses")
            assert len(self.courses) >= 1

        elif self.given == "courses":
            assert self.requirements is None
            assert self.saves is None
            assert self.courses is None

        elif self.given == "performances":
            assert self.requirements is None
            assert self.saves is None
            assert self.courses is None

        elif self.given == "attendances":
            assert self.requirements is None
            assert self.saves is None
            assert self.courses is None

        elif self.given == "areas":
            assert self.requirements is None
            assert self.saves is None
            assert self.courses is None

        else:
            raise NameError(f"unknown 'given' type {self.given}")

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        path = [*path, f"$given->{repr(self)}"]
        logging.debug(f"{path}")

        if self.given == "courses":
            yield from self.solutions_when_given_courses(ctx=ctx, path=path)
        elif self.given == "these-courses":
            yield from self.solutions_when_given_these_courses(ctx=ctx, path=path)
        elif self.given == "these-saves":
            assert self.saves is not None
            yield from self.solutions_when_given_saves(
                ctx=ctx, path=path, saves=self.saves
            )
        elif self.given == "save":
            assert self.save is not None
            yield from self.solutions_when_given_saves(
                ctx=ctx, path=path, saves=[self.save]
            )
        else:
            raise KeyError(f'unknown "given" type "{self.given}"')

    def solutions_when_given_courses(
        self, *, ctx: RequirementContext, path: List[str]
    ) -> Iterator[GivenSolution]:
        filtered = (
            self.where.filter(ctx.transcript)
            if self.where is not None
            else ctx.transcript
        )

        logging.warning(filtered)

        if self.action is None:
            yield GivenSolution(output=filtered, action=None)
            return

        for bound in range(int(self.action.rhs), len(filtered)):
            for i, combo in enumerate(itertools.combinations(filtered, bound)):
                logging.debug(
                    f"{[*path, f'combo branch #{i}']} GivenRule {[str(c) for c in combo]}"
                )
                yield GivenSolution(output=list(combo), action=self.action)

    def solutions_when_given_these_courses(
        self, *, ctx: RequirementContext, path: List[str]
    ) -> Iterator[GivenSolution]:
        if not self.courses:
            raise ValueError(
                "when given:these-courses, the `courses:` key must not be empty"
            )

        filtered = [c for c in ctx.transcript if c.course in self.courses]

        filtered = self.where.filter(filtered) if self.where is not None else filtered

        if self.action is None:
            return GivenSolution(output=filtered, action=None)

        for bound in range(int(self.action.rhs), len(filtered)):
            for i, combo in enumerate(itertools.combinations(filtered, bound)):
                logging.debug(
                    f"{[*path, f'combo branch #{i}']} GivenRule {[str(c) for c in combo]}"
                )
                yield GivenSolution(output=list(combo), action=self.action)

    def solutions_when_given_saves(
        self, *, ctx: RequirementContext, path: List[str], saves: List[str]
    ) -> Iterator[GivenSolution]:
        if not saves:
            raise ValueError(
                "when given:these-saves/save, the `saves:/save:` key must not be empty"
            )
        logging.debug(f"solutions_when_given_saves {saves}")

        single_save = saves[0]

        the_save = ctx.saves[single_save]

        for solution in the_save.solutions(ctx=ctx, path=[*path, ">>save"]):
            logging.debug(solution)

            if self.action is None:
                yield solution
            else:
                for bound in range(int(self.action.rhs), len(solution.output)):
                    combos = itertools.combinations(solution.output, bound)
                    for i, combo in enumerate(combos):
                        logging.debug(
                            f"{[*path, f'combo branch #{i}']} GivenRule {[str(c) for c in combo]}"
                        )
                        yield GivenSolution(output=list(combo), action=self.action)


@dataclass(frozen=True)
class SaveRule:
    innards: GivenRule
    name: str

    @staticmethod
    def load(data: Dict) -> SaveRule:
        return SaveRule(innards=GivenRule.load(data), name=data["name"])

    def validate(self, *, ctx: RequirementContext):
        assert self.name.strip() != ""

        self.innards.validate(ctx=ctx)

    def solutions(
        self, *, ctx: RequirementContext, path: List[str]
    ) -> Iterator[GivenSolution]:
        logging.debug("inside a saverule")
        yield from self.innards.solutions(
            ctx=ctx, path=[*path, f'.save["{self.name}"]']
        )


@dataclass(frozen=True)
class GivenSolution:
    output: Sequence[Union[CourseInstance, Term, Grade, Semester]]
    action: Optional[GivenAction]


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

        yield from ctx.child_requirements[self.requirement].solutions(
            ctx=ctx, path=[*path, f"$ref->{self.requirement}"]
        )


RuleTypeUnion = Union[
    CourseRule, CountRule, EitherRule, BothRule, GivenRule, ActionRule, ReferenceRule
]


@dataclass(frozen=True)
class Rule:
    rule: RuleTypeUnion

    def __repr__(self):
        return f"[rule {self.rule}]"

    @staticmethod
    def load(data: Union[Dict, str]) -> Rule:
        if isinstance(data, str):
            return Rule(rule=CourseRule(course=data))
        elif CourseRule.can_load(data):
            return Rule(rule=CourseRule.load(data))
        elif GivenRule.can_load(data):
            return Rule(rule=GivenRule.load(data))
        elif CountRule.can_load(data):
            return Rule(rule=CountRule.load(data))
        elif BothRule.can_load(data):
            return Rule(rule=BothRule.load(data))
        elif EitherRule.can_load(data):
            return Rule(rule=EitherRule.load(data))
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
        elif isinstance(self.rule, GivenRule):
            self.rule.validate(ctx=ctx)
        elif isinstance(self.rule, CountRule):
            self.rule.validate(ctx=ctx)
        elif isinstance(self.rule, BothRule):
            self.rule.validate(ctx=ctx)
        elif isinstance(self.rule, EitherRule):
            self.rule.validate(ctx=ctx)
        elif isinstance(self.rule, ReferenceRule):
            self.rule.validate(ctx=ctx)
        else:
            raise ValueError(f"panic! unknown type of rule was constructed {self.rule}")

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        if isinstance(self.rule, CourseRule):
            yield from self.rule.solutions(path=path)
        elif isinstance(self.rule, ActionRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, GivenRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, CountRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, BothRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, EitherRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        elif isinstance(self.rule, ReferenceRule):
            yield from self.rule.solutions(ctx=ctx, path=path)
        else:
            raise ValueError(
                f"panic! unknown type of rule was constructed {self.rule} (at {path})"
            )


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
    course: str
    subject: List[str]
    attributes: Optional[List[str]] = None

    @staticmethod
    def from_dict(**kwargs):
        return CourseInstance(
            course=kwargs["course"],
            subject=kwargs["subject"],
            attributes=kwargs.get("attributes", None),
        )

    def __str__(self):
        return f"{self.course}"


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
            name: SaveRule.load(name, s)
            for name, s in data.get("saves", {}).items()
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
        for save in self.saves:
            new_ctx = RequirementContext(
                transcript=ctx.transcript,
                saves={name: s for name, s in validated_saves.items()},
                child_requirements=children,
            )
            save.validate(ctx=new_ctx)
            validated_saves[save.name] = save

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            saves={name: s for name, s in self.saves or {}},
            child_requirements=children,
        )

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        path = [*path, f"$req->{self.name}"]

        header = f'{path}\n\trequirement "{self.name}"'

        logging.debug(f'{header} has not been evaluated')
        # TODO: implement caching

        if not self.message:
            logging.debug(f'{header} has no message')

        if not self.audited_by:
            logging.debug(f'{header} is not audited')

        if not self.result:
            logging.debug(f'{header} does not have a result')
            return
        else:
            logging.debug(f'{header} has a result')

        new_ctx = RequirementContext(
            transcript=ctx.transcript,
            saves={s.name: s for s in self.saves},
            child_requirements={r.name: r for r in self.requirements or []},
        )

        path = [*path, ".result"]
        yield from self.result.solutions(ctx=new_ctx, path=path)


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""

    name: str
    kind: str
    degree: Optional[str]
    catalog: str

    result: Rule
    requirements: Dict[str, Requirement]

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        requirements = {
            name: Requirement.load(name, r)
            for name, r in data["requirements"].items()
        }
        result = Rule.load(data["result"])

        return AreaOfStudy(
            name=data["name"],
            catalog=data["catalog"],
            degree=data.get("degree", None),
            kind=data["type"],
            requirements=requirements,
            result=result,
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
            saves={},
            child_requirements=self.requirements,
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

        path = [*path, ".result"]
        return self.result.solutions(ctx=ctx, path=path)


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
            # "./gobbldygook-area-data/2018-19/major/womens-and-gender-studies.yaml"
            "./sample-simple-area.yaml"
        ]:
            print(f"processing {file}")
            with open(file, "r", encoding="utf-8") as infile:
                area = load(infile)

            area.validate()

            outname = f'./tmp/{area.kind}/{area.name.replace("/", "_")}.json'
            with open(outname, "w", encoding="utf-8") as outfile:
                jsonpickle.set_encoder_options("json", sort_keys=False, indent=4)
                outfile.write(jsonpickle.encode(area, unpicklable=True))

            start = time.perf_counter()

            for sol in area.solutions(transcript=transcript):
                print(sol)

            the_count = count(area.solutions(transcript=transcript), print_every=1_000)

            print(f"{the_count} possible combinations")
            end = time.perf_counter()
            print(f"time: {end - start}")
            print()

    main()
