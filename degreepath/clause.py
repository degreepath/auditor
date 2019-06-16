from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Tuple, Dict, Any
import enum
import logging


class Operator(enum.Enum):
    LessThan = "$lt"
    LessThanOrEqualTo = "$lte"
    GreaterThan = "$gt"
    GreaterThanOrEqualTo = "$gte"
    EqualTo = "$eq"
    NotEqualTo = "$neq"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class AndClause:
    children: Tuple[Clause, ...]

    def to_dict(self):
        return {"type": "and-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: List[Dict]) -> Clause:
        clauses = []
        for clause in data:
            clauses.append(SingleClause.load(clause))
        return AndClause(children=tuple(clauses))

    def __iter__(self):
        yield from self.children


@dataclass(frozen=True)
class OrClause:
    children: Tuple[Clause, ...]

    def to_dict(self):
        return {"type": "or-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: Dict) -> Clause:
        clauses = []
        for clause in data:
            clauses.append(SingleClause.load(clause))
        return OrClause(children=tuple(clauses))

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
            "key": self.key,
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

        return AndClause(children=tuple(clauses))

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
