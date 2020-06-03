import attr
from typing import Dict, Sequence, Iterator, List, Collection, Any, Tuple, Optional, cast, TYPE_CHECKING
import logging
from decimal import Decimal

from ..clause import SingleClause, ResolvedSingleClause
from ..load_clause import load_clause
from ..constants import Constants
from ..op import Operator, apply_operator
from ..base.bases import Rule, Solution
from ..base.assertion import BaseAssertionRule
from ..apply_clause import apply_clause_to_assertion_with_courses, apply_clause_to_assertion_with_areas, apply_clause_to_assertion_with_data, area_actions, course_actions, other_actions
from ..status import ResultStatus
from ..result.assertion import AssertionResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data.clausable import Clausable  # noqa: F401
    from ..data.course import CourseInstance  # noqa: F401
    from ..data.area_pointer import AreaPointer  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AssertionRule(Rule, BaseAssertionRule):
    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, ctx: Optional['RequirementContext'], path: Sequence[str]) -> 'AssertionRule':
        path = [*path, ".assert"]

        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c=c)

        assertion = load_clause(data["assert"], c=c, ctx=ctx, allow_boolean=False, forbid=[Operator.LessThan])

        message = data.get("message", None)

        allowed_keys = {'where', 'assert', 'message'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        assert isinstance(assertion, SingleClause), "assertions may only be single clauses"

        return AssertionRule(assertion=assertion, where=where, path=tuple(path), inserted=tuple(), message=message)

    @staticmethod
    def with_clause(clause: SingleClause) -> 'AssertionRule':
        return AssertionRule(assertion=clause, where=None, path=(), inserted=(), message=None)

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return []

    def get_required_courses(self, *, ctx: 'RequirementContext') -> Collection['CourseInstance']:
        return tuple()

    def exclude_required_courses(self, to_exclude: Collection['CourseInstance']) -> 'AssertionRule':
        return self

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[Solution]:
        raise Exception('this method should not be called')

    def estimate(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> int:
        raise Exception('this method should not be called')

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        raise Exception('this method should not be called')

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        raise Exception('this method should not be called')

    def set_expected_value(self, value: Decimal) -> 'AssertionRule':
        clause = self.assertion.override_expected(value)

        return attr.evolve(self, assertion=clause)

    def override(self) -> AssertionResult:
        return AssertionResult.from_rule(self, overridden=True)

    def resolve(self, value: Tuple['Clausable', ...], *, overridden: bool = False, inserted: Tuple[str, ...] = tuple()) -> AssertionResult:
        if overridden:
            assertion = ResolvedSingleClause.as_overridden(self.assertion)
            return AssertionResult.from_rule(self, assertion=assertion, overridden=False)

        if self.assertion.key in course_actions.keys():
            return self.resolve_with_courses(cast(Sequence['CourseInstance'], value), inserted=inserted)

        if self.assertion.key in area_actions.keys():
            return self.resolve_with_areas(cast(Sequence['AreaPointer'], value), inserted=inserted)

        if self.assertion.key in other_actions.keys():
            return self.resolve_with_items(value, inserted=inserted)

        raise TypeError(f'unexpected key {self.assertion.key!r}')

    def resolve_with_areas(self, value: Sequence['AreaPointer'], *, inserted: Tuple[str, ...] = tuple()) -> AssertionResult:
        calculated_result = apply_clause_to_assertion_with_areas(self.assertion, value)

        computed_value = calculated_result.value
        operator_result = apply_operator(lhs=computed_value, op=self.assertion.operator, rhs=self.assertion.expected)

        if operator_result is True:
            result = ResultStatus.Done

        elif self.assertion.operator is Operator.GreaterThan and 0 < computed_value <= self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator is Operator.GreaterThanOrEqualTo and 0 < computed_value < self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator is Operator.EqualTo and 0 < computed_value < self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator in (Operator.LessThan, Operator.LessThanOrEqualTo):
            result = ResultStatus.FailedInvariant

        else:
            result = ResultStatus.Empty

        assertion = ResolvedSingleClause.from_clause(
            self.assertion,
            status=result,
            resolved_with=computed_value,
            resolved_items=calculated_result.data,
        )

        return AssertionResult.from_rule(self, assertion=assertion)

    def resolve_with_items(self, value: Sequence['Clausable'], *, inserted: Tuple[str, ...] = tuple()) -> AssertionResult:
        calculated_result = apply_clause_to_assertion_with_data(self.assertion, cast(Sequence[Any], value))

        computed_value = calculated_result.value
        operator_result = apply_operator(lhs=computed_value, op=self.assertion.operator, rhs=self.assertion.expected)

        if operator_result is True:
            result = ResultStatus.Done

        elif self.assertion.operator is Operator.GreaterThan and 0 < computed_value <= self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator is Operator.GreaterThanOrEqualTo and 0 < computed_value < self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator is Operator.EqualTo and 0 < computed_value < self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator in (Operator.LessThan, Operator.LessThanOrEqualTo):
            result = ResultStatus.FailedInvariant

        else:
            result = ResultStatus.Empty

        assertion = ResolvedSingleClause.from_clause(
            self.assertion,
            status=result,
            resolved_with=computed_value,
            resolved_items=calculated_result.data,
        )

        return AssertionResult.from_rule(self, assertion=assertion)

    def resolve_with_courses(self, value: Sequence['CourseInstance'], *, inserted: Tuple[str, ...] = tuple()) -> AssertionResult:
        calculated_result = apply_clause_to_assertion_with_courses(self.assertion, value)
        operator_result = apply_operator(lhs=calculated_result.value, op=self.assertion.operator, rhs=self.assertion.expected)

        if operator_result is True:
            has_ip_courses = any(c.is_in_progress for c in calculated_result.courses)

            if has_ip_courses:
                # does the clause still pass if it's given only non-IP courses?
                non_ip_courses = (c for c in value if not c.is_in_progress)
                calculated_result_no_ip = apply_clause_to_assertion_with_courses(self.assertion, non_ip_courses)
                operator_result_no_ip = apply_operator(lhs=calculated_result_no_ip.value, op=self.assertion.operator, rhs=self.assertion.expected)
            else:
                # we don't need to check if there are no IP courses in the input
                operator_result_no_ip = True

            if self.assertion.treat_in_progress_as_pass or operator_result_no_ip is True:
                result = ResultStatus.Done

            elif has_ip_courses:
                has_enrolled_courses = any(c.is_in_progress_this_term for c in calculated_result.courses)
                has_registered_courses = any(c.is_in_progress_in_future for c in calculated_result.courses)
                has_incomplete_courses = any(c.is_incomplete for c in calculated_result.courses)

                # something has gone horribly wrong if there was an IP course that's neither
                # this term nor future, and isn't an incomplete
                assert has_enrolled_courses or has_registered_courses or has_incomplete_courses

                if (has_enrolled_courses or has_incomplete_courses) and (not has_registered_courses):
                    result = ResultStatus.PendingCurrent
                elif has_registered_courses:
                    result = ResultStatus.PendingRegistered
                else:
                    raise Exception('unreachable')

            else:
                result = ResultStatus.Done

        elif self.assertion.operator is Operator.GreaterThan and 0 < calculated_result.value <= self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator is Operator.GreaterThanOrEqualTo and 0 < calculated_result.value < self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator is Operator.EqualTo and 0 < calculated_result.value < self.assertion.expected:
            result = ResultStatus.NeedsMoreItems

        elif self.assertion.operator in (Operator.LessThan, Operator.LessThanOrEqualTo):
            result = ResultStatus.FailedInvariant

        else:
            result = ResultStatus.Empty

        assertion = ResolvedSingleClause.from_clause(
            self.assertion,
            status=result,
            resolved_with=calculated_result.value,
            resolved_items=calculated_result.data,
            resolved_clbids=tuple(c.clbid for c in calculated_result.courses),
        )

        return AssertionResult.from_rule(self, assertion=assertion, inserted_clbids=inserted)

    def input_size_range(self, *, maximum: int) -> Iterator[int]:
        assertion = self.assertion

        if type(assertion.expected) is not int:
            raise TypeError('cannot find a range of values for a non-integer clause: %s', type(assertion.expected))

        if assertion.operator == Operator.EqualTo or (assertion.operator == Operator.GreaterThanOrEqualTo and assertion.at_most is True):
            if maximum < assertion.expected:
                yield maximum
                return
            yield from range(assertion.expected, assertion.expected + 1)

        elif assertion.operator == Operator.NotEqualTo:
            # from 0-maximum, skipping "expected"
            yield from range(0, assertion.expected)
            yield from range(assertion.expected + 1, max(assertion.expected + 1, maximum + 1))

        elif assertion.operator == Operator.GreaterThanOrEqualTo:
            if maximum < assertion.expected:
                yield maximum
                return
            yield from range(assertion.expected, max(assertion.expected + 1, maximum + 1))

        elif assertion.operator == Operator.GreaterThan:
            if maximum < assertion.expected:
                yield maximum
                return
            yield from range(assertion.expected + 1, max(assertion.expected + 2, maximum + 1))

        elif assertion.operator == Operator.LessThan:
            yield from range(0, assertion.expected)

        elif assertion.operator == Operator.LessThanOrEqualTo:
            yield from range(0, assertion.expected + 1)

        else:
            raise TypeError('unsupported operator for ranges %s', assertion.operator)
