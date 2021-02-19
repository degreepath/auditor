"""Populates a CompoundPredicateExpression instance from an area specification.

Examples
========

> {has-ip-course: AMCON 101}
< PredicateExpression(
    function=has-ip-course,
    arguments=[AMCON 101],
    result=True,
)

> {$and: [{has-ip-course: AMCON 101}, {has-area-code: '130'}]}
< CompoundPredicateExpression(
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
"""

from typing import Dict, Optional, Any, Mapping, Sequence, Iterable, Union, Tuple, TYPE_CHECKING
import logging
import enum

import attr

from .data.student import course_filter

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext
    from .data.course import CourseInstance

logger = logging.getLogger(__name__)

SomePredicateExpression = Union[
    'PredicateExpressionCompoundAnd',
    'PredicateExpressionCompoundOr',
    'PredicateExpressionNot',
    'PredicateExpression',
]

SomeDynamicPredicateExpression = Union[
    'DynamicPredicateExpression',
    'DynamicPredicateExpressionCompoundAnd',
    'DynamicPredicateExpressionCompoundOr',
]


@enum.unique
class PredicateExpressionFunction(enum.Enum):
    HasIpCourse = 'has-ip-course'
    HasCompletedCourse = 'has-completed-course'
    HasCourse = 'has-course'
    PassedProficiencyExam = 'passed-proficiency-exam'
    HasDeclaredAreaCode = 'has-declared-area-code'
    StudentHasCourseWithAttribute = 'student-has-course-with-attribute'
    HasOverrideException = 'has-override-exception'


@enum.unique
class DynamicPredicateExpressionFunction(enum.Enum):
    QueryHasCourseWithAttribute = 'query-has-course-with-attribute'
    QueryHasSingleCourseWithAttribute = 'query-has-single-course-with-attribute'


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateExpressionCompoundAnd:
    expressions: Tuple[SomePredicateExpression, ...] = tuple()
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return '$and' in data

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'PredicateExpressionCompoundAnd':
        # ensure that the data looks like {$and: []}, with no extra keys
        assert len(data.keys()) == 1
        assert type(data['$and']) == list
        clauses = tuple(load_predicate_expression(e, ctx=ctx) for e in data['$and'])
        return PredicateExpressionCompoundAnd(expressions=clauses, result=all(e.result for e in clauses))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-expr--and",
            "expressions": [c.to_dict() for c in self.expressions],
            "result": self.result,
        }

    def evaluate(self, *, ctx: 'RequirementContext') -> 'PredicateExpressionCompoundAnd':
        if self.result is not None:
            return self
        evaluated = tuple(e.evaluate(ctx=ctx) for e in self.expressions)
        return attr.evolve(self, expressions=evaluated, result=all(e.result for e in evaluated))


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateExpressionCompoundOr:
    expressions: Tuple[SomePredicateExpression, ...] = tuple()
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return '$or' in data

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'PredicateExpressionCompoundOr':
        # ensure that the data looks like {$or: []}, with no extra keys
        assert len(data.keys()) == 1
        assert type(data['$or']) == list
        clauses = tuple(load_predicate_expression(e, ctx=ctx) for e in data['$or'])
        return PredicateExpressionCompoundOr(expressions=clauses, result=any(e.result for e in clauses))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-expr--or",
            "expressions": [c.to_dict() for c in self.expressions],
            "result": self.result,
        }

    def evaluate(self, *, ctx: 'RequirementContext') -> 'PredicateExpressionCompoundOr':
        if self.result is not None:
            return self
        evaluated = tuple(e.evaluate(ctx=ctx) for e in self.expressions)
        return attr.evolve(self, expressions=evaluated, result=any(e.result for e in evaluated))


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateExpressionNot:
    expression: SomePredicateExpression
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return '$not' in data

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'PredicateExpressionNot':
        # ensure that the data looks like {$not: {}}, with no extra keys
        assert len(data.keys()) == 1
        expression = load_predicate_expression(data['$not'], ctx=ctx)
        return PredicateExpressionNot(expression=expression, result=not expression.result)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-expr--not",
            "expression": self.expression.to_dict(),
            "result": self.result,
        }

    def evaluate(self, *, ctx: 'RequirementContext') -> 'PredicateExpressionNot':
        if self.result is not None:
            return self
        evaluated = self.expression.evaluate(ctx=ctx)
        return attr.evolve(self, expression=evaluated, result=not evaluated.result)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class PredicateExpression:
    function: PredicateExpressionFunction
    argument: str
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        if len(data.keys()) != 1:
            return False

        try:
            function_name = list(data.keys())[0]
            PredicateExpressionFunction(function_name)
            return True
        except ValueError:
            return False

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'PredicateExpression':
        assert type(data) is dict, TypeError('predicate expressions must be dicts')
        assert len(data.keys()) == 1, ValueError("only one key allowed in predicate expressions")

        function_name = list(data.keys())[0]
        function = PredicateExpressionFunction(function_name)

        argument = data[function_name]

        assert type(argument) is str, \
            TypeError(f'invalid argument type for predicate expression {type(argument)}')

        result = evaluate_predicate_function(function, argument, ctx=ctx)

        return PredicateExpression(function=function, argument=argument, result=result)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-expr",
            "function": self.function.value,
            "argument": self.argument,
            "result": self.result,
        }

    def evaluate(self, *, ctx: 'RequirementContext') -> 'PredicateExpression':
        if self.result is not None:
            return self
        result = evaluate_predicate_function(self.function, self.argument, ctx=ctx)
        return attr.evolve(self, result=result)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class DynamicPredicateExpression:
    function: DynamicPredicateExpressionFunction
    argument: str
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        if len(data.keys()) != 1:
            return False

        try:
            function_name = list(data.keys())[0]
            DynamicPredicateExpressionFunction(function_name)
            return True
        except ValueError:
            return False

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'DynamicPredicateExpression':
        assert type(data) is dict, TypeError('predicate expressions must be dicts')
        assert len(data.keys()) == 1, ValueError("only one key allowed in predicate expressions")

        function_name = list(data.keys())[0]
        function = DynamicPredicateExpressionFunction(function_name)

        argument = data[function_name]

        assert type(argument) is str, \
            TypeError(f'invalid argument type for predicate expression {type(argument)}')

        return DynamicPredicateExpression(function=function, argument=argument, result=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-dyn-expr",
            "function": self.function.value,
            "argument": self.argument,
            "result": self.result,
        }

    def evaluate_against_data(self, *, data: Sequence['CourseInstance']) -> 'DynamicPredicateExpression':
        result = evaluate_dynamic_predicate_function(self.function, self.argument, data=data)
        return attr.evolve(self, result=result)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class DynamicPredicateExpressionCompoundAnd:
    expressions: Tuple[SomeDynamicPredicateExpression, ...] = tuple()
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return '$and' in data

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'DynamicPredicateExpressionCompoundAnd':
        # ensure that the data looks like {$and: []}, with no extra keys
        assert len(data.keys()) == 1
        assert type(data['$and']) == list
        clauses = tuple(load_dynamic_predicate_expression(e, ctx=ctx) for e in data['$and'])
        return DynamicPredicateExpressionCompoundAnd(expressions=clauses, result=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-dyn-expr--and",
            "expressions": [c.to_dict() for c in self.expressions],
            "result": self.result,
        }

    def evaluate_against_data(self, *, data: Sequence['CourseInstance']) -> 'DynamicPredicateExpressionCompoundAnd':
        if self.result is not None:
            return self
        evaluated = tuple(e.evaluate_against_data(data=data) for e in self.expressions)
        return attr.evolve(self, expressions=evaluated, result=all(e.result for e in evaluated))


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class DynamicPredicateExpressionCompoundOr:
    expressions: Tuple[SomeDynamicPredicateExpression, ...] = tuple()
    result: Optional[bool] = None

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return '$or' in data

    @staticmethod
    def load(data: Mapping, *, ctx: 'RequirementContext') -> 'DynamicPredicateExpressionCompoundOr':
        # ensure that the data looks like {$or: []}, with no extra keys
        assert len(data.keys()) == 1
        assert type(data['$or']) == list
        clauses = tuple(load_dynamic_predicate_expression(e, ctx=ctx) for e in data['$or'])
        return DynamicPredicateExpressionCompoundOr(expressions=clauses, result=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "pred-dyn-expr--or",
            "expressions": [c.to_dict() for c in self.expressions],
            "result": self.result,
        }

    def evaluate_against_data(self, *, data: Sequence['CourseInstance']) -> 'DynamicPredicateExpressionCompoundOr':
        if self.result is not None:
            return self
        evaluated = tuple(e.evaluate_against_data(data=data) for e in self.expressions)
        return attr.evolve(self, expressions=evaluated, result=any(e.result for e in evaluated))


def evaluate_predicate_function(function: PredicateExpressionFunction, argument: str, *, ctx: 'RequirementContext') -> bool:
    logger.debug('evaluate: (%r %r)', function, argument)
    if function is PredicateExpressionFunction.HasDeclaredAreaCode:
        return ctx.has_declared_area_code(argument)

    elif function is PredicateExpressionFunction.HasCourse:
        return ctx.has_course(argument)

    elif function is PredicateExpressionFunction.HasIpCourse:
        return ctx.has_ip_course(argument)

    elif function is PredicateExpressionFunction.HasCompletedCourse:
        return ctx.has_completed_course(argument)

    elif function is PredicateExpressionFunction.StudentHasCourseWithAttribute:
        for _ in filter(course_filter(attribute=argument), ctx.transcript()):
            return True
        return False

    elif function is PredicateExpressionFunction.PassedProficiencyExam:
        return ctx.music_proficiencies.passed_exam(of=argument)

    elif function is PredicateExpressionFunction.HasOverrideException:
        return ctx.has_waive_exception_for_conditional_expression(key=argument)

    else:
        raise TypeError(f"unknown static PredicateExpressionFunction {function}")


def evaluate_dynamic_predicate_function(function: DynamicPredicateExpressionFunction, argument: str, *, data: Sequence['CourseInstance']) -> bool:
    logger.debug('evaluate-dynamic: (%r %r)', function, argument)

    if function is DynamicPredicateExpressionFunction.QueryHasCourseWithAttribute:
        for _ in filter(course_filter(attribute=argument), data):
            return True
        return False

    elif function is DynamicPredicateExpressionFunction.QueryHasSingleCourseWithAttribute:
        if count(filter(course_filter(attribute=argument), data)) == 1:
            return True
        return False

    else:
        raise TypeError(f"unknown DynamicPredicateExpressionFunction {function}")


def count(it: Iterable[Any]) -> int:
    return sum(1 for _ in it)


def load_predicate_expression(
    data: Mapping[str, Any],
    *,
    ctx: 'RequirementContext',
) -> SomePredicateExpression:
    """Processes a predicate expression dictionary into a CompoundPredicateExpression instance.

    > {has-ip-course: AMCON 101}
    > {$and: [{has-ip-course: AMCON 101}, {has-area-code: '130'}]}
    > {$or: [{has-ip-course: AMCON 101}, {has-ip-course: 'AMCON 102'}]}
    > {$not: {has-ip-course: AMCON 101}}
    > {$not: {$or: [{has-ip-course: AMCON 101}, {has-ip-course: 'AMCON 102'}]}}
    """

    if PredicateExpressionCompoundAnd.can_load(data):
        return PredicateExpressionCompoundAnd.load(data, ctx=ctx)

    elif PredicateExpressionCompoundOr.can_load(data):
        return PredicateExpressionCompoundOr.load(data, ctx=ctx)

    elif PredicateExpressionNot.can_load(data):
        return PredicateExpressionNot.load(data, ctx=ctx)

    elif PredicateExpression.can_load(data):
        return PredicateExpression.load(data, ctx=ctx)

    else:
        raise TypeError(f'unknown predicate expression {data!r}')


def load_dynamic_predicate_expression(
    data: Mapping[str, Any],
    *,
    ctx: 'RequirementContext',
) -> SomeDynamicPredicateExpression:
    """Processes a predicate expression dictionary into a DynamicCompoundPredicateExpression instance.

    > {has-ip-course: AMCON 101}
    > {$and: [{has-ip-course: AMCON 101}, {has-area-code: '130'}]}
    > {$or: [{has-ip-course: AMCON 101}, {has-ip-course: 'AMCON 102'}]}
    > {$not: {has-ip-course: AMCON 101}}
    > {$not: {$or: [{has-ip-course: AMCON 101}, {has-ip-course: 'AMCON 102'}]}}
    """

    if DynamicPredicateExpressionCompoundAnd.can_load(data):
        return DynamicPredicateExpressionCompoundAnd.load(data, ctx=ctx)

    elif DynamicPredicateExpressionCompoundOr.can_load(data):
        return DynamicPredicateExpressionCompoundOr.load(data, ctx=ctx)

    elif DynamicPredicateExpression.can_load(data):
        return DynamicPredicateExpression.load(data, ctx=ctx)

    else:
        raise TypeError(f'unknown dynamic predicate expression {data!r}')
