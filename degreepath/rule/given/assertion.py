from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Any, List, Tuple, TYPE_CHECKING
import re
import itertools
import logging

from ...clause import Operator

if TYPE_CHECKING:
    from ...requirement import RequirementContext


@dataclass(frozen=True)
class AndAssertion:
    children: Tuple[AnyAssertion, ...]

    def to_dict(self):
        return {"type": "from-assertion/and", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: List[Dict]) -> AnyAssertion:
        clauses = [Assertion.load(clause) for clause in data]
        return AndAssertion(children=tuple(clauses))

    def __iter__(self):
        yield from self.children

    def apply(self, value: Any):
        return all(c.apply(value) for c in self)


@dataclass(frozen=True)
class OrAssertion:
    children: Tuple[AnyAssertion, ...]

    def to_dict(self):
        return {"type": "from-assertion/or", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: Dict) -> AnyAssertion:
        clauses = [Assertion.load(clause) for clause in data]
        return OrAssertion(children=tuple(clauses))

    def __iter__(self):
        yield from self.children

    def apply(self, value: Any):
        return any(c.apply(value) for c in self)


@dataclass(frozen=True)
class Assertion:
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
    def load(data: Dict) -> Assertion:
        if "$and" in data:
            assert len(data.keys()) is 1
            return AndAssertion.load(data["$and"])
        elif "$or" in data:
            assert len(data.keys()) is 1
            return OrAssertion.load(data["$or"])

        keys = list(data.keys())

        assert (len(keys)) == 1

        rex = re.compile(r"(count|sum|minimum|maximum|stored|average)\((.*)\)")

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

        if isinstance(compare_to, list):
            compare_to = tuple(compare_to)

        return Assertion(
            command=command, source=source, operator=operator, compare_to=compare_to
        )

    def validate(self, *, ctx: RequirementContext):
        assert self.command in [
            "count",
            "sum",
            "minimum",
            "maximum",
            "stored",
            "average",
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
        elif self.command == "average":
            assert self.source in ["grades", "credits"]
        elif self.command == "minimum" or self.command == "maximum":
            assert self.source in ["terms", "semesters", "grades", "credits"]
        elif self.command == "stored":
            # TODO: assert that the stored lookup exists
            pass

    def get_value(self):
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(
                f"compare_to must be numeric to be used in min(); was {repr(compare_to)} ({type(compare_to)}"
            )

        return compare_to

    def range(self, *, items: List):
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(
                f"compare_to must be numeric to be used in range(); was {repr(compare_to)} ({type(compare_to)}"
            )

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

        if hi <= lo:
            logging.info(f"expected hi={hi} > lo={lo}")

        return range(lo, hi)

    def apply(self, value: Any):
        compare_to: Any = self.compare_to

        if type(compare_to) not in [int, float]:
            raise TypeError(
                f"compare_to must be numeric to be used in apply(); was {repr(compare_to)} ({type(compare_to)}"
            )

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

        else:
            raise Exception("um")


AnyAssertion = Union[AndAssertion, OrAssertion, Assertion]
