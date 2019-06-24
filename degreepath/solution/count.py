from dataclasses import dataclass
from typing import List, Tuple, TYPE_CHECKING, Any
import itertools
import logging

from ..result import CountResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountSolution:
    count: int
    items: Tuple

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
    def from_rule(rule: Any, *, items):
        return CountSolution(count=rule.count, items=items)

    def flatten(self):
        return (x for s in self.items for x in s.flatten())

    def audit(self, *, ctx, path: List):
        path = [*path, f".of"]

        results = tuple(
            r.audit(ctx=ctx, path=[*path, i]) if r.state() == "solution" else r
            for i, r in enumerate(self.items)
        )

        # print(self.items)

        return CountResult(count=self.count, items=results)
