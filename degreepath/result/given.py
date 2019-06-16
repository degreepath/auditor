from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from ..data import CourseInstance

if TYPE_CHECKING:
    from ..rule import FromRule


@dataclass(frozen=True)
class FromResult:
    rule: FromRule
    claimed: List[CourseInstance]

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "state": self.state(),
            "status": "pass" if self.ok() else "skip",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    def claims(self):
        return self.claimed

    def state(self):
        return "result"

    def ok(self) -> bool:
        return len(self.claimed) >= 1

    def rank(self):
        return 1 if self.ok() else 0
