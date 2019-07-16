from dataclasses import dataclass
from typing import Dict, Union, Any, List, Tuple, Iterable
import re
import logging

from ...clause import Operator


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
    def load(data: List[Dict]):
        clauses = [SingleAssertion.load(clause) for clause in data]
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
    def load(data: Dict):
        clauses = [SingleAssertion.load(clause) for clause in data]
        return OrAssertion(children=tuple(clauses))

    def apply(self, value: Any):
        return any(c.apply(value) for c in self)


assertion_key_regex = re.compile(r"(count|sum|minimum|maximum|stored|average)\((.*)\)")


@dataclass(frozen=True)
class SingleAssertion:
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
    def load(data: Dict):
        if "$and" in data:
            assert len(data.keys()) is 1
            return AndAssertion.load(data["$and"])
        elif "$or" in data:
            assert len(data.keys()) is 1
            return OrAssertion.load(data["$or"])

        assert type(data) == dict, "data must be a dictionary: {}".format(data)

        keys = list(data.keys())

        assert (len(keys)) == 1

        k = keys[0]

        m = assertion_key_regex.match(k)
        if not m:
            raise KeyError(f'expected "{k}" to match {assertion_key_regex}')

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

        return SingleAssertion(command=command, source=source, operator=operator, compare_to=compare_to)

    def validate(self, *, ctx):
        allowed_commands = [
            "count",
            "sum",
            "minimum",
            "maximum",
            "stored",
            "average",
        ]
        assert self.command in allowed_commands, f"{self.command} must be in {allowed_commands}"

        if self.command == "count":
            allowed = [
                "distinct courses",
                "courses",
                "areas",
                "performances",
                "terms",
                "semesters",
                "subjects",
            ]
            assert self.source in allowed, f"{self.source} not in {allowed}"
        elif self.command == "sum":
            allowed = ["grades", "credits"]
            assert self.source in allowed, f"{self.source} not in {allowed}"
        elif self.command == "average":
            allowed = ["grades", "credits"]
            assert self.source in allowed, f"{self.source} not in {allowed}"
        elif self.command == "minimum" or self.command == "maximum":
            allowed = ["terms", "semesters", "grades", "credits"]
            assert self.source in allowed, f"{self.source} not in {allowed}"
        elif self.command == "stored":
            # TODO: assert that the stored lookup exists
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
