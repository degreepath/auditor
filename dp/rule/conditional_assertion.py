from typing import Dict, Sequence, Iterator, List, Collection, Any, Optional, Union
import logging

import attr

from ..base.bases import Rule, Solution
from ..clause import apply_clause
from ..constants import Constants
from ..context import RequirementContext
from ..data.clausable import Clausable
from ..data.course import CourseInstance
from ..status import PassingStatuses

from .assertion import AssertionRule

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalAssertionRule(Rule):
    condition: AssertionRule
    when_yes: AssertionRule
    when_no: Optional[AssertionRule]

    @staticmethod
    def load(data: Dict, *, c: Constants, ctx: Optional[RequirementContext], path: Sequence[str]) -> Union['ConditionalAssertionRule', AssertionRule]:
        if 'if' not in data:
            return AssertionRule.load(data, c=c, path=path, ctx=ctx)

        allowed_keys = {'if', 'then', 'else'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        condition = AssertionRule.load(data['if'], c=c, ctx=ctx, path=[*path, '#if'])
        when_yes = AssertionRule.load(data['then'], c=c, ctx=ctx, path=path)
        when_no = AssertionRule.load(data['else'], c=c, ctx=ctx, path=path) if data.get('else', None) is not None else None

        return ConditionalAssertionRule(condition=condition, when_yes=when_yes, when_no=when_no, path=tuple(path))

    def validate(self, *, ctx: RequirementContext) -> None:
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

    def solutions(self, *, ctx: RequirementContext, depth: Optional[int] = None) -> Iterator[Solution]:
        return self.when_yes.solutions(ctx=ctx, depth=depth)

    def estimate(self, *, ctx: RequirementContext, depth: Optional[int] = None) -> int:
        return self.when_yes.estimate(ctx=ctx)

    def has_potential(self, *, ctx: RequirementContext) -> bool:
        return self.when_yes.has_potential(ctx=ctx)

    def all_matches(self, *, ctx: RequirementContext) -> Collection[Clausable]:
        return self.when_yes.all_matches(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return self.when_yes.get_requirement_names()

    def get_required_courses(self, *, ctx: RequirementContext) -> Collection[CourseInstance]:
        return self.when_yes.get_required_courses(ctx=ctx)

    def exclude_required_courses(self, to_exclude: Collection[CourseInstance]) -> 'ConditionalAssertionRule':
        return self

    def resolve_conditional(self, input: Sequence[Clausable]) -> Optional[AssertionRule]:
        if self.condition.where is not None:
            filtered_input = tuple(item for item in input if apply_clause(self.condition.where, item))
        else:
            filtered_input = tuple(input)

        result = self.condition.resolve(filtered_input)

        if result.status() in PassingStatuses:
            return self.when_yes
        else:
            return self.when_no
