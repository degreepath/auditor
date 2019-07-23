from dataclasses import dataclass
from collections.abc import Mapping, Iterable
from typing import Union, List, Tuple, Dict, Any, Callable, Optional, Sequence
import enum
import logging
import decimal
# from functools import lru_cache
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


# @lru_cache(maxsize=256, typed=True)
def apply_operator(*, op, lhs, rhs) -> bool:
    """
    Applies two values (lhs and rhs) to an operator.

    `lhs` is drawn from the input data, while `rhs` is drawn from the area specification.

    {attributes: {$eq: csci_elective}}, then, is transformed into something like
    {[csci_elective, csci_systems]: {$eq: csci_elective}}, which is reduced to a set of
    checks: csci_elective == csci_elective && csci_systems == csci_elective.

    {count(courses): {$gte: 2}} is transformed into {5: {$gte: 2}}, which becomes
    `5 >= 2`.

    The additional complications are as follows:

    1. When the comparison is started, if only one of RHS,LHS is a string, the
       other is coerced into a string.

    2. If both LHS and RHS are sequences, an error is raised.

    3. If LHS is a sequence, and OP is .EqualTo, OP is changed to .In
    4. If LHS is a sequence, and OP is .NotEqualTo, OP is changed to .NotIn
    """
    logging.debug("apply_operator: `{}` ({}) {} `{}` ({})", lhs, type(lhs), op, rhs, type(rhs))

    if isinstance(lhs, tuple) and isinstance(rhs, tuple):
        if op is not Operator.In:
            raise Exception('both rhs and lhs must not be sequences when using {}; lhs={}, rhs={}', op, lhs, rhs)

        if lhs == tuple() or rhs == tuple():
            logging.debug("apply_operator/skip: either lhs={} or rhs={} was empty; returning false", lhs == tuple(), rhs == tuple())
            return False

        logging.debug("apply_operator/coerce: converting both {} and {} to sets of strings, and running issubset", lhs, rhs)
        lhs = set(str(s) for s in lhs)
        rhs = set(str(s) for s in rhs)
        logging.debug("apply_operator/coerce: lhs={}; rhs={}; lhs.issubset(rhs)={}; rhs.issubset(lhs)={}", lhs, rhs, lhs.issubset(rhs), rhs.issubset(lhs))
        return lhs.issubset(rhs) or rhs.issubset(lhs)

    if isinstance(lhs, tuple) or isinstance(rhs, tuple):
        if op is Operator.EqualTo:
            logging.debug("apply_operator/coerce: got lhs={} / rhs={}; switching to {}", type(lhs), type(rhs), Operator.In)
            return apply_operator(op=Operator.In, lhs=lhs, rhs=rhs)
        elif op is Operator.NotEqualTo:
            logging.debug("apply_operator/coerce: got lhs={} / rhs={}; switching to {}", type(lhs), type(rhs), Operator.NotIn)
            return apply_operator(op=Operator.NotIn, lhs=lhs, rhs=rhs)

        if op is Operator.In:
            logging.debug("apply_operator/in: `{}` {} `{}`", lhs, op.value, rhs)
            if isinstance(lhs, tuple):
                return any(apply_operator(op=Operator.EqualTo, lhs=v, rhs=rhs) for v in lhs)
            if isinstance(rhs, tuple):
                return any(apply_operator(op=Operator.EqualTo, lhs=lhs, rhs=v) for v in rhs)
            raise TypeError(f"{op}: expected either {type(lhs)} or {type(rhs)} to be a tuple")

        elif op is Operator.NotIn:
            logging.debug("apply_operator/not-in: `{}` {} `{}`", lhs, op.value, rhs)
            if isinstance(lhs, tuple):
                return all(apply_operator(op=Operator.NotEqualTo, lhs=v, rhs=rhs) for v in lhs)
            if isinstance(rhs, tuple):
                return all(apply_operator(op=Operator.NotEqualTo, lhs=lhs, rhs=v) for v in rhs)
            raise TypeError(f"{op}: expected either {type(lhs)} or {type(rhs)} to be a tuple")

        else:
            raise Exception(f'{op} does not accept a list; got {lhs} ({type(lhs)})')

    if isinstance(lhs, str) and not isinstance(rhs, str):
        rhs = str(rhs)
    if not isinstance(lhs, str) and isinstance(rhs, str):
        lhs = str(lhs)

    if op is Operator.EqualTo:
        logging.debug("apply_operator: `{}` {} `{}` == {}", lhs, op, rhs, lhs == rhs)
        return lhs == rhs

    if op is Operator.NotEqualTo:
        logging.debug("apply_operator: `{}` {} `{}` == {}", lhs, op, rhs, lhs != rhs)
        return lhs != rhs

    if op is Operator.LessThan:
        logging.debug("apply_operator: `{}` {} `{}` == {}", lhs, op, rhs, lhs < rhs)
        return lhs < rhs

    if op is Operator.LessThanOrEqualTo:
        logging.debug("apply_operator: `{}` {} `{}` == {}", lhs, op, rhs, lhs <= rhs)
        return lhs <= rhs

    if op is Operator.GreaterThan:
        logging.debug("apply_operator: `{}` {} `{}` == {}", lhs, op, rhs, lhs > rhs)
        return lhs > rhs

    if op is Operator.GreaterThanOrEqualTo:
        logging.debug("apply_operator: `{}` {} `{}` == {}", lhs, op, rhs, lhs >= rhs)
        return lhs >= rhs

    raise TypeError(f"unknown comparison {op}")


@dataclass(frozen=True)
class ResolvedBaseClause:
    resolved_with: Optional[Any]
    resolved_items: Sequence[Any]
    result: bool

    def to_dict(self):
        return {
            "resolved_with": self.resolved_with,
            "resolved_items": [x for x in self.resolved_items],
            "result": self.result,
        }


@dataclass(frozen=True)
class AndClause:
    children: Tuple

    def to_dict(self):
        return {
            "type": "and-clause",
            "children": [c.to_dict() for c in self.children],
        }

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

    def compare_and_resolve_with(self, *, value: Any, map: Callable[[Any], Any]) -> ResolvedBaseClause:
        children = [c.compare_and_resolve_with(value=value, map=map) for c in self.children]
        result = all(c.result for c in children)

        return ResolvedAndClause(children=children, resolved_with=None, resolved_items=[], result=result)


@dataclass(frozen=True)
class ResolvedAndClause(AndClause, ResolvedBaseClause):
    def to_dict(self):
        return {
            **AndClause.to_dict(self),
            **ResolvedBaseClause.to_dict(self),
        }


@dataclass(frozen=True)
class OrClause:
    children: Tuple

    def to_dict(self):
        return {
            "type": "or-clause",
            "children": [c.to_dict() for c in self.children],
        }

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

    def compare_and_resolve_with(self, *, value: Any, map: Callable[[Any], Any]) -> ResolvedBaseClause:
        children = [c.compare_and_resolve_with(value=value, map=map) for c in self.children]
        result = any(c.result for c in children)

        return ResolvedOrClause(children=children, resolved_with=None, resolved_items=[], result=result)


@dataclass(frozen=True)
class ResolvedOrClause(OrClause, ResolvedBaseClause):
    def to_dict(self):
        return {
            **OrClause.to_dict(self),
            **ResolvedBaseClause.to_dict(self),
        }


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

    def compare_and_resolve_with(self, *, value: Any, map: Callable[[Any], Any]) -> ResolvedBaseClause:
        reduced_value, value_items = map(clause=self, value=value)
        result = self.compare(reduced_value)

        return ResolvedSingleClause(
            key=self.key,
            expected=self.expected,
            expected_verbatim=self.expected_verbatim,
            operator=self.operator,
            resolved_with=reduced_value,
            resolved_items=value_items,
            result=result,
        )


@dataclass(frozen=True)
class ResolvedSingleClause(ResolvedBaseClause, SingleClause):
    def to_dict(self):
        return {
            **SingleClause.to_dict(self),
            **ResolvedBaseClause.to_dict(self),
        }


def str_clause(clause) -> str:
    if not isinstance(clause, dict):
        return str_clause(clause.to_dict())

    if clause["type"] == "single-clause":
        if clause.get('resolved_with', None) is not None:
            resolved = f" ({clause.get('resolved_with', None)}; {sorted(clause.get('resolved_items', []))})"
        else:
            resolved = ""

        if clause['expected'] != clause['expected_verbatim']:
            postscript = f" (via \"{clause['expected_verbatim']}\")"
        else:
            postscript = ""

        return f"\"{clause['key']}\"{resolved} {clause['operator']} \"{clause['expected']}\"{postscript}"
    elif clause["type"] == "or-clause":
        return f'({" or ".join(str_clause(c) for c in clause["children"])})'
    elif clause["type"] == "and-clause":
        return f'({" and ".join(str_clause(c) for c in clause["children"])})'

    raise Exception('not a clause')


Clause = Union[AndClause, OrClause, SingleClause]
ResolvedClause = Union[ResolvedAndClause, ResolvedOrClause, ResolvedSingleClause]
