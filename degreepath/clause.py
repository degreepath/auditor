from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Tuple, Dict, Any
import enum
import logging
import collections


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
        clauses = [SingleClause.load(clause) for clause in data]
        return AndClause(children=tuple(clauses))

    def __iter__(self):
        yield from self.children

    def mc_applies_same(self, other) -> bool:
        """Checks if this clause applies to the same items as the other clause,
        when used as part of a multicountable ruleset."""

        return any(c.mc_applies_same(other) for c in self)


@dataclass(frozen=True)
class OrClause:
    children: Tuple[Clause, ...]

    def to_dict(self):
        return {"type": "or-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: Dict) -> Clause:
        clauses = [SingleClause.load(clause) for clause in data]
        return OrClause(children=tuple(clauses))

    def __iter__(self):
        yield from self.children

    def mc_applies_same(self, other) -> bool:
        """Checks if this clause applies to the same items as the other clause,
        when used as part of a multicountable ruleset."""

        return any(c.mc_applies_same(other) for c in self)


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
            assert len(data.keys()) is 1
            return AndClause.load(data["$and"])
        elif "$or" in data:
            assert len(data.keys()) is 1
            return OrClause.load(data["$or"])

        clauses = []
        for key, value in data.items():
            assert len(value.keys()) is 1
            op = list(value.keys())[0]

            operator = Operator(op)
            expected_value = value[op]

            if key == 'subjects':
                key = 'subject'
            if key == 'attribute':
                key = 'attributes'

            clause = SingleClause(key=key, expected=expected_value, operator=operator)

            clauses.append(clause)

        return AndClause(children=tuple(clauses))

    def compare(self, to_value: Any) -> bool:
        logging.debug(f"Clause.compare {self}, to: {to_value}")

        if isinstance(to_value, tuple) or isinstance(to_value, list):
            if len(to_value) is 0:
                logging.debug(f"Skipping comparison as to_value was empty")
                return False
            
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

    def mc_applies_same(self, other) -> bool:
        """Checks if this clause applies to the same items as the other clause,
        when used as part of a multicountable ruleset."""

        if isinstance(other, AndClause):
            return other.mc_applies_same(self)

        if isinstance(other, OrClause):
            return other.mc_applies_same(self)

        if not isinstance(other, SingleClause):
            return False

        return (
            self.key == other.key
            and self.expected == other.expected
            and self.operator == other.operator
        )

    def applies_to(self, other) -> bool:
        return self.compare(other)


def str_clause(clause: Clause) -> str:
    if clause["type"] == "single-clause":
        return f"\"{clause['key']}\" {clause['operator']} \"{clause['expected']}\""
    elif clause["type"] == "or-clause":
        return f'({" or ".join(str_clause(c) for c in clause["children"])})'
    elif clause["type"] == "and-clause":
        return f'({" and ".join(str_clause(c) for c in clause["children"])})'


Clause = Union[AndClause, OrClause, SingleClause]
