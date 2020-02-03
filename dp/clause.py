from typing import Union, Tuple, Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal
import logging

import attr

from .operator import Operator, apply_operator
from .data.course_enums import GradeOption, GradeCode
from .status import ResultStatus
from .stringify import str_clause
from functools import lru_cache

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext
    from .data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)
CACHE_SIZE = 2048


@lru_cache(CACHE_SIZE)
def apply_clause(clause: 'Clause', to: 'Clausable') -> bool:
    if isinstance(clause, AndClause):
        return all(apply_clause(subclause, to=to) for subclause in clause.children)
    elif isinstance(clause, OrClause):
        return any(apply_clause(subclause, to=to) for subclause in clause.children)
    else:
        return to.apply_single_clause(clause)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class AndClause:
    children: Tuple['Clause', ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "and-clause",
            "children": [c.to_dict() for c in self.children],
            "hash": str(hash(self.children)),
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.children:
            c.validate(ctx=ctx)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class OrClause:
    children: Tuple['Clause', ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "or-clause",
            "children": [c.to_dict() for c in self.children],
            "hash": str(hash(self.children)),
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.children:
            c.validate(ctx=ctx)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class SingleClause:
    key: str
    expected: Any
    expected_verbatim: Any
    operator: Operator
    label: Optional[str]
    at_most: bool
    treat_in_progress_as_pass: bool
    state: ResultStatus

    @staticmethod
    def from_args(
        key: str = "???",
        expected: Any = None,
        expected_verbatim: Any = None,
        operator: Operator = Operator.EqualTo,
        label: Optional[str] = None,
        at_most: bool = False,
        treat_in_progress_as_pass: bool = False,
        state: ResultStatus = ResultStatus.Empty,
    ) -> 'SingleClause':
        return SingleClause(
            key=key,
            expected=expected,
            expected_verbatim=expected_verbatim,
            operator=operator,
            label=label,
            at_most=at_most,
            treat_in_progress_as_pass=treat_in_progress_as_pass,
            state=state,
        )

    def __repr__(self) -> str:
        return f"Clause({str_clause(self.to_dict())})"

    def to_dict(self) -> Dict[str, Any]:
        status = self.status()
        rank, max_rank = self.rank()

        return {
            "type": "single-clause",
            "key": self.key,
            "expected": stringify_expected(self.expected),
            "expected_verbatim": stringify_expected(self.expected_verbatim),
            "operator": self.operator.name,
            "label": self.label,
            "ip_as_passing": self.treat_in_progress_as_pass,
            "hash": str(hash((self.key, self.expected, self.operator))),
            "result": self.state.value,
            "rank": str(rank),
            "max_rank": str(max_rank),
            "status": status.value,
        }

    def override_expected(self, value: Decimal) -> 'SingleClause':
        return attr.evolve(self, expected=value, expected_verbatim=str(value))

    def status(self) -> ResultStatus:
        return self.state

    def rank(self) -> Tuple[Decimal, Decimal]:
        if self.state in (ResultStatus.Done, ResultStatus.Waived):
            return Decimal(1), Decimal(1)

        return Decimal(0), Decimal(1)

    def validate(self, *, ctx: 'RequirementContext') -> None:
        pass

    @lru_cache(CACHE_SIZE)
    def apply(self, to: 'Clausable') -> bool:
        return to.apply_single_clause(self)

    @lru_cache(CACHE_SIZE)
    def compare(self, to_value: Any) -> bool:
        return apply_operator(lhs=to_value, op=self.operator, rhs=self.expected)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class ResolvedSingleClause(SingleClause):
    resolved_with: Union[int, Decimal]
    resolved_items: Union[Tuple[str, ...], Tuple[Decimal, ...]] = tuple()
    resolved_clbids: Tuple[str, ...] = tuple()

    def __repr__(self) -> str:
        return f"ResolvedClause({str_clause(self.to_dict())})"

    @staticmethod
    def from_clause(
        clause: SingleClause,
        *,
        status: ResultStatus,
        resolved_with: Union[int, Decimal],
        resolved_items: Union[Tuple[str, ...], Tuple[Decimal, ...]],
        resolved_clbids: Tuple[str, ...] = tuple(),
    ) -> 'ResolvedSingleClause':
        return ResolvedSingleClause(
            key=clause.key,
            expected=clause.expected,
            expected_verbatim=clause.expected_verbatim,
            operator=clause.operator,
            at_most=clause.at_most,
            label=clause.label,
            resolved_with=resolved_with,
            resolved_items=resolved_items,
            resolved_clbids=resolved_clbids,
            state=status,
            treat_in_progress_as_pass=clause.treat_in_progress_as_pass,
        )

    @staticmethod
    def as_overridden(clause: SingleClause) -> 'ResolvedSingleClause':
        return ResolvedSingleClause(
            key=clause.key,
            expected=clause.expected,
            expected_verbatim=clause.expected_verbatim,
            operator=clause.operator,
            at_most=clause.at_most,
            label=clause.label,
            resolved_with=Decimal(0),
            resolved_items=tuple(),
            resolved_clbids=tuple(),
            state=ResultStatus.Waived,
            treat_in_progress_as_pass=clause.treat_in_progress_as_pass,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "resolved_with": str(self.resolved_with),
            "resolved_items": [stringify_expected(x) for x in self.resolved_items],
            "resolved_clbids": [x for x in self.resolved_clbids],
        }

    def rank(self) -> Tuple[Decimal, Decimal]:
        if self.state in (ResultStatus.Done, ResultStatus.Waived):
            return Decimal(1), Decimal(1)

        if self.operator not in (Operator.LessThan, Operator.LessThanOrEqualTo):
            if type(self.expected) in (int, Decimal) and self.expected != 0:
                resolved = Decimal(self.resolved_with) / Decimal(self.expected)
                return min(Decimal(1), resolved), Decimal(1)

        return Decimal(0), Decimal(1)


def stringify_expected(expected: Any) -> Any:
    if isinstance(expected, tuple):
        return tuple(stringify_expected(e) for e in expected)

    if isinstance(expected, (GradeOption, GradeCode)):
        return expected.value

    elif isinstance(expected, Decimal):
        return str(expected)

    return expected


Clause = Union[AndClause, OrClause, SingleClause]
