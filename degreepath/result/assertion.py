from dataclasses import dataclass
from typing import Optional, Dict
from ..clause import Clause, ResolvedClause, load_clause
from ..constants import Constants


@dataclass(frozen=True)
class AssertionResult:
    where: Optional[Clause]
    assertion: ResolvedClause

    def to_dict(self):
        return {
            "type": "assertion",
            "assertion": self.assertion.to_dict() if self.assertion else None,
            "where": self.where.to_dict() if self.where else None,
            "status": "skip",
            "state": self.state(),
            "ok": self.ok(),
            "rank": self.rank(),
        }

    def validate(self, *, ctx):
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def state(self):
        return "rule"

    def ok(self):
        return True

    def rank(self):
        return 0
