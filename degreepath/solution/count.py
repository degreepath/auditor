from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Tuple, TYPE_CHECKING
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
    count: int
    items: Tuple[Union[Solution, Rule]]

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
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

    @staticmethod
    def from_rule(rule: CountRule, *, items) -> CountSolution:
        return CountSolution(count=rule.count, items=items)

    def flatten(self):
        return (x for s in self.items for x in s.flatten())

    def audit(self, *, ctx: RequirementContext, path: List) -> Result:
        path = [*path, f".of"]

        results = tuple(
            r.audit(ctx=ctx, path=[*path, i]) if r.state() == "solution" else r
            for i, r in enumerate(self.items)
        )

        # print(self.items)

        return CountResult(count=self.count, items=results)
