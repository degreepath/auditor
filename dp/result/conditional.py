from typing import Optional, TYPE_CHECKING
import logging

import attr

from ..base import Base, Result, BaseConditionalRule

if TYPE_CHECKING:
    from ..solution.conditional import ConditionalSolution

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalResult(Result, BaseConditionalRule):
    @staticmethod
    def from_solution(*, source: 'ConditionalSolution', when_true: Optional[Base] = None, when_false: Optional[Base] = None) -> 'ConditionalResult':
        return ConditionalResult(
            path=source.path,
            condition=source.condition,
            when_true=when_true if when_true else source.when_true,
            when_false=when_false if when_false else source.when_false,
            overridden=source.overridden,
        )
