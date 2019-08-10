from dataclasses import dataclass, replace
from typing import List, Any, Mapping, Optional
import logging

from ..base import Rule, BaseRequirementRule
from ..base.requirement import AuditedBy
from ..solution.requirement import RequirementSolution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequirementRule(Rule, BaseRequirementRule):
    result: Optional[Rule]

    def status(self):
        return "pending"

    @staticmethod
    def load(name: str, data: Mapping[str, Any], c):
        from ..load_rule import load_rule

        result = data.get("result", None)
        if result is not None:
            result = load_rule(result, c, data.get("requirements", {}))

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

    def solutions(self, *, ctx, path: List[str]):
        path = [*path, f"$r->{self.name}"]

        logger.debug("%s auditing %s", path, self.name)

        if self.audited_by is not None:
            logger.debug("%s requirement \"%s\" is audited %s", path, self.name, self.audited_by)

        if not self.result:
            logger.debug("%s requirement \"%s\" does not have a result", path, self.name)
            yield RequirementSolution.from_rule(rule=self, solution=None)
            return

        new_ctx = replace(ctx)

        for solution in self.result.solutions(ctx=new_ctx, path=path):
            yield RequirementSolution.from_rule(rule=self, solution=solution)

    def estimate(self, *, ctx):
        if not self.result:
            logger.debug('RequirementRule.estimate: 1')
            return 1

        estimate = self.result.estimate(ctx=ctx)
        logger.debug('RequirementRule.estimate: %s', estimate)
        return estimate
