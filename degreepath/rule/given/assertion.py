from dataclasses import dataclass
from typing import Dict, Union, Any, List, Tuple, Iterable
import re
import logging
import enum

from ...clause import Operator
from ...constants import Constants


def load_assertion(data: Dict, c: Constants):
    if "$and" in data:
        assert len(data.keys()) is 1
        return AndAssertion.load(data["$and"], c)
    elif "$or" in data:
        assert len(data.keys()) is 1
        return OrAssertion.load(data["$or"], c)

    assert type(data) == dict, "data must be a dictionary: {}".format(data)

    return SingleAssertion.load(data, c)


@dataclass(frozen=True)
class AssertionCollection:
    children: Tuple

    def __iter__(self):
        yield from self.children

    def minmax(self, items: List) -> Tuple[int, int]:
        ranges = [c.minmax(items) for c in self]
        lo = min(r[0] for r in ranges)
        hi = max(r[1] for r in ranges)
        return (lo, hi)

    def range(self, items: List) -> Iterable:
        lo, hi = self.minmax(items)
        return range(lo, hi)

    def get_min_value(self) -> int:
        return max(c.get_max_value() for c in self)

    def get_max_value(self) -> int:
        return min(c.get_min_value() for c in self)

    def validate(self, *, ctx):
        for child in self.children:
            child.validate(ctx=ctx)


@dataclass(frozen=True)
class AndAssertion(AssertionCollection):
    def to_dict(self):
        return {
            "type": "from-assertion/and",
            "children": [c.to_dict() for c in self.children],
            "min": self.get_min_value(),
            "max": self.get_max_value(),
        }

    @staticmethod
    def load(data: List[Dict], c: Constants):
        clauses = [SingleAssertion.load(clause, c) for clause in data]
        return AndAssertion(children=tuple(clauses))

    def apply(self, value: Any):
        return all(c.apply(value) for c in self)


@dataclass(frozen=True)
class OrAssertion(AssertionCollection):
    def to_dict(self):
        return {
            "type": "from-assertion/or",
            "children": [c.to_dict() for c in self.children],
            "min": self.get_min_value(),
            "max": self.get_max_value(),
        }

    @staticmethod
    def load(data: Dict, c: Constants):
        clauses = [SingleAssertion.load(clause, c) for clause in data]
        return OrAssertion(children=tuple(clauses))

    def apply(self, value: Any):
        return any(c.apply(value) for c in self)


@enum.unique
class Command(enum.Enum):
    count = enum.auto()
    sum = enum.auto()
    minimum = enum.auto()
    maximum = enum.auto()
    average = enum.auto()
    # TODO: assert that the stored lookup exists
    stored = enum.auto()


@enum.unique
class Countables(enum.Enum):
    courses = enum.auto()
    areas = enum.auto()
    performances = enum.auto()
    terms = enum.auto()
    semesters = enum.auto()
    subjects = enum.auto()
    distinct_courses = enum.auto()


@enum.unique
class Summables(enum.Enum):
    grades = enum.auto()
    credits = enum.auto()


@enum.unique
class Averagables(enum.Enum):
    grades = enum.auto()
    credits = enum.auto()


@enum.unique
class Sortables(enum.Enum):
    terms = enum.auto()
    semesters = enum.auto()
    grades = enum.auto()
    credits = enum.auto()


Sources = Union[Countables, Summables, Averagables, Sortables, str]


@dataclass(frozen=True)
class SingleAssertion:
    command: Command
    source: Sources
    operator: Operator
    compare_to: Union[str, int, float]

    def to_dict(self):
        return {
            "type": "from-assertion",
            "command": self.command.name,
            "source": self.source.name,
            "operator": self.operator.name,
            "compare_to": self.compare_to,
        }

    @staticmethod
    def load(data: Dict, c: Constants):
        keys = list(data.keys())

        assert (len(keys)) == 1

        k = keys[0]

        m = re.match(r"(count|sum|minimum|maximum|stored|average)\((.*)\)", k)
        if not m:
            raise KeyError(f'expected "{k}" to match {assertion_key_regex}')

        val = data[k]

        assert len(val.keys()) == 1

        op = list(val.keys())[0]

        groups = m.groups()

        command = Command[groups[0]]
        if command is Command.count:
            Sources = Countables
        elif command is Command.sum:
            Sources = Summables
        elif command is Command.minimum or command is Command.maximum:
            Sources = Sortables
        elif command is Command.average:
            Sources = Averagables
        elif command is Command.stored:
            Sources = {}

        source = Sources[groups[1]]
        operator = Operator(op)
        compare_to = val[op]

        if isinstance(compare_to, list):
            compare_to = tuple(compare_to)

        return SingleAssertion(command=command, source=source, operator=operator, compare_to=compare_to)

    def validate(self, *, ctx):
        pass

    def get_min_value(self):
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(f"compare_to must be numeric to be used in min(); was {repr(compare_to)} ({type(compare_to)}")

        return compare_to

    def get_max_value(self):
        compare_to = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(f"compare_to must be numeric to be used in max(); was {repr(compare_to)} ({type(compare_to)}")

        return compare_to

    def range(self, items: List) -> Iterable:
        lo, hi = self.minmax(items)
        return range(lo, hi)

    def minmax(self, items: List) -> Tuple[int, int]:
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(f"compare_to must be numeric to be used in a range; was {repr(compare_to)} ({type(compare_to)}")

        if self.operator == Operator.LessThanOrEqualTo:
            hi = compare_to
            # lo = len(items)
            lo = 0

        elif self.operator == Operator.LessThan:
            hi = compare_to - 1
            # lo = len(items)
            lo = 0

        elif self.operator == Operator.GreaterThan:
            lo = compare_to + 1
            hi = max(len(items), lo + 1)

        elif self.operator == Operator.GreaterThanOrEqualTo:
            lo = compare_to
            hi = max(len(items), lo + 1)

        elif self.operator == Operator.EqualTo:
            hi = compare_to + 1
            lo = compare_to

        else:
            raise Exception(f"unknown operator {self.operator}")

        if hi <= lo:
            logging.info(f"expected hi={hi} > lo={lo}")

        return (lo, hi)

    def apply(self, value: Any) -> bool:
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(f"compare_to must be numeric to be used in apply(); was {repr(compare_to)} ({type(compare_to)}")

        if self.operator == Operator.LessThanOrEqualTo:
            return value <= compare_to

        elif self.operator == Operator.LessThan:
            return value < compare_to

        elif self.operator == Operator.GreaterThan:
            return value > compare_to

        elif self.operator == Operator.GreaterThanOrEqualTo:
            return value >= compare_to

        elif self.operator == Operator.EqualTo:
            return value == compare_to

        elif self.operator == Operator.NotEqualTo:
            return value != compare_to

        else:
            raise Exception(f"unknown operator {self.operator}")


def str_assertion(assertion) -> str:
    if not isinstance(assertion, dict):
        return str_assertion(assertion.to_dict())

    if assertion["type"] == "from-assertion":
        op = assertion["operator"]
        if op == Operator.GreaterThanOrEqualTo.name:
            action_desc = f"at least {assertion['compare_to']}"
        elif op == Operator.GreaterThan.name:
            action_desc = f"at least {assertion['compare_to']}"
        elif op == Operator.LessThanOrEqualTo.name:
            action_desc = f"at most {assertion['compare_to']}"
        elif op == Operator.LessThan.name:
            action_desc = f"at most {assertion['compare_to']}"
        elif op == Operator.EqualTo.name:
            action_desc = f"exactly {assertion['compare_to']}"
        elif op == Operator.NotEqualTo.name:
            action_desc = f"not {assertion['compare_to']}"
        else:
            action_desc = ""

        source = assertion["source"]
        if source == "courses":
            word = "course" if assertion["compare_to"] == 1 else "courses"
        elif source == "subjects":
            word = "subject code" if assertion["compare_to"] == 1 else "subject codes"
        else:
            word = "items"

        return f"{action_desc} matching {word}"

    if assertion["type"] == "from-assertion/or":
        return f'({" or ".join(str_assertion(c) for c in assertion["children"])})'

    if assertion["type"] == "from-assertion/and":
        return f'({" and ".join(str_assertion(c) for c in assertion["children"])})'

    raise Exception('not an assertion')


AnyAssertion = Union[AndAssertion, OrAssertion, SingleAssertion]
