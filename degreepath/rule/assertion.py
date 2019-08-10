from dataclasses import dataclass
from typing import Dict
from ..clause import load_clause, str_clause
from ..constants import Constants

from ..base.bases import Rule
from ..base.assertion import BaseAssertionRule


@dataclass(frozen=True)
class AssertionRule(Rule, BaseAssertionRule):
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

    def validate(self, *, ctx):
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def estimate(self):
        return 0

    def solutions(self):
        raise Exception('this method should not be called')
