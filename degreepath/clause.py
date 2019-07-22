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


def apply_operator(*, op, lhs, rhs) -> bool:
    if isinstance(lhs, tuple) and (op is not Operator.In and op is not Operator.NotIn and op is not Operator.EqualTo and op is not Operator.NotEqualTo):
        raise Exception(f'{op} does not accept a list as the expected value')

    if not isinstance(lhs, tuple) and (op is Operator.In or op is Operator.NotIn):
        raise Exception(f'expected a list of values to compare with {op}')

    if isinstance(lhs, tuple) and (op is Operator.EqualTo or op is Operator.NotEqualTo):
        if len(lhs) is 0:
            logging.debug(f"apply_operator/simplify: `{lhs}` was empty, so returning False")
            return False

        if len(lhs) is 1:
            logging.debug(f"apply_operator/simplify: reduced `{lhs}` to `{lhs[0]}`")
            lhs = lhs[0]
        else:
            if op is Operator.EqualTo:
                return apply_operator(lhs=lhs, op=Operator.In, rhs=rhs)
            elif op is Operator.NotEqualTo:
                return apply_operator(lhs=lhs, op=Operator.NotIn, rhs=rhs)

    if op is Operator.In:
        logging.debug(f"apply_operator/in: `{lhs}` {op.value} `{rhs}`")
        return any(apply_operator(op=Operator.EqualTo, lhs=v, rhs=rhs) for v in lhs)
    elif op is Operator.NotIn:
        logging.debug(f"apply_operator/not-in: `{lhs}` {op.value} `{rhs}`")
        return all(apply_operator(op=Operator.NotEqualTo, lhs=v, rhs=rhs) for v in lhs)

    if isinstance(lhs, str) and not isinstance(rhs, str):
        rhs = str(rhs)
    if not isinstance(lhs, str) and isinstance(rhs, str):
        lhs = str(lhs)

    if op is Operator.EqualTo:
        logging.debug(f"apply_operator: `{lhs}` {op} `{rhs}` == {lhs == rhs}")
        return lhs == rhs

    if op is Operator.NotEqualTo:
        logging.debug(f"apply_operator: `{lhs}` {op} `{rhs}` == {lhs != rhs}")
        return lhs != rhs

    if op is Operator.LessThan:
        logging.debug(f"apply_operator: `{lhs}` {op} `{rhs}` == {lhs < rhs}")
        return lhs < rhs

    if op is Operator.LessThanOrEqualTo:
        logging.debug(f"apply_operator: `{lhs}` {op} `{rhs}` == {lhs <= rhs}")
        return lhs <= rhs

    if op is Operator.GreaterThan:
        logging.debug(f"apply_operator: `{lhs}` {op} `{rhs}` == {lhs > rhs}")
        return lhs > rhs

    if op is Operator.GreaterThanOrEqualTo:
        logging.debug(f"apply_operator: `{lhs}` {op} `{rhs}` == {lhs >= rhs}")
        return lhs >= rhs

    raise TypeError(f"unknown comparison function {op}")


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
        return apply_operator(lhs=to_value, op=self.operator, rhs=self.expected)

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
