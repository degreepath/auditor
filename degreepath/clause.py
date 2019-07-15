from dataclasses import dataclass
from collections.abc import Mapping
from typing import Union, List, Tuple, Dict, Any
import enum
import logging
import decimal


class Operator(enum.Enum):
    LessThan = "$lt"
    LessThanOrEqualTo = "$lte"
    GreaterThan = "$gt"
    GreaterThanOrEqualTo = "$gte"
    EqualTo = "$eq"
    NotEqualTo = "$neq"
    In = "$in"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class AndClause:
    children: Tuple

    def to_dict(self):
        return {"type": "and-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: List[Dict]):
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
    children: Tuple

    def to_dict(self):
        return {"type": "or-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: Dict):
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
    def load(data: Dict):
        if not isinstance(data, Mapping):
            raise Exception(f'expected {data} to be a dictionary')

        if "$and" in data:
            assert len(data.keys()) is 1
            return AndClause.load(data["$and"])
        elif "$or" in data:
            assert len(data.keys()) is 1
            return OrClause.load(data["$or"])

        clauses = []
        for key, value in data.items():
            assert type(value) == dict, f"{data}"
            assert len(value.keys()) is 1, f"{value}"
            op = list(value.keys())[0]

            operator = Operator(op)
            expected_value = value[op]

            if key == "subjects":
                key = "subject"
            if key == "attribute":
                key = "attributes"
            if key == "gereq":
                key = "gereqs"

            if isinstance(expected_value, list):
                expected_value = tuple(expected_value)

            clause = SingleClause(key=key, expected=expected_value, operator=operator)

            clauses.append(clause)

        if len(clauses) == 1:
            return clauses[0]

        return AndClause(children=tuple(clauses))

    def compare(self, to_value: Any) -> bool:
        # logging.debug(f"clause/compare {to_value} against {self}")

        if isinstance(self.expected, tuple) and self.operator != Operator.In:
            raise Exception(f'operator {self.operator} does not accept a list as the expected value')
        elif not isinstance(self.expected, tuple) and self.operator == Operator.In:
            raise Exception('expected a list of values to compare with $in operator')

        if isinstance(to_value, tuple) or isinstance(to_value, list):
            if len(to_value) is 0:
                logging.debug(f"clause/compare: skipped (empty to_value)")
                return False

            if len(to_value) is 1:
                to_value = to_value[0]
            else:
                logging.debug(f"clause/compare: beginning recursive comparison")
                return any(self.compare(v) for v in to_value)

        if self.operator == Operator.In:
            logging.debug(f"clause/compare/$in: beginning inclusion check")
            return any(to_value == v for v in self.expected)

        if isinstance(to_value, str) and (
            isinstance(self.expected, int)
            or isinstance(self.expected, float)
            or isinstance(self.expected, decimal.Decimal)
        ):
            expected = str(self.expected)
        else:
            expected = self.expected

        if self.operator == Operator.LessThan:
            result = expected < to_value
        elif self.operator == Operator.LessThanOrEqualTo:
            result = expected <= to_value
        elif self.operator == Operator.EqualTo:
            result = expected == to_value
        elif self.operator == Operator.NotEqualTo:
            result = expected != to_value
        elif self.operator == Operator.GreaterThanOrEqualTo:
            result = expected >= to_value
        elif self.operator == Operator.GreaterThan:
            result = expected > to_value
        else:
            raise TypeError(f"unknown comparison function {self.operator}")

        logging.debug(
            f"clause/compare: '{expected}' {self.operator.value} '{to_value}'; {result}"
        )
        return result

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


def str_clause(clause) -> str:
    if not isinstance(clause, dict):
        return str_clause(clause.to_dict())
    if clause["type"] == "single-clause":
        return f"\"{clause['key']}\" {clause['operator']} \"{clause['expected']}\""
    elif clause["type"] == "or-clause":
        return f'({" or ".join(str_clause(c) for c in clause["children"])})'
    elif clause["type"] == "and-clause":
        return f'({" and ".join(str_clause(c) for c in clause["children"])})'


Clause = Union[AndClause, OrClause, SingleClause]
