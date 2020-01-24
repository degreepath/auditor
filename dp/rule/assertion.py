import attr
from typing import Dict, Sequence, Iterator, List, Collection, Any, Tuple, Optional, Union, TYPE_CHECKING
import logging
from decimal import Decimal

from ..clause import SingleClause, ResolvedSingleClause, apply_clause
from ..load_clause import load_clause
from ..constants import Constants
from ..operator import Operator, apply_operator
from ..base.bases import Rule, Solution
from ..base.assertion import BaseAssertionRule
from ..apply_clause import apply_clause_to_assertion
from ..status import ResultStatus
from ..result.assertion import AssertionResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data import Clausable, CourseInstance  # noqa: F401

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
        calculated_result = apply_clause_to_assertion(self.assertion, value)

        reduced_value = calculated_result.value
        value_items = calculated_result.data
        clbids = calculated_result.clbids()
        ip_clbids = calculated_result.ip_clbids()

        # if we have `treat_in_progress_as_pass` set, we skip the ip_clbids check entirely
        if ip_clbids and self.assertion.treat_in_progress_as_pass is False:
            result = ResultStatus.InProgress
        elif apply_operator(lhs=reduced_value, op=self.assertion.operator, rhs=self.assertion.expected) is True:
            result = ResultStatus.Pass
        elif clbids:
            # we aren't "passing", but we've also got at least something
            # counting towards this clause, so we'll mark it as in-progress.
            result = ResultStatus.InProgress
        else:
            result = ResultStatus.Pending

        if self.assertion.operator in (Operator.LessThan, Operator.LessThanOrEqualTo)\
                and result == ResultStatus.InProgress\
                and apply_operator(lhs=reduced_value, op=self.assertion.operator, rhs=self.assertion.expected) is True:
            result = ResultStatus.Pass

        assertion = ResolvedSingleClause(
            key=self.assertion.key,
            expected=self.assertion.expected,
            expected_verbatim=self.assertion.expected_verbatim,
            operator=self.assertion.operator,
            at_most=self.assertion.at_most,
            label=self.assertion.label,
            resolved_with=Decimal(reduced_value),
            resolved_items=tuple(value_items),
            resolved_clbids=clbids,
            in_progress_clbids=ip_clbids,
            state=result,
            treat_in_progress_as_pass=self.assertion.treat_in_progress_as_pass,
        )

        return AssertionResult.from_rule(self, assertion=assertion, inserted_clbids=inserted, overridden=False)

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


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalAssertionRule(Rule):
    condition: AssertionRule
    when_yes: AssertionRule
    when_no: Optional[AssertionRule]

    @staticmethod
    def load(data: Dict, *, c: Constants, ctx: Optional['RequirementContext'], path: Sequence[str]) -> Union['ConditionalAssertionRule', AssertionRule]:
        if 'if' not in data:
            return AssertionRule.load(data, c=c, path=path, ctx=ctx)

        allowed_keys = {'if', 'then', 'else'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        condition = AssertionRule.load(data['if'], c=c, ctx=ctx, path=[*path, '#if'])
        when_yes = AssertionRule.load(data['then'], c=c, ctx=ctx, path=path)
        when_no = AssertionRule.load(data['else'], c=c, ctx=ctx, path=path) if data.get('else', None) is not None else None

        return ConditionalAssertionRule(condition=condition, when_yes=when_yes, when_no=when_no, path=tuple(path))

    def validate(self, *, ctx: 'RequirementContext') -> None:
        self.condition.validate(ctx=ctx)
        self.when_yes.validate(ctx=ctx)
        if self.when_no:
            self.when_no.validate(ctx=ctx)
            assert self.when_yes.type() == self.when_no.type()
            assert self.when_yes.path == self.when_no.path

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "condition": self.condition.to_dict(),
            "when_yes": self.when_yes.to_dict(),
            "when_no": self.when_no.to_dict() if self.when_no else None,
        }

    def type(self) -> str:
        return "conditional-assertion"

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[Solution]:
        return self.when_yes.solutions(ctx=ctx, depth=depth)

    def estimate(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> int:
        return self.when_yes.estimate(ctx=ctx)

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        return self.when_yes.has_potential(ctx=ctx)

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        return self.when_yes.all_matches(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return self.when_yes.get_requirement_names()

    def get_required_courses(self, *, ctx: 'RequirementContext') -> Collection['CourseInstance']:
        return self.when_yes.get_required_courses(ctx=ctx)

    def exclude_required_courses(self, to_exclude: Collection['CourseInstance']) -> 'ConditionalAssertionRule':
        return self

    def resolve_conditional(self, input: Sequence['Clausable']) -> Optional[AssertionRule]:
        if self.condition.where is not None:
            filtered_input = tuple(item for item in input if apply_clause(self.condition.where, item))
        else:
            filtered_input = tuple(input)

        result = self.condition.resolve(filtered_input)

        if result.ok():
            return self.when_yes
        else:
            return self.when_no
