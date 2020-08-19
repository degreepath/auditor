from typing import Any, Mapping, Optional, List, Sequence, Iterator, Collection, TYPE_CHECKING
import logging
import attr

from ..base import Rule, BaseConditionalRule
from ..constants import Constants
from ..solution.conditional import ConditionalSolution
from ..exception import BlockException
from ..conditional_expression import load_predicate_expression

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data.clausable import Clausable  # noqa: F401
    from ..data.course import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalRule(Rule, BaseConditionalRule):
    when_true: Rule
    when_false: Optional[Rule]

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return "$if" in data

    @staticmethod
    def load(data: Mapping[str, Any], *, c: Constants, path: Sequence[str], ctx: 'RequirementContext') -> Optional['ConditionalRule']:
        from ..load_rule import load_rule

        path = tuple([*path, ".cond"])

        # "name" is allowed due to emphasis requirements
        allowed_keys = {'$if', '$then', '$else'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        condition = load_predicate_expression(data['$if'], ctx=ctx)

        when_true = load_rule(data=data['$then'], children={}, c=c, ctx=ctx, path=[*path, '/t'])
        assert when_true
        when_false = None
        if data.get('$else', None) is not None:
            when_false = load_rule(data=data['$else'], children={}, c=c, ctx=ctx, path=[*path, '/f'])

        overridden = bool(ctx.get_waive_exception(path))

        return ConditionalRule(
            path=path,
            condition=condition,
            when_true=when_true,
            when_false=when_false,
            overridden=overridden,
        )

    def validate(self, *, ctx: 'RequirementContext') -> None:
        self.condition.validate(ctx=ctx)
        self.when_true.validate(ctx=ctx)
        if self.when_false:
            self.when_false.validate(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        if self.condition.result is True:
            return self.when_true.get_requirement_names()
        elif self.condition.result is False and self.when_false:
            return self.when_false.get_requirement_names()
        else:
            return []

    def get_required_courses(self, *, ctx: 'RequirementContext') -> Collection['CourseInstance']:
        if self.condition.result is True:
            return self.when_true.get_required_courses(ctx=ctx)
        elif self.condition.result is False and self.when_false:
            return self.when_false.get_required_courses(ctx=ctx)
        else:
            return []

    def exclude_required_courses(self, to_exclude: Collection['CourseInstance']) -> 'ConditionalRule':
        when_true = self.when_true.exclude_required_courses(to_exclude)
        when_false = self.when_false
        if when_false:
            when_false = when_false.exclude_required_courses(to_exclude)

        return attr.evolve(self, when_true=when_true, when_false=when_false)

    def apply_block_exception(self, to_block: BlockException) -> 'ConditionalRule':
        when_true = self.when_true.apply_block_exception(to_block)
        when_false = self.when_false
        if when_false:
            when_false = when_false.apply_block_exception(to_block)

        return attr.evolve(self, when_true=when_true, when_false=when_false)

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[ConditionalSolution]:
        if self.condition.result is True:
            for sol in self.when_true.solutions(ctx=ctx, depth=depth):
                yield ConditionalSolution(when_true=sol, path=self.path, condition=self.condition, when_false=self.when_false, overridden=self.overridden)
        elif self.condition.result is False and self.when_false:
            for sol in self.when_false.solutions(ctx=ctx, depth=depth):
                yield ConditionalSolution(when_false=sol, path=self.path, condition=self.condition, when_true=self.when_true, overridden=self.overridden)
        else:
            return

    def estimate(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> int:
        if self.condition.result is True:
            return self.when_true.estimate(ctx=ctx, depth=depth)
        elif self.condition.result is False and self.when_false:
            return self.when_false.estimate(ctx=ctx, depth=depth)
        else:
            return 0

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if self.condition.result is True:
            return self.when_true.has_potential(ctx=ctx)
        elif self.condition.result is False and self.when_false:
            return self.when_false.has_potential(ctx=ctx)
        else:
            return False

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        if self.condition.result is True:
            return self.when_true.all_matches(ctx=ctx)
        elif self.condition.result is False and self.when_false:
            return self.when_false.all_matches(ctx=ctx)
        else:
            return []
