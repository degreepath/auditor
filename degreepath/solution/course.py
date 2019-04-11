from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Optional, Any, TYPE_CHECKING
import itertools
import logging

if TYPE_CHECKING:
    from ..rule import CourseRule
    from ..result import Result
    from ..requirement import RequirementContext

from ..result import CourseResult
from ..data import CourseStatus


@dataclass(frozen=True)
class CourseSolution:
    course: str
    rule: CourseRule

    def to_dict(self):
        return {**self.rule.to_dict(), "type": "course", "course": self.course}

    def audit(self, *, ctx: RequirementContext) -> Result:
        found_course = ctx.find_course(self.course)

        if found_course:
            return CourseResult(
                course=self.course, status=found_course.status, success=True
            )

        logging.debug(f'course "{self.course}" does not exist in the transcript')
        return CourseResult(
            course=self.course, status=CourseStatus.NotTaken, success=False
        )
