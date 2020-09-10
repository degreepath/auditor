from typing import Any, Mapping, Optional, List, Iterator, Collection, TYPE_CHECKING
import logging
import attr

from ..base import Rule, BaseRequirementRule
from ..constants import Constants
from ..solution.requirement import RequirementSolution
from ..exception import BlockException

from ..autop import autop

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data.clausable import Clausable  # noqa: F401
    from ..data.course import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RequirementRule(Rule, BaseRequirementRule):
    result: Optional[Rule]

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return "requirement" in data or "name" in data

    @staticmethod
    def load(data: Mapping[str, Any], *, name: str, c: Constants, path: List[str], ctx: 'RequirementContext') -> 'RequirementRule':
        from ..load_rule import load_rule

        path = [*path, f"%{name}"]

        # "name" is allowed due to emphasis requirements
        allowed_keys = {
            'in_gpa', 'name', 'result', 'disjoint',
            'message', 'contract', 'requirements',
            'department_audited', 'department-audited',
        }
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        result = data.get("result", None)

        if result is not None:
            result = load_rule(data=result, c=c, children=data.get("requirements", {}), path=path, ctx=ctx)

            all_child_names = set(data.get("requirements", {}).keys())
            used_child_names = set(result.get_requirement_names())
            unused_child_names = all_child_names.difference(used_child_names)
            assert unused_child_names == set(), f"expected {unused_child_names} to be empty"

        is_audited = data.get("department_audited", data.get("department-audited", False))

        if 'audit' in data:
            raise TypeError('you probably meant to indent that audit: key into the result: key')

        if not is_audited and not result:
            raise TypeError(f'requirements need either audited_by or result (at {path})')

        message = data.get("message", None)
        if message:
            message = autop(message)

        return RequirementRule(
            name=name,
            message=message,
            result=result,
            is_contract=data.get("contract", False),
            disjoint=data.get("disjoint", None),
            in_gpa=data.get("in_gpa", True),
            is_audited=is_audited,
            path=tuple(path),
        )

    def validate(self, *, ctx: 'RequirementContext') -> None:
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        if self.message is not None:
            assert isinstance(self.message, str)
            assert self.message.strip() != ""

        if self.result is not None:
            self.result.validate(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return [self.name]

    def get_required_courses(self, *, ctx: 'RequirementContext') -> Collection['CourseInstance']:
        if self.result:
            return self.result.get_required_courses(ctx=ctx)
        return tuple()

    def exclude_required_courses(self, to_exclude: Collection['CourseInstance']) -> 'RequirementRule':
        if not self.result:
            return self

        result = self.result.exclude_required_courses(to_exclude)
        return attr.evolve(self, result=result)

    def apply_block_exception(self, to_block: BlockException) -> 'RequirementRule':
        if not self.result:
            return self

        result = self.result.apply_block_exception(to_block)
        return attr.evolve(self, result=result)

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[RequirementSolution]:
        if ctx.get_waive_exception(self.path):
            yield RequirementSolution.from_rule(rule=self, solution=self.result, overridden=True)
            return

        if not self.result:
            yield RequirementSolution.from_rule(rule=self, solution=None)
            return

        for solution in self.result.solutions(ctx=ctx):
            yield RequirementSolution.from_rule(rule=self, solution=solution)

    def estimate(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> int:
        if ctx.get_waive_exception(self.path):
            return 1

        if not self.result:
            return 1

        return self.result.estimate(ctx=ctx)

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if self._has_potential(ctx=ctx):
            logger.debug('%s has potential: yes', self.path)
            return True
        else:
            logger.debug('%s has potential: no', self.path)
            return False

    def _has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if ctx.has_exception_beneath(self.path):
            return True

        if self.is_audited:
            return False

        if self.result:
            return self.result.has_potential(ctx=ctx)

        return False

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        if not self.result:
            return []

        return self.result.all_matches(ctx=ctx)
