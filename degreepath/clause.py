from collections.abc import Mapping, Iterable
from typing import Union, List, Set, Tuple, Dict, Any, Optional, Iterator, Sequence, cast, TYPE_CHECKING
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

if TYPE_CHECKING:
    from .base.course import BaseCourseRule  # noqa: F401
    from .context import RequirementContext
    from .data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


def load_clause(
    data: Dict[str, Any],
    *,
    c: Constants,
    allow_boolean: bool = True,
    forbid: Sequence[Operator] = tuple(),
) -> 'Clause':
    if not isinstance(data, Mapping):
        raise Exception(f'expected {data} to be a dictionary')

    if not allow_boolean and ('$and' in data or '$or' in data):
        raise ValueError('$and / $or clauses are not allowed here')

    if "$and" in data:
        assert len(data.keys()) == 1
        return AndClause.load(data["$and"], c, allow_boolean, forbid)
    elif "$or" in data:
        assert len(data.keys()) == 1
        return OrClause.load(data["$or"], c, allow_boolean, forbid)

    assert len(data.keys()) == 1, "only one key allowed in single-clauses"

    clauses = tuple(SingleClause.load(key, value, c, forbid) for key, value in data.items())

    if len(clauses) == 1:
        return clauses[0]

    return AndClause(children=clauses)


@attr.s(auto_attribs=True, slots=True)
class _Clause(abc.ABC):
    @abc.abstractmethod
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'Clause':
        raise NotImplementedError(f'must define a compare_and_resolve_with(value) method')

    @abc.abstractmethod
    def apply(self, to: 'Clausable') -> bool:
        raise NotImplementedError(f'must define an apply(to=) method')


@attr.s(auto_attribs=True, slots=True)
class ResolvedClause:
    resolved_with: Optional[Any] = None
    resolved_items: Tuple[Any, ...] = tuple()
    resolved_clbids: Tuple[str, ...] = tuple()
    in_progress_clbids: Tuple[str, ...] = tuple()
    result: ResultStatus = ResultStatus.Pending

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resolved_with": str(self.resolved_with) if self.resolved_with is not None and type(self.resolved_with) is not str else self.resolved_with,
            "resolved_items": [str(x) if isinstance(x, Decimal) else x for x in self.resolved_items],
            "resolved_clbids": [x for x in self.resolved_clbids],
            "in_progress_clbids": [x for x in self.in_progress_clbids],
            "result": self.result.value,
            "rank": str(self.rank()),
            "max_rank": str(self.max_rank()),
        }

    def rank(self) -> Union[int, Decimal]:
        if self.ok():
            return 1

        return 0

    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return 1

    @abc.abstractmethod
    def in_progress(self) -> bool:
        raise NotImplementedError(f'must define an in_progress() method')

    @abc.abstractmethod
    def ok(self) -> bool:
        raise NotImplementedError(f'must define an ok() method')

    def status(self) -> ResultStatus:
        if self.in_progress():
            return ResultStatus.InProgress

        if self.ok():
            return ResultStatus.Pass

        return ResultStatus.Pending


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class AndClause(_Clause, ResolvedClause):
    children: Tuple = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "type": "and-clause",
            "children": [c.to_dict() for c in self.children],
            "hash": str(hash(self.children)),
        }

    @staticmethod
    def load(data: List[Dict], c: Constants, allow_boolean: bool = True, forbid: Sequence[Operator] = tuple()) -> 'AndClause':
        clauses = [load_clause(clause, c=c, allow_boolean=allow_boolean, forbid=forbid) for clause in data]
        return AndClause(children=tuple(clauses))

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.children:
            c.validate(ctx=ctx)

    @lru_cache(2048)
    def apply(self, to: 'Clausable') -> bool:
        return all(subclause.apply(to) for subclause in self.children)

    @lru_cache(2048)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'AndClause':
        children = tuple(c.compare_and_resolve_with(value=value) for c in self.children)

        if any(c.result is ResultStatus.InProgress for c in children):
            # if there are any in-progress children
            result = ResultStatus.InProgress
        elif all(c.result is ResultStatus.Pass for c in children):
            # if all children are OK
            result = ResultStatus.Pass
        elif 1 <= len([c.result is ResultStatus.Pass for c in children]) < len(self.children):
            # if the number of done items is not fully complete
            result = ResultStatus.InProgress
        else:
            # otherwise
            result = ResultStatus.Pending

        return AndClause(children=children, resolved_with=None, result=result)

    def ok(self) -> bool:
        return all(c.ok() for c in self.children)

    def in_progress(self) -> bool:
        return any(c.in_progress() for c in self.children)

    def rank(self) -> Union[int, Decimal]:
        return sum(c.rank() for c in self.children)

    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return sum(c.max_rank() for c in self.children)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class OrClause(_Clause, ResolvedClause):
    children: Tuple = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "type": "or-clause",
            "children": [c.to_dict() for c in self.children],
            "hash": str(hash(self.children)),
        }

    @staticmethod
    def load(data: Dict, c: Constants, allow_boolean: bool = True, forbid: Sequence[Operator] = tuple()) -> 'OrClause':
        clauses = [load_clause(clause, c=c, allow_boolean=allow_boolean, forbid=forbid) for clause in data]
        return OrClause(children=tuple(clauses))

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.children:
            c.validate(ctx=ctx)

    @lru_cache(2048)
    def apply(self, to: 'Clausable') -> bool:
        return any(subclause.apply(to) for subclause in self.children)

    @lru_cache(2048)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'OrClause':
        children = tuple(c.compare_and_resolve_with(value=value) for c in self.children)

        if any(c.result is ResultStatus.InProgress for c in children):
            # if there are any in-progress children
            result = ResultStatus.InProgress
        elif any(c.result is ResultStatus.Pass for c in children):
            # if any children are OK
            result = ResultStatus.Pass
        else:
            # otherwise
            result = ResultStatus.Pending

        return OrClause(children=children, resolved_with=None, result=result)

    def ok(self) -> bool:
        return any(c.ok() for c in self.children)

    def in_progress(self) -> bool:
        return any(c.in_progress() for c in self.children)

    def rank(self) -> Union[int, Decimal]:
        return sum(c.rank() for c in self.children)

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
class SingleClause(_Clause, ResolvedClause):
    key: str = "???"
    expected: Any = None
    expected_verbatim: Any = None
    operator: Operator = Operator.EqualTo
    at_most: bool = False
    treat_in_progress_as_pass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        expected = stringify_expected(self.expected)

        return {
            **super().to_dict(),
            "type": "single-clause",
            "key": self.key,
            "expected": expected,
            "expected_verbatim": self.expected_verbatim,
            "operator": self.operator.name,
            "ip_as_passing": self.treat_in_progress_as_pass,
            "hash": str(hash((self.key, self.expected, self.operator))),
        }

    @staticmethod  # noqa: C901
    def load(key: str, value: Any, c: Constants, forbid: Sequence[Operator] = tuple()) -> 'SingleClause':
        if not isinstance(value, Dict):
            raise Exception(f'expected {value} to be a dictionary')

        operators = [k for k in value.keys() if k.startswith('$')]

        assert len(operators) == 1, f"{value}"
        op = operators[0]

        at_most = value.get('at_most', False)
        assert type(at_most) is bool

        operator = Operator(op)
        expected_value = value[op]

        if operator in forbid:
            raise ValueError(f'operator {operator} is forbidden here')

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

        if operator is Operator.In or operator is Operator.NotIn:
            assert all(v is not None for v in expected_value)
        else:
            assert expected_value is not None

        if key == 'grade':
            if type(expected_value) is str:
                try:
                    expected_value = Decimal(expected_value)
                except InvalidOperation:
                    expected_value = str_to_grade_points(expected_value)
            elif isinstance(expected_value, Iterable):
                expected_value = tuple(
                    str_to_grade_points(v) if type(v) is str else Decimal(v)
                    for v in expected_value
                )
            else:
                expected_value = Decimal(expected_value)
        elif key == 'grade_option':
            expected_value = GradeOption(expected_value)
        elif key == 'credits':
            expected_value = Decimal(expected_value)
        elif key == 'gpa':
            expected_value = Decimal(expected_value)

        return SingleClause(
            key=key,
            expected=expected_value,
            operator=operator,
            expected_verbatim=expected_verbatim,
            at_most=at_most,
            treat_in_progress_as_pass=value.get('treat_in_progress_as_pass', False),
        )

    def override_expected(self, value: Decimal) -> 'SingleClause':
        return attr.evolve(self, expected=value, expected_verbatim=str(value))

    def ok(self) -> bool:
        return self.result is ResultStatus.Pass

    def in_progress(self) -> bool:
        return self.result is ResultStatus.InProgress

    @lru_cache(2048)
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

    def max_rank(self) -> Union[int, Decimal]:
        if self.ok():
            return self.rank()

        return 1

    def __repr__(self) -> str:
        return f"Clause({str_clause(self)})"

    def validate(self, *, ctx: 'RequirementContext') -> None:
        pass

    @lru_cache(2048)
    def apply(self, to: 'Clausable') -> bool:
        return to.apply_single_clause(self)

    @lru_cache(2048)
    def compare(self, to_value: Any) -> bool:
        return apply_operator(lhs=to_value, op=self.operator, rhs=self.expected)

    @lru_cache(2048)
    def compare_and_resolve_with(self, value: Tuple['Clausable', ...]) -> 'SingleClause':
        calculated_result = apply_clause_to_assertion(self, value)

        reduced_value = calculated_result.value
        value_items = calculated_result.data
        courses = calculated_result.courses

        clbids = tuple(c.clbid for c in courses)
        ip_clbids = tuple(c.clbid for c in courses if c.is_in_progress)

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
