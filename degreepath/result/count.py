from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from ..data import CourseStatus

if TYPE_CHECKING:
    from . import Result
    from ..solution import Solution


@dataclass(frozen=True)
class CountResult:
    items: List[Result]
    choices: List[Solution]  # rule???

    def to_dict(self):
        return {
            "ok": self.ok(),
            "rank": self.rank(),
            "items": [x.to_dict() for x in self.items],
            "choices": [x.to_dict() for x in self.choices],
        }

    def ok(self) -> bool:
        return all(r.ok() for r in self.items)

    def rank(self):
        return sum(r.rank() for r in self.items)
