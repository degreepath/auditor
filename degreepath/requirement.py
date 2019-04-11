from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .data import CourseInstance, CourseStatus


@dataclass(frozen=False)
class RequirementContext:
    transcript: List[CourseInstance] = field(default_factory=list)

    def find_course(self, c: str) -> Optional[CourseInstance]:
        try:
            return next(
                course
                for course in self.transcript
                if course.status != CourseStatus.DidNotComplete and course.course() == c
            )
        except StopIteration:
            return None
