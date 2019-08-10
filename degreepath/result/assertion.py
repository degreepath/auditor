from dataclasses import dataclass

from ..base.bases import Result
from ..base.assertion import BaseAssertionRule


@dataclass(frozen=True)
class AssertionResult(Result, BaseAssertionRule):
    def validate(self, *, ctx):
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def ok(self):
        return self.assertion.result is True

    def rank(self):
        return 0

    def max_rank(self):
        return 0
