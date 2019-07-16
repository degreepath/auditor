from dataclasses import dataclass
from typing import Union, List, TYPE_CHECKING, Sequence, Any
import logging
import decimal

from ..result import FromResult
from ..data import CourseInstance, Term

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FromSolution:
    output: Sequence[Union[CourseInstance, Term, decimal.Decimal, int]]
    rule: Any

    def to_dict(self):
        return {
            "type": "from",
            "source": self.rule.source,
            "action": self.rule.action,
            "where": self.rule.where,
            "output": [x.to_dict() for x in self.output],
            "allow_claimed": self.allow_claimed,
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

    def audit(self, *, ctx, path: List):
        path = [*path, f".of"]

        if self.rule.source.mode == "student":
            return self.audit_when_student(ctx=ctx, path=path)
        if self.rule.source.mode == "saves":
            return self.audit_when_saves(ctx=ctx, path=path)
        if self.rule.source.mode == "requirements":
            return self.audit_when_reqs(ctx=ctx, path=path)

        raise KeyError(f'unknown "from" type "{self.rule.source.mode}"')

    def audit_when_student(self, ctx, path: List):
        successful_claims = []
        failed_claims = []
        for course in self.output:
            if self.rule.where is None:
                raise Exception("`where` should not be none here; otherwise this given-rule has nothing to do")

            claim = ctx.make_claim(
                course=course,
                path=path,
                clause=self.rule.where,
                transcript=ctx.transcript,
                allow_claimed=self.rule.allow_claimed,
            )

            if claim.failed():
                logger.debug(f'{path}\n\tcourse "{course}" exists, but has already been claimed by {claim.conflict_with}')
                failed_claims.append(claim)
            else:
                logger.debug(f'{path}\n\tcourse "{course}" exists, and is available')
                successful_claims.append(claim)

        may_possibly_succeed = self.rule.action.apply(len(self.output))

        if may_possibly_succeed:
            logger.debug(f"{path} from-rule '{self.rule}' might possibly succeed")
        else:
            logger.debug(f"{path} from-rule '{self.rule}' did not succeed")

        return FromResult(
            rule=self.rule,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=may_possibly_succeed and len(failed_claims) == 0,
        )
