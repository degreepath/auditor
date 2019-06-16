from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Optional, Any, TYPE_CHECKING, Sequence
import itertools
import logging
import decimal

if TYPE_CHECKING:
    from ..rule import FromRule
    from ..result import Result
    from ..requirement import RequirementContext

from ..result import FromResult
from ..data import CourseInstance, Term

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FromSolution:
    output: Sequence[Union[CourseInstance, Term, decimal.Decimal, int]]
    rule: FromRule

    def to_dict(self):
        return {
            "type": "from",
            "source": self.rule.source,
            "action": self.rule.action,
            "where": self.rule.where,
            "output": [x.to_dict() for x in self.output],
            "state": self.state(),
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [item for item in self.claims()],
        }

    def state(self):
        return "solution"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    def stored(self):
        return self.output

    def audit(self, *, ctx: RequirementContext, path: List) -> Result:
        path = [*path, f".of"]

        if self.rule.source.mode == "student":
            return self.audit_when_student(ctx=ctx, path=path)
        if self.rule.source.mode == "saves":
            return self.audit_when_saves(ctx=ctx, path=path)
        if self.rule.source.mode == "requirements":
            return self.audit_when_reqs(ctx=ctx, path=path)

        raise KeyError(f'unknown "from" type "{self.rule.source.mode}"')

    def audit_when_student(self, ctx: RequirementContext, path: List) -> Result:
        if self.rule.action.apply(len(self.output)):
            for course in self.output:
                claim = ctx.make_claim(
                    course=course, key=path, value=self.rule.action.to_dict()
                )

                if claim.failed:
                    logger.debug(
                        f'{path}\n\tcourse "{course}" exists, but has already been claimed by {claim.conflict_with}'
                    )
                    return FromResult(rule=self.rule, claimed=list())

                logger.debug(
                    f'{path}\n\tcourse "{course}" exists, and has not been claimed'
                )

            return FromResult(rule=self.rule, claimed=list(self.output))
        else:
            # logger.debug(f"{path} from-rule '{self.rule}' did not succeed")
            return FromResult(rule=self.rule, claimed=[])
