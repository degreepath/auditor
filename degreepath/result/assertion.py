from dataclasses import dataclass

from ..base.bases import Result
from ..base.assertion import BaseAssertionRule


@dataclass(frozen=True)
class AssertionResult(Result, BaseAssertionRule):
    overridden: bool = False

    def validate(self, *, ctx):
        if self.where:
            self.where.validate(ctx=ctx)

        self.assertion.validate(ctx=ctx)

    def was_overridden(self):
        return self.overridden

    def ok(self):
        if self.was_overridden():
            return True

        return self.assertion.result is True

    def rank(self):
        return 0

    def max_rank(self):
        return 0
