from dataclasses import dataclass
from collections.abc import Mapping, Iterable
from typing import Union, List, Tuple, Dict, Any
import enum
import logging
import decimal
from .constants import Constants


def load_clause(data: Dict, c: Constants):
    if not isinstance(data, Mapping):
        raise Exception(f'expected {data} to be a dictionary')

    if "$and" in data:
        assert len(data.keys()) is 1
        return AndClause.load(data["$and"], c)
    elif "$or" in data:
        assert len(data.keys()) is 1
        return OrClause.load(data["$or"], c)

    clauses = [SingleClause.load(key, value, c) for key, value in data.items()]

    if len(clauses) == 1:
        return clauses[0]

    return AndClause(children=tuple(clauses))


class Operator(enum.Enum):
    LessThan = "$lt"
    LessThanOrEqualTo = "$lte"
    GreaterThan = "$gt"
    GreaterThanOrEqualTo = "$gte"
    EqualTo = "$eq"
    NotEqualTo = "$neq"
    In = "$in"
    NotIn = "$nin"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class AndClause:
    children: Tuple

    def to_dict(self):
        return {"type": "and-clause", "children": [c.to_dict() for c in self.children]}

    @staticmethod
    def load(data: List[Dict], c: Constants):
        clauses = [load_clause(clause, c) for clause in data]
        return AndClause(children=tuple(clauses))

    def validate(self, *, ctx):
        for c in self.children:
            c.validate(ctx=ctx)

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
    def load(data: Dict, c: Constants):
        clauses = [load_clause(clause, c) for clause in data]
        return OrClause(children=tuple(clauses))

    def validate(self, *, ctx):
        for c in self.children:
            c.validate(ctx=ctx)

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
    expected_verbatim: Any
    operator: Operator

    def to_dict(self):
        return {
            "type": "single-clause",
            "key": self.key,
            "expected": self.expected,
            "expected_verbatim": self.expected_verbatim,
            "operator": self.operator.name,
        }

    @staticmethod
    def load(key: str, value: Any, c: Constants):
        if not isinstance(value, Mapping):
            raise Exception(f'expected {value} to be a dictionary')

        assert len(value.keys()) is 1, f"{value}"
        op = list(value.keys())[0]

        operator = Operator(op)
        expected_value = value[op]

        if isinstance(expected_value, list):
            expected_value = tuple(expected_value)

        expected_verbatim = expected_value

        if key == "subjects":
            key = "subject"
        if key == "attribute":
            key = "attributes"
        if key == "gereq":
            key = "gereqs"

        if type(expected_value) == str:
            expected_value = c.get_by_name(expected_value)
        elif isinstance(expected_value, Iterable):
            expected_value = tuple(c.get_by_name(v) for v in expected_value)

        return SingleClause(
            key=key,
            expected=expected_value,
            operator=operator,
            expected_verbatim=expected_verbatim,
        )

    def validate(self, *, ctx):
        pass

    def compare(self, to_value: Any) -> bool:
        # logging.debug(f"clause/compare {to_value} against {self}")

        if isinstance(self.expected, tuple) and (self.operator is not Operator.In or self.operator is not Operator.NotIn):
            raise Exception(f'operator {self.operator} does not accept a list as the expected value')
        elif not isinstance(self.expected, tuple) and (self.operator is Operator.In or self.operator is Operator.NotIn):
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

        if self.operator is Operator.In:
            logging.debug(f"clause/compare/$in: beginning inclusion check")
            return any(to_value == v for v in self.expected)
        elif self.operator is Operator.NotIn:
            logging.debug(f"clause/compare/$in: beginning inclusion check")
            return all(to_value != v for v in self.expected)

        # if we're comparing to a string, make our value a string
        if isinstance(to_value, str) and not isinstance(self.expected, str):
            expected = str(self.expected)
        else:
            expected = self.expected

        if self.operator is Operator.LessThan:
            result = to_value < expected
        elif self.operator is Operator.LessThanOrEqualTo:
            result = to_value <= expected
        elif self.operator is Operator.EqualTo:
            result = to_value == expected
        elif self.operator is Operator.NotEqualTo:
            result = to_value != expected
        elif self.operator is Operator.GreaterThanOrEqualTo:
            result = to_value >= expected
        elif self.operator is Operator.GreaterThan:
            result = to_value > expected
        else:
            raise TypeError(f"unknown comparison function {self.operator}")

        logging.debug(f"clause/compare: `{to_value}` {self.operator.value} `{expected}`; {result}")
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
        if clause['expected'] == clause['expected_verbatim']:
            return f"\"{clause['key']}\" {clause['operator']} \"{clause['expected']}\""
        else:
            return f"\"{clause['key']}\" {clause['operator']} \"{clause['expected']}\" (via \"{clause['expected_verbatim']}\")"
    elif clause["type"] == "or-clause":
        return f'({" or ".join(str_clause(c) for c in clause["children"])})'
    elif clause["type"] == "and-clause":
        return f'({" and ".join(str_clause(c) for c in clause["children"])})'

    raise Exception('not a clause')


Clause = Union[AndClause, OrClause, SingleClause]
