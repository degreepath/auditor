from dataclasses import dataclass, replace
from typing import List, Optional, Any, Mapping
import logging

from ..frozendict import frozendict
from ..solution.requirement import RequirementSolution
from ..load_rule import load_rule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Requirement:
    name: str
    requirements: Mapping  # frozendict[str, Requirement]
    message: Optional[str] = None
    result: Optional[Any] = None
    audited_by: Optional[str] = None
    contract: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "requirements": {name: r.to_dict() for name, r in self.requirements.items()},
            "message": self.message,
            "result": self.result.to_dict() if self.result is not None else None,
            "audited_by": self.audited_by,
            "contract": self.contract,
        }

    @staticmethod
    def load(name: str, data: Mapping[str, Any], c):
        children = frozendict({
            name: Requirement.load(name, r, c)
            for name, r in data.get("requirements", {}).items()
        })

        result = data.get("result", None)
        if result is not None:
            result = load_rule(result, c)

        audited_by = None
        if data.get("department_audited", False):
            audited_by = "department"
        if data.get("department-audited", False):
            audited_by = "department"
        elif data.get("registrar_audited", False):
            audited_by = "registrar"

        if 'audit' in data:
            raise TypeError('you probably meant to indent that audit: key into the result: key')

        return Requirement(
            name=name,
            message=data.get("message", None),
            requirements=children,
            result=result,
            contract=data.get("contract", False),
            audited_by=audited_by,
        )

    def validate(self, *, ctx):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        if self.message is not None:
            assert isinstance(self.message, str)
            assert self.message.strip() != ""

        new_ctx = replace(ctx, requirements=self.requirements)

        if self.result is not None:
            self.result.validate(ctx=new_ctx)

    def solutions(self, *, ctx, path: List[str]):
        path = [*path, f"$req->{self.name}"]

        logger.debug("%s auditing %s", path, self.name)

        if self.audited_by is not None:
            logger.debug("%s requirement \"%s\" is audited %s", path, self.name, self.audited_by)

        if not self.result:
            logger.debug("%s requirement \"%s\" does not have a result", path, self.name)
            yield RequirementSolution.from_requirement(self, solution=None)
            return

        new_ctx = replace(ctx, requirements=self.requirements)

        path = [*path, ".result"]

        for solution in self.result.solutions(ctx=new_ctx, path=path):
            yield RequirementSolution.from_requirement(self, solution=solution)
