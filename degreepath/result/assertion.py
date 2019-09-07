import attr
from typing import TYPE_CHECKING

from ..base.bases import Result
from ..base.assertion import BaseAssertionRule

if TYPE_CHECKING:
    from ..context import RequirementContext  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AssertionResult(Result, BaseAssertionRule):
    overridden: bool

    def was_overridden(self) -> bool:
        return self.overridden
