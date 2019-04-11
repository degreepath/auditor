from __future__ import annotations
from dataclasses import dataclass

from ..data import CourseStatus


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
