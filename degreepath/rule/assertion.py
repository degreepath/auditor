import attr
from typing import Dict, Sequence, Iterator, List, Collection, Optional, Union, TYPE_CHECKING
import logging

from ..clause import SingleClause
from ..load_clause import load_clause
from ..constants import Constants
from ..operator import Operator
from ..base.bases import Rule, Solution
from ..base.assertion import BaseAssertionRule

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AssertionRule(Rule, BaseAssertionRule):
    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: Sequence[str]) -> 'AssertionRule':
        path = [*path, ".assert"]

        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c=c)

        assertion = load_clause(data["assert"], c=c, allow_boolean=False, forbid=[Operator.LessThan])

        message = data.get("message", None)

        allowed_keys = {'where', 'assert', 'message'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        assert isinstance(assertion, SingleClause), "assertions may only be single clauses"

        return AssertionRule(assertion=assertion, where=where, path=tuple(path), inserted=tuple(), message=message)

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return []

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[Solution]:
        raise Exception('this method should not be called')

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        raise Exception('this method should not be called')

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        raise Exception('this method should not be called')


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalAssertionRule(Rule):
    condition: AssertionRule
    when_yes: AssertionRule
    when_no: Optional[AssertionRule]

    @staticmethod
    def load(data: Dict, *, c: Constants, path: Sequence[str]) -> Union['ConditionalAssertionRule', AssertionRule]:
        if 'if' not in data:
            return AssertionRule.load(data, c=c, path=path)

        allowed_keys = {'if', 'then', 'else'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        condition = AssertionRule.load(data['if'], c=c, path=[*path, '#if'])
        when_yes = AssertionRule.load(data['then'], c=c, path=path)
        when_no = AssertionRule.load(data['else'], c=c, path=path) if data['else'] is not None else None

        return ConditionalAssertionRule(condition=condition, when_yes=when_yes, when_no=when_no, path=tuple(path))

    def validate(self, *, ctx: 'RequirementContext') -> None:
        self.condition.validate(ctx=ctx)
        self.when_yes.validate(ctx=ctx)
        if self.when_no:
            self.when_no.validate(ctx=ctx)
            assert self.when_yes.type() == self.when_no.type()
            assert self.when_yes.path == self.when_no.path

    def type(self) -> str:
        return "conditional-assertion"

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[Solution]:
        return self.when_yes.solutions(ctx=ctx, depth=depth)

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        return self.when_yes.has_potential(ctx=ctx)

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        return self.when_yes.all_matches(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return self.when_yes.get_requirement_names()

    def resolve(self, input: Sequence['Clausable']) -> Optional[AssertionRule]:
        if self.condition.where is not None:
            filtered_input = tuple(item for item in input if self.condition.where.apply(item))
        else:
            filtered_input = tuple(input)

        result = self.condition.assertion.compare_and_resolve_with(filtered_input)

        if result.ok():
            return self.when_yes
        else:
            return self.when_no
