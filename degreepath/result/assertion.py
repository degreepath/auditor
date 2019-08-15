from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..base.bases import Result
from ..base.assertion import BaseAssertionRule

if TYPE_CHECKING:
    from ..context import RequirementContext  # noqa: F401


@dataclass(frozen=True)
class AssertionResult(Result, BaseAssertionRule):
    __slots__ = ('overridden',)
    overridden: bool

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.where:
            self.where.validate(ctx=ctx)

        self.assertion.validate(ctx=ctx)

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.assertion.result is True
