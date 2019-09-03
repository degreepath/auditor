import attr
from typing import Any, Mapping, Optional, List, Iterator, Collection, TYPE_CHECKING
import logging

from ..base import Rule, BaseRequirementRule, ResultStatus
from ..base.requirement import AuditedBy
from ..constants import Constants
from ..solution.requirement import RequirementSolution
from ..rule.query import QueryRule
from ..solve import find_best_solution

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RequirementRule(Rule, BaseRequirementRule):
    result: Optional[Rule]

    def status(self) -> ResultStatus:
        return ResultStatus.Pending

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return "requirement" in data

    @staticmethod
    def load(data: Mapping[str, Any], *, name: str, c: Constants, path: List[str], ctx: Optional['RequirementContext'] = None) -> Optional['RequirementRule']:
        from ..load_rule import load_rule

        path = [*path, f"%{name}"]

        # be able to exclude requirements if they shouldn't exist
        if 'if' in data:
            if ctx is None:
                raise TypeError('conditional requirements are only supported at the top-level')

            rule = QueryRule.load(data['if'], c=c, path=path)

            s = find_best_solution(rule=rule, ctx=ctx)
            if not s:
                return None

            if s.ok():
                pass
            else:
                return None

        result = data.get("result", None)
        if result is not None:
            result = load_rule(data=result, c=c, children=data.get("requirements", {}), path=path)
            if result is None:
                return None

            all_child_names = set(data.get("requirements", {}).keys())
            used_child_names = set(result.get_requirement_names())
            unused_child_names = all_child_names.difference(used_child_names)
            assert unused_child_names == set(), f"expected {unused_child_names} to be empty"

        audited_by = None
        if data.get("department_audited", data.get("department-audited", False)):
            audited_by = AuditedBy.Department
        elif data.get("registrar_audited", data.get("registrar-audited", False)):
            audited_by = AuditedBy.Registrar

        if 'audit' in data:
            raise TypeError('you probably meant to indent that audit: key into the result: key')

        if not audited_by and not result:
            raise TypeError(f'requirements need either audited_by or result (at {path})')

        return RequirementRule(
            name=name,
            message=data.get("message", None),
            result=result,
            is_contract=data.get("contract", False),
            audited_by=audited_by,
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

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[RequirementSolution]:
        if ctx.get_waive_exception(self.path):
            logger.debug("forced override on %s", self.path)
            yield RequirementSolution.from_rule(rule=self, solution=self.result, overridden=True)
            return

        logger.debug("%s auditing %s", self.path, self.name)

        if self.audited_by is not None:
            logger.debug("%s requirement \"%s\" is audited %s", self.path, self.name, self.audited_by)

        if not self.result:
            logger.debug("%s requirement \"%s\" does not have a result", self.path, self.name)
            yield RequirementSolution.from_rule(rule=self, solution=None)
            return

        for solution in self.result.solutions(ctx=ctx):
            yield RequirementSolution.from_rule(rule=self, solution=solution)

    def estimate(self, *, ctx: 'RequirementContext') -> int:
        if not self.result:
            logger.debug('RequirementRule.estimate: 1')
            return 1

        estimate = self.result.estimate(ctx=ctx)
        logger.debug('RequirementRule.estimate: %s', estimate)
        return estimate

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if self._has_potential(ctx=ctx):
            logger.debug('%s has potential: yes', self.path)
            return True
        else:
            logger.debug('%s has potential: no', self.path)
            return False

    def _has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if ctx.has_exception(self.path):
            return True

        if self.audited_by is not None:
            return False

        if self.result:
            return self.result.has_potential(ctx=ctx)

        return False

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        if not self.result:
            return []

        return self.result.all_matches(ctx=ctx)
