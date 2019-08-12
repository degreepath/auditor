from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional, List, Iterator, TYPE_CHECKING
import logging

from ..base import Rule, BaseRequirementRule, ResultStatus
from ..base.requirement import AuditedBy
from ..constants import Constants
from ..solution.requirement import RequirementSolution

if TYPE_CHECKING:
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequirementRule(Rule, BaseRequirementRule):
    result: Optional[Rule]

    def status(self) -> ResultStatus:
        return ResultStatus.Pending

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return "requirement" in data

    @staticmethod
    def load(data: Mapping[str, Any], *, name: str, c: Constants, path: List[str]) -> 'RequirementRule':
        from ..load_rule import load_rule

        path = [*path, f"%{name}"]

        result = data.get("result", None)
        if result is not None:
            result = load_rule(data=result, c=c, children=data.get("requirements", {}), path=path)

        audited_by = None
        if data.get("department_audited", data.get("department-audited", False)):
            audited_by = AuditedBy.Department
        elif data.get("registrar_audited", data.get("registrar-audited", False)):
            audited_by = AuditedBy.Registrar

        if 'audit' in data:
            raise TypeError('you probably meant to indent that audit: key into the result: key')

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

        new_ctx = replace(ctx)

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx: 'RequirementContext') -> Iterator[RequirementSolution]:
        exception = ctx.get_exception(self.path)
        if exception and exception.is_pass_override():
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

        new_ctx = replace(ctx)

        for solution in self.result.solutions(ctx=new_ctx):
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
        if ctx.get_exception(self.path):
            return True

        if self.audited_by is not None:
            return False

        return self.result.has_potential(ctx=ctx)
