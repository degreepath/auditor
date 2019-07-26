from dataclasses import dataclass, field, replace
from typing import List, Optional, Tuple, Any, Dict, Union, Set, TYPE_CHECKING
import logging
from collections import defaultdict
import copy

from ..result.requirement import RequirementResult


@dataclass(frozen=True)
class RequirementSolution:
    name: str
    saves: Any  # frozendict[str, SaveRule]
    requirements: Any  # frozendict[str, Requirement]
    result: Optional[Any]
    inputs: Tuple[Tuple[str, int], ...]
    message: Optional[str] = None
    audited_by: Optional[str] = None
    contract: bool = False

    # req: Requirement
    @staticmethod
    def from_requirement(req: Any, *, solution: Optional[Any], inputs: Tuple[Tuple[str, int], ...]):
        return RequirementSolution(
            inputs=inputs,
            result=solution,
            name=req.name,
            saves=req.saves,
            requirements=req.requirements,
            message=req.message,
            audited_by=req.audited_by,
            contract=req.contract,
        )

    def matched(self, *, ctx):
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)

    def to_dict(self):
        return {
            "type": "requirement",
            "name": self.name,
            "saves": {name: s.to_dict() for name, s in self.saves.items()},
            "requirements": {name: r.to_dict() for name, r in self.requirements.items()},
            "message": self.message,
            "result": self.result.to_dict() if self.result else None,
            "audited_by": self.audited_by,
            "contract": self.contract,
            "state": self.state(),
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": self.claims(),
        }

    def rank(self):
        return 0

    def state(self):
        if self.audited_by:
            return "solution"
        if not self.result:
            return "solution"
        return self.result.state()

    def claims(self):
        if self.audited_by:
            return []
        if not self.result:
            return []
        return self.result.claims()

    def ok(self):
        if not self.result:
            return False
        return self.result.ok()

    def audit(self, *, ctx, path: List):
        if not self.result:
            # TODO: return something better
            return RequirementResult.from_solution(self, result=None)

        result = self.result.audit(ctx=ctx, path=path)

        return RequirementResult.from_solution(self, result=result)
