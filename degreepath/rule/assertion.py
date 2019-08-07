from dataclasses import dataclass
from typing import Optional, Dict
from ..clause import Clause, load_clause, str_clause
from ..constants import Constants


@dataclass(frozen=True)
class AssertionRule:
    where: Optional[Clause]
    assertion: Clause

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
        return False

    def rank(self):
        return 0

    def __repr__(self):
        content = (f"where {str_clause(self.where)}, " if self.where else '') + f"{str_clause(self.assertion)}"
        return f"AssertionRule({content})"

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants):
        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c)

        assertion = load_clause(data["assert"], c)

        return AssertionRule(assertion=assertion, where=where)
