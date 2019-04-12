from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, TYPE_CHECKING

from ..data import CourseStatus

if TYPE_CHECKING:
    from . import Result
    from ..solution import Solution
    from ..rule import Rule


@dataclass(frozen=True)
class CountResult:
    of: Tuple[Result, ...]
    ignored: Tuple[Rule, ...]
    count: int
    size: int

    def to_dict(self):
        return {
            "type": "count",
            "ok": self.ok(),
            "rank": self.rank(),
            "of": [x.to_dict() for x in self.of],
            "ignored": [x.to_dict() for x in self.ignored],
            "size": self.size,
            "count": self.count,
        }

    def ok(self) -> bool:
        return sum(1 if r.ok() else 0 for r in self.of) >= self.count

    def rank(self):
        return sum(r.rank() for r in self.of)
