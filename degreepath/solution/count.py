from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Optional, Any, Tuple, TYPE_CHECKING
import itertools
import logging

if TYPE_CHECKING:
    from ..rule import CountRule, Rule
    from ..result import Result
    from ..requirement import RequirementContext
    from . import Solution

from ..result import CountResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountSolution:
    of: Tuple[Solution, ...]
    ignored: Tuple[Rule, ...]
    count: int
    size: int

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "type": "count",
            "of": [item.to_dict() for item in self.of],
            "ignored": [item.to_dict() for item in self.ignored],
            "count": self.count,
            "size": self.size,
        }

    def flatten(self):
        return (x for s in self.of for x in s.flatten())

    def audit(self, *, ctx: RequirementContext, path: List) -> Result:
        path = [*path, f".of"]

        results = tuple(
            r.audit(ctx=ctx, path=[*path, f"idx={i}"]) for i, r in enumerate(self.of)
        )

        return CountResult(
            of=results, ignored=self.ignored, size=self.size, count=self.count
        )
