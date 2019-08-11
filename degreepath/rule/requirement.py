from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional, List
import logging

from ..base import Rule, BaseRequirementRule, ResultStatus
from ..base.requirement import AuditedBy
from ..constants import Constants
from ..solution.requirement import RequirementSolution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequirementRule(Rule, BaseRequirementRule):
    result: Optional[Rule]

    def status(self):
        return ResultStatus.Pending

    @staticmethod
    def can_load(data: Mapping) -> bool:
        return "requirement" in data

    @staticmethod
    def load(data: Mapping[str, Any], *, name: str, c: Constants, path: List[str]):
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

    def validate(self, *, ctx):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        if self.message is not None:
            assert isinstance(self.message, str)
            assert self.message.strip() != ""

        new_ctx = replace(ctx)

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx):
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

    def estimate(self, *, ctx):
        if not self.result:
            logger.debug('RequirementRule.estimate: 1')
            return 1

        estimate = self.result.estimate(ctx=ctx)
        logger.debug('RequirementRule.estimate: %s', estimate)
        return estimate
