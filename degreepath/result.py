from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List
import itertools

from .data import CourseStatus


@dataclass(frozen=True)
class CountResult:
    items: List
    choices: List

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


@dataclass(frozen=True)
class CourseResult:
    course: str
    status: CourseStatus
    success: bool

    def to_dict(self):
        return {
            "ok": self.ok(),
            "rank": self.rank(),
            "course": self.course,
            "status": self.status,
        }

    def ok(self) -> bool:
        return self.success

    def rank(self):
        return 1 if self.ok() else 0


Result = Union[CountResult, CourseResult]
