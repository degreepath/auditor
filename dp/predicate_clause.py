"""Populates a CompoundPredicate instance from an area specification.

## Examples

> where: {course: {$eq: AMCON 101}}
< Predicate(key=course, operator=eq, value=AMCON 101)

> where: {$or: [{course: {$eq: AMCON 101}}, {course: {$eq: AMCON 201}}]}
< CompoundPredicate(
    mode=.or,
    subpredicates=[
        Predicate(key=course, operator=eq, value=AMCON 101),
        Predicate(key=course, operator=eq, value=AMCON 201),
    ]
)

> where: {$or: [
    {course: {$eq: AMCON 101}},
    {$if: {has-ip-course: AMCON 101}, $then: {course: {$eq: AMCON 201}}},
]}
< CompoundPredicate(
    mode=.or,
    subpredicates=[
        Predicate(key=course, operator=eq, value=AMCON 101),
        ConditionalPredicate(
            condition=PredicateExpression(
                function=has-ip-course,
                arguments=[AMCON 101],
                result=True,
            )
            when_true=Predicate(key=course, operator=eq, value=AMCON 201),
            when_false=None,
        ),
    ]
)
<<< Given courses matching
<<< course = AMCON 101
<<< or, if AMCON 101 is in-progress, course = AMCON 201

> where: {$or: [
    {course: {$eq: AMCON 101}},
    {
        $if: {
            $and: [{has-ip-course: AMCON 101}, {has-area-code: '130'}],
        },
        $then: {course: {$eq: AMCON 201}},
    },
]}
< CompoundPredicate(
    mode=.or,
    subpredicates=[
        Predicate(key=course, operator=eq, value=AMCON 101),
        ConditionalPredicate(
            condition=CompoundPredicateExpression(
                mode=.and,
                expressions=[
                    PredicateExpression(
                        function=has-ip-course,
                        arguments=('AMCON 101',),
                        result=True,
                    ),
                    PredicateExpression(
                        function=has-area-code,
                        arguments=('130',),
                        result=False,
                    ),
                ],
                result=False,
            )
            when_true=Predicate(key=course, operator=eq, value=AMCON 201),
            when_false=None,
        ),
    ]
)
<<< Given courses matching
<<< course = AMCON 101
<<< or, if AMCON 101 is in-progress, course = AMCON 201
"""

from typing import Dict, Sequence, Optional, Any, Mapping, Union, Tuple, Callable, TYPE_CHECKING
from collections.abc import Iterable
from decimal import Decimal
from functools import lru_cache
import logging

import attr

from .constants import Constants
from .data.course_enums import GradeOption, GradeCode
from .data_type import DataType
from .op import Operator, apply_operator
from .clause_helpers import stringify_expected, flatten
from .data.clausable import Clausable
from .conditional_expression import load_predicate_expression, SomePredicateExpression

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext

logger = logging.getLogger(__name__)
CACHE_SIZE = 2048

ONE_POINT_OH = Decimal(1)
ZERO_POINT_OH = Decimal(0)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateCompoundAnd:
    predicates: Tuple['SomePredicate', ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred--and",
            "predicates": [c.to_dict() for c in self.predicates],
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.predicates:
            c.validate(ctx=ctx)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: Clausable) -> bool:
        return all(p.apply(to) for p in self.predicates)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateCompoundOr:
    predicates: Tuple['SomePredicate', ...] = tuple()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred--or",
            "predicates": [c.to_dict() for c in self.predicates],
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        for c in self.predicates:
            c.validate(ctx=ctx)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: Clausable) -> bool:
        return any(p.apply(to) for p in self.predicates)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateNot:
    predicate: 'SomePredicate'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred--not",
            "predicate": self.predicate.to_dict(),
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        self.predicate.validate(ctx=ctx)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: Clausable) -> bool:
        return not self.predicate.apply(to)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class ConditionalPredicate:
    condition: SomePredicateExpression
    when_true: 'SomePredicate'
    when_false: Optional['SomePredicate']

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred--if",
            "condition": self.condition.to_dict(),
            "when_true": self.when_true.to_dict(),
            "when_false": self.when_false.to_dict() if self.when_false else None,
        }

    def validate(self, *, ctx: 'RequirementContext') -> None:
        self.condition.validate(ctx=ctx)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: Clausable) -> bool:
        if self.condition.result:
            return self.when_true.apply(to)
        elif self.when_false is not None:
            return self.when_false.apply(to)
        else:
            return False


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class Predicate:
    key: str
    expected: Any
    expected_verbatim: Any
    operator: Operator
    during_covid: Optional[Any]

    @staticmethod
    def from_args(
        key: str = "???",
        expected: Any = None,
        expected_verbatim: Any = None,
        operator: Operator = Operator.EqualTo,
        during_covid: Optional[Any] = None,
    ) -> 'Predicate':
        return Predicate(
            key=key,
            expected=expected,
            expected_verbatim=expected_verbatim,
            operator=operator,
            during_covid=during_covid,
        )

    def to_dict(self) -> Dict[str, Any]:
        expected = stringify_expected(self.expected)
        expected_verbatim = stringify_expected(self.expected_verbatim)

        as_dict = {
            "type": "predicate",
            "key": self.key,
            "expected": expected,
            "operator": self.operator.name,
        }

        if expected != expected_verbatim:
            as_dict["expected_verbatim"] = expected_verbatim

        return as_dict

    def override_expected(self, value: Decimal) -> 'Predicate':
        return attr.evolve(self, expected=value, expected_verbatim=str(value))

    def validate(self, *, ctx: 'RequirementContext') -> None:
        pass

    @lru_cache(CACHE_SIZE)
    def compare(self, to_value: Any) -> bool:
        return apply_operator(lhs=to_value, op=self.operator, rhs=self.expected)

    @lru_cache(CACHE_SIZE)
    def compare_in_covid(self, to_value: Any) -> bool:
        if self.during_covid is None and self.during_covid != self.expected:
            return self.compare(to_value)
        return apply_operator(lhs=to_value, op=self.operator, rhs=self.during_covid)

    @lru_cache(CACHE_SIZE)
    def apply(self, to: Clausable) -> bool:
        return to.apply_predicate(self)


SomePredicate = Union[
    'PredicateCompoundAnd',
    'PredicateCompoundOr',
    'PredicateNot',
    ConditionalPredicate,
    Predicate,
]


def load_predicate(
    data: Dict[str, Any],
    *,
    mode: DataType,
    c: Constants,
    ctx: 'RequirementContext',
) -> SomePredicate:
    if not isinstance(data, Mapping):
        raise Exception(f'expected {data} to be a dictionary')

    if "$and" in data:
        # ensure that the data looks like {$and: []}, with no extra keys
        assert len(data.keys()) == 1
        predicates = tuple(load_predicate(p, c=c, ctx=ctx, mode=mode) for p in data['$and'])
        # ensure that, after checking the conditionals, that we have at least one clause
        assert len(predicates) >= 1
        return PredicateCompoundAnd(predicates=predicates)

    elif "$or" in data:
        # ensure that the data looks like {$or: []}, with no extra keys
        assert len(data.keys()) == 1
        predicates = tuple(load_predicate(p, c=c, ctx=ctx, mode=mode) for p in data['$or'])
        # ensure that, after checking the conditionals, that we have at least one clause
        assert len(predicates) >= 1
        return PredicateCompoundOr(predicates=predicates)

    elif "$not" in data:
        # ensure that the data looks like {$not: {}}, with no extra keys
        assert len(data.keys()) == 1
        predicate = load_predicate(data['$not'], c=c, ctx=ctx, mode=mode)
        return PredicateNot(predicate=predicate)

    elif "$if" in data:
        assert ctx, '$if clauses are not allowed here (no RequirementContext provided)'

        condition = load_predicate_expression(data['$if'], ctx=ctx)
        when_true = load_predicate(data['$then'], c=c, ctx=ctx, mode=mode)
        when_false = None
        if data.get('$else', None) is not None:
            when_false = load_predicate(data['$else'], c=c, ctx=ctx, mode=mode)

        return ConditionalPredicate(condition=condition, when_true=when_true, when_false=when_false)

    else:
        # assert len(data.keys()) == 1, "only one key allowed in single-clauses"

        clauses = tuple(
            load_single_predicate(key=key, value=value, c=c, mode=mode, ctx=ctx)
            for key, value in data.items()
        )

        if len(clauses) == 1:
            return clauses[0]

        return PredicateCompoundAnd(predicates=clauses)


def load_single_predicate(
    *,
    key: str,
    value: Dict,
    mode: DataType,
    c: Constants,
    ctx: 'RequirementContext',
    forbid: Sequence[Operator] = tuple(),
) -> Predicate:
    assert isinstance(value, Dict), TypeError(f'expected {value!r} to be a dictionary')

    if mode is DataType.Course:
        assert key in {'subject', 'attributes', 'course', 'number', 'gereqs'}
    elif mode is DataType.Area:
        assert key in {'name', 'type'}

    operators = [k for k in value.keys() if Operator.is_operator(k)]
    assert len(operators) == 1, ValueError(f"there must be only one operator in {value!r}")
    op = operators[0]
    operator = Operator(op)
    assert operator not in forbid, ValueError(f'operator {operator!r} is forbidden here - {forbid}')

    expected_value, expected_verbatim = load_expected_value(key=key, value=value, op=op, c=c)

    expected_value_covid = None
    if '$during_covid' in value:
        expected_value_covid, _ = load_expected_value(key=key, value=value, op='$during_covid', c=c)
        assert expected_value_covid is not None

    # forbid all null values in tuples or single-value clauses
    if operator in (Operator.In, Operator.NotIn):
        assert all(v is not None for v in expected_value)
    else:
        assert expected_value is not None

    return Predicate(
        key=key,
        expected=expected_value,
        operator=operator,
        expected_verbatim=expected_verbatim,
        during_covid=expected_value_covid,
    )


def load_expected_value(*, key: str, value: Dict, op: str, c: Constants) -> Tuple[Any, Any]:
    expected_value = value[op]
    if isinstance(expected_value, list):
        expected_value = tuple(expected_value)
    elif isinstance(expected_value, Iterable) and type(expected_value) != str:
        raise TypeError(f'unexpected type {type(expected_value)} for {expected_value!r}')
    elif isinstance(expected_value, float):
        raise TypeError(f'expected_value must not be a float: {expected_value!r}')

    expected_verbatim = expected_value

    allowed_types = (bool, str, tuple, int, Decimal)
    assert type(expected_value) in allowed_types, \
        ValueError(f"expected_value should be one of {allowed_types!r}, not {type(expected_value)}")

    if type(expected_value) == str:
        expected_value = c.get_by_name(expected_value)
    elif isinstance(expected_value, tuple):
        expected_value = tuple(c.get_by_name(v) for v in expected_value)
        expected_value = tuple(flatten(expected_value))

    if key in clause_value_process:
        expected_value = clause_value_process[key](expected_value)

    return expected_value, expected_verbatim


def predicate_value_map__grade(expected_value: Any) -> Union[GradeCode, Tuple[GradeCode, ...]]:
    if not type(expected_value) is str and isinstance(expected_value, Iterable):
        return tuple(GradeCode(v) for v in expected_value)
    else:
        return GradeCode(expected_value)


def predicate_value_map__grade_option(expected_value: Any) -> GradeOption:
    return GradeOption(expected_value)


def predicate_value_map__credits(expected_value: Any) -> Decimal:
    return Decimal(expected_value)


def predicate_value_map__gpa(expected_value: Any) -> Decimal:
    return Decimal(expected_value)


clause_value_process: Mapping[
    str,
    Callable[[Any], Union[GradeOption, GradeCode, Tuple[GradeCode, ...], Decimal, Tuple[Decimal, ...]]]
] = {
    'grade': predicate_value_map__grade,
    'grade_option': predicate_value_map__grade_option,
    'credits': predicate_value_map__credits,
    'gpa': predicate_value_map__gpa,
}

ProcessedClauseValue = Union[Any, GradeOption, GradeCode, Tuple[GradeCode, ...], Decimal, Tuple[Decimal, ...]]
