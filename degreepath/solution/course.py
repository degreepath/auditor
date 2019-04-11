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

    # def audit(self):
    #     path = [*path, f"$c->{self.course}"]
    #     if not ctx.has_course(self.course):
    #         logging.debug(
    #             f'{path}\n\tcourse "{self.course}" does not exist in the transcript'
    #         )
    #         return Solution.fail(self)
    #
    #     claim = ctx.make_claim(
    #         course=self.course, key=path, value={"course": self.course}
    #     )
    #
    #     if claim.failed():
    #         logging.debug(
    #             f'{path}\n\tcourse "{self.course}" exists, but has already been claimed by {claim.conflict.path}'
    #         )
    #         return Solution.fail(self)
    #
    #     logging.debug(
    #         f'{path}\n\tcourse "{self.course}" exists, and has not been claimed'
    #     )
    #     claim.commit()
