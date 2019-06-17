from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Result
    from ..rule import Rule


@dataclass(frozen=True)
class CountResult:
    count: int
    items: Tuple[Union[Rule, Result], ...]

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "items": [x.to_dict() for x in self.items],
            "status": "pass" if self.ok() else "problem",
            "rank": self.rank(),
            "ok": self.ok(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    def state(self):
        return "result"

    def claims(self):
        return [claim for item in self.items for claim in item.claims()]

    def ok(self) -> bool:
        return sum(1 if r.ok() else 0 for r in self.items) >= self.count

    def rank(self):
        return sum(r.rank() for r in self.items)
