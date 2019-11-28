from collections.abc import Iterable
from typing import Union, List, Set, Tuple, Dict, Any, Mapping, Callable, Optional, Iterator, Sequence, TYPE_CHECKING
import logging
from decimal import Decimal, InvalidOperation
import abc
import attr

from .constants import Constants
from .lib import str_to_grade_points
from .operator import Operator, apply_operator, str_operator
from .data.course_enums import GradeOption, GradeCode
from .status import ResultStatus
from .apply_clause import apply_clause_to_assertion
from functools import lru_cache

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext
    from .data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)
CACHE_SIZE = 2048


@attr.s(auto_attribs=True, slots=True)
class BaseClause(abc.ABC):
    @lru_cache(CACHE_SIZE)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'Clause':
        raise NotImplementedError(f'must define a compare_and_resolve_with(value) method')

    @lru_cache(CACHE_SIZE)
    def apply(self, to: 'Clausable') -> bool:
        raise NotImplementedError(f'must define an apply(to=) method')


@attr.s(auto_attribs=True, slots=True)
class ClauseWithResult:
    result: ResultStatus = ResultStatus.Pending

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.value,
            "rank": str(self.rank()),
            "max_rank": str(self.max_rank()),
        }

    @lru_cache(CACHE_SIZE)
    def rank(self) -> Union[int, Decimal]:
        if self.ok():
            return 1

        return 0

    @lru_cache(CACHE_SIZE)
    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return 1

    @lru_cache(CACHE_SIZE)
    def in_progress(self) -> bool:
        raise NotImplementedError(f'must define an in_progress() method')

    @lru_cache(CACHE_SIZE)
    def ok(self) -> bool:
        raise NotImplementedError(f'must define an ok() method')

    @lru_cache(CACHE_SIZE)
    def status(self) -> ResultStatus:
        if self.in_progress():
            return ResultStatus.InProgress

        if self.ok():
            return ResultStatus.Pass

        return ResultStatus.Pending


@attr.s(auto_attribs=True, slots=True)
class ResolvedClause(ClauseWithResult):
    resolved_with: Optional[Any] = None
    resolved_items: Tuple[Any, ...] = tuple()
    resolved_clbids: Tuple[str, ...] = tuple()
    in_progress_clbids: Tuple[str, ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "resolved_with": str(self.resolved_with) if self.resolved_with is not None else self.resolved_with,
            "resolved_items": [str(x) if isinstance(x, Decimal) else x for x in self.resolved_items],
            "resolved_clbids": [x for x in self.resolved_clbids],
            "in_progress_clbids": [x for x in self.in_progress_clbids],
        }


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class AndClause(BaseClause, ClauseWithResult):
    children: Tuple['Clause', ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "type": "and-clause",
            "children": [c.to_dict() for c in self.children],
            "hash": str(hash(self.children)),
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.children:
            c.validate(ctx=ctx)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: 'Clausable') -> bool:
        return all(subclause.apply(to) for subclause in self.children)

    @lru_cache(CACHE_SIZE)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'AndClause':  # type: ignore
        children = tuple(c.compare_and_resolve_with(value=value) for c in self.children)

        if any(c.in_progress() for c in children):
            # if there are any in-progress children
            result = ResultStatus.InProgress
        elif all(c.ok() for c in children):
            # if all children are OK
            result = ResultStatus.Pass
        elif any(c.ok() for c in children):
            # if the number of done items is not fully complete
            result = ResultStatus.InProgress
        else:
            # otherwise
            result = ResultStatus.Pending

        return AndClause(children=children, result=result)

    @lru_cache(CACHE_SIZE)
    def ok(self) -> bool:
        return all(c.ok() for c in self.children)

    @lru_cache(CACHE_SIZE)
    def in_progress(self) -> bool:
        return any(c.in_progress() for c in self.children)

    @lru_cache(CACHE_SIZE)
    def rank(self) -> Union[int, Decimal]:
        return sum(c.rank() for c in self.children)

    @lru_cache(CACHE_SIZE)
    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return sum(c.max_rank() for c in self.children)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class OrClause(BaseClause, ClauseWithResult):
    children: Tuple['Clause', ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "type": "or-clause",
            "children": [c.to_dict() for c in self.children],
            "hash": str(hash(self.children)),
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.children:
            c.validate(ctx=ctx)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: 'Clausable') -> bool:
        return any(subclause.apply(to) for subclause in self.children)

    @lru_cache(CACHE_SIZE)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'OrClause':  # type: ignore
        children = tuple(c.compare_and_resolve_with(value=value) for c in self.children)

        if any(c.in_progress() for c in children):
            # if there are any in-progress children
            result = ResultStatus.InProgress
        elif any(c.ok() for c in children):
            # if any children are OK
            result = ResultStatus.Pass
        else:
            # otherwise
            result = ResultStatus.Pending

        return OrClause(children=children, result=result)

    @lru_cache(CACHE_SIZE)
    def ok(self) -> bool:
        return any(c.ok() for c in self.children)

    @lru_cache(CACHE_SIZE)
    def in_progress(self) -> bool:
        return any(c.in_progress() for c in self.children)

    @lru_cache(CACHE_SIZE)
    def rank(self) -> Union[int, Decimal]:
        return sum(c.rank() for c in self.children)

    @lru_cache(CACHE_SIZE)
    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return sum(c.rank() if c.ok() else c.max_rank() for c in self.children)


def stringify_expected(expected: Any) -> Any:
    if isinstance(expected, tuple):
        return tuple(stringify_expected(e) for e in expected)

    if isinstance(expected, (GradeOption, GradeCode)):
        return expected.value

    elif isinstance(expected, Decimal):
        return str(expected)

    return expected


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class SingleClause(BaseClause, ResolvedClause):
    key: str = "???"
    expected: Any = None
    expected_verbatim: Any = None
    operator: Operator = Operator.EqualTo
    label: Optional[str] = None
    at_most: bool = False
    treat_in_progress_as_pass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "type": "single-clause",
            "key": self.key,
            "expected": stringify_expected(self.expected),
            "expected_verbatim": stringify_expected(self.expected_verbatim),
            "operator": self.operator.name,
            "label": self.label,
            "ip_as_passing": self.treat_in_progress_as_pass,
            "hash": str(hash((self.key, self.expected, self.operator))),
        }

    @staticmethod
    def load(key: str, value: Any, c: Constants, forbid: Sequence[Operator] = tuple()) -> 'SingleClause':
        assert isinstance(value, Dict), Exception(f'expected {value} to be a dictionary')

        operators = [k for k in value.keys() if k.startswith('$')]
        assert len(operators) == 1, f"{value}"
        op = operators[0]
        operator = Operator(op)
        assert operator not in forbid, ValueError(f'operator {operator} is forbidden here - {forbid}')

        expected_value = value[op]
        if isinstance(expected_value, list):
            expected_value = tuple(expected_value)
        elif isinstance(expected_value, float):
            expected_value = Decimal(expected_value)

        expected_verbatim = expected_value

        key_lookup = {
            "subjects": "subject",
            "attribute": "attributes",
            "gereq": "gereqs",
        }
        key = key_lookup.get(key, key)

        allowed_types = (bool, str, tuple, int, Decimal)
        assert type(expected_value) in allowed_types, f"expected_value should be {allowed_types}, not {type(expected_value)}"

        if type(expected_value) == str:
            expected_value = c.get_by_name(expected_value)
        elif isinstance(expected_value, Iterable):
            expected_value = tuple(c.get_by_name(v) for v in expected_value)

        expected_value = process_clause_value(expected_value, key=key)

        if operator in (Operator.In, Operator.NotIn):
            assert all(v is not None for v in expected_value)
        else:
            assert expected_value is not None

        at_most = value.get('at_most', False)
        assert type(at_most) is bool

        return SingleClause(
            key=key,
            expected=expected_value,
            operator=operator,
            expected_verbatim=expected_verbatim,
            at_most=at_most,
            label=value.get('label', None),
            treat_in_progress_as_pass=value.get('treat_in_progress_as_pass', False),
        )

    def override_expected(self, value: Decimal) -> 'SingleClause':
        return attr.evolve(self, expected=value, expected_verbatim=str(value))

    @lru_cache(CACHE_SIZE)
    def ok(self) -> bool:
        return self.result is ResultStatus.Pass

    @lru_cache(CACHE_SIZE)
    def in_progress(self) -> bool:
        return self.result is ResultStatus.InProgress

    @lru_cache(CACHE_SIZE)
    def rank(self) -> Union[int, Decimal]:
        if self.result is ResultStatus.Pass:
            return 1

        if self.operator not in (Operator.LessThan, Operator.LessThanOrEqualTo):
            if self.resolved_with is not None and type(self.resolved_with) in (int, Decimal):
                if type(self.expected) in (int, Decimal):
                    if self.expected != 0:
                        resolved = Decimal(self.resolved_with) / Decimal(self.expected)
                        return min(Decimal(1), resolved)

        return 0

    @lru_cache(CACHE_SIZE)
    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return 1

    def __repr__(self) -> str:
        return f"Clause({str_clause(self)})"

    def validate(self, *, ctx: 'RequirementContext') -> None:
        pass

    @lru_cache(CACHE_SIZE)
    def apply(self, to: 'Clausable') -> bool:
        return to.apply_single_clause(self)

    @lru_cache(CACHE_SIZE)
    def compare(self, to_value: Any) -> bool:
        return apply_operator(lhs=to_value, op=self.operator, rhs=self.expected)

    @lru_cache(CACHE_SIZE)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'SingleClause':  # type: ignore
        calculated_result = apply_clause_to_assertion(self, value)

        reduced_value = calculated_result.value
        value_items = calculated_result.data
        clbids = calculated_result.clbids()
        ip_clbids = calculated_result.ip_clbids()

        # if we have `treat_in_progress_as_pass` set, we skip the ip_clbids check entirely
        if ip_clbids and self.treat_in_progress_as_pass is False:
            result = ResultStatus.InProgress
        elif apply_operator(lhs=reduced_value, op=self.operator, rhs=self.expected) is True:
            result = ResultStatus.Pass
        elif clbids:
            # we aren't "passing", but we've also got at least something
            # counting towards this clause, so we'll mark it as in-progress.
            result = ResultStatus.InProgress
        else:
            result = ResultStatus.Pending

        return SingleClause(
            key=self.key,
            expected=self.expected,
            expected_verbatim=self.expected_verbatim,
            operator=self.operator,
            at_most=self.at_most,
            label=self.label,
            resolved_with=reduced_value,
            resolved_items=tuple(value_items),
            resolved_clbids=clbids,
            in_progress_clbids=ip_clbids,
            result=result,
            treat_in_progress_as_pass=self.treat_in_progress_as_pass,
        )

    def input_size_range(self, *, maximum: int) -> Iterator[int]:
        if type(self.expected) is not int:
            raise TypeError('cannot find a range of values for a non-integer clause: %s', type(self.expected))

        if self.operator == Operator.EqualTo or (self.operator == Operator.GreaterThanOrEqualTo and self.at_most is True):
            if maximum < self.expected:
                yield maximum
                return
            yield from range(self.expected, self.expected + 1)

        elif self.operator == Operator.NotEqualTo:
            # from 0-maximum, skipping "expected"
            yield from range(0, self.expected)
            yield from range(self.expected + 1, max(self.expected + 1, maximum + 1))

        elif self.operator == Operator.GreaterThanOrEqualTo:
            if maximum < self.expected:
                yield maximum
                return
            yield from range(self.expected, max(self.expected + 1, maximum + 1))

        elif self.operator == Operator.GreaterThan:
            if maximum < self.expected:
                yield maximum
                return
            yield from range(self.expected + 1, max(self.expected + 2, maximum + 1))

        elif self.operator == Operator.LessThan:
            yield from range(0, self.expected)

        elif self.operator == Operator.LessThanOrEqualTo:
            yield from range(0, self.expected + 1)

        else:
            raise TypeError('unsupported operator for ranges %s', self.operator)


def process_clause__grade(expected_value: Any) -> Union[Decimal, Tuple[Decimal, ...]]:
    if type(expected_value) is str:
        try:
            return Decimal(expected_value)
        except InvalidOperation:
            return str_to_grade_points(expected_value)
    elif isinstance(expected_value, Iterable):
        return tuple(
            str_to_grade_points(v) if type(v) is str else Decimal(v)
            for v in expected_value
        )
    else:
        return Decimal(expected_value)


def process_clause__grade_option(expected_value: Any) -> GradeOption:
    return GradeOption(expected_value)


def process_clause__credits(expected_value: Any) -> Decimal:
    return Decimal(expected_value)


def process_clause__gpa(expected_value: Any) -> Decimal:
    return Decimal(expected_value)


clause_value_process: Mapping[str, Callable[[Sequence[Any]], Union[GradeOption, Decimal, Tuple[Decimal, ...]]]] = {
    'grade': process_clause__grade,
    'grade_option': process_clause__grade_option,
    'credits': process_clause__credits,
    'gpa': process_clause__gpa,
}


def process_clause_value(expected_value: Any, *, key: str) -> Union[Any, GradeOption, Decimal, Tuple[Decimal, ...]]:
    if key in clause_value_process:
        return clause_value_process[key](expected_value)

    return expected_value


def str_clause(clause: Union[Dict[str, Any], 'Clause']) -> str:
    if not isinstance(clause, dict):
        return str_clause(clause.to_dict())

    if clause["type"] == "single-clause":
        resolved_with = clause.get('resolved_with', None)
        if resolved_with is not None:
            resolved = f" ({repr(resolved_with)})"
        else:
            resolved = ""

        if clause['expected'] != clause['expected_verbatim']:
            postscript = f" (via {repr(clause['expected_verbatim'])})"
        else:
            postscript = ""

        label = clause['label']
        if label:
            postscript += f' [label: "{label}"]'

        op = str_operator(clause['operator'])

        return f'"{clause["key"]}"{resolved} {op} "{clause["expected"]}"{postscript}'
    elif clause["type"] == "or-clause":
        return f'({" or ".join(str_clause(c) for c in clause["children"])})'
    elif clause["type"] == "and-clause":
        return f'({" and ".join(str_clause(c) for c in clause["children"])})'

    raise Exception('not a clause')


def get_resolved_items(clause: Union[Dict[str, Any], 'Clause']) -> str:
    if not isinstance(clause, dict):
        return get_resolved_items(clause.to_dict())

    if clause["type"] == "single-clause":
        resolved_with = clause.get('resolved_with', None)
        if resolved_with is not None:
            return str(sorted(clause.get('resolved_items', [])))
        else:
            return ""
    elif clause["type"] == "or-clause":
        return f'({" or ".join(get_resolved_items(c) for c in clause["children"])})'
    elif clause["type"] == "and-clause":
        return f'({" and ".join(get_resolved_items(c) for c in clause["children"])})'

    raise Exception('not a clause')


def get_resolved_clbids(clause: Union[Dict[str, Any], 'Clause']) -> List[str]:
    if not isinstance(clause, dict):
        return get_resolved_clbids(clause.to_dict())

    if clause["type"] == "single-clause":
        return sorted(clause['resolved_clbids'])
    elif clause["type"] == "or-clause":
        return [clbid for c in clause["children"] for clbid in get_resolved_clbids(c)]
    elif clause["type"] == "and-clause":
        return [clbid for c in clause["children"] for clbid in get_resolved_clbids(c)]

    raise Exception('not a clause')


def get_in_progress_clbids(clause: Union[Dict[str, Any], 'Clause']) -> Set[str]:
    if not isinstance(clause, dict):
        return get_in_progress_clbids(clause.to_dict())

    if clause["type"] == "single-clause":
        return set(clause['in_progress_clbids'])
    elif clause["type"] == "or-clause":
        return set(clbid for c in clause["children"] for clbid in get_in_progress_clbids(c))
    elif clause["type"] == "and-clause":
        return set(clbid for c in clause["children"] for clbid in get_in_progress_clbids(c))

    raise Exception('not a clause')


Clause = Union[AndClause, OrClause, SingleClause]
