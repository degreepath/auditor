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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CourseSolution:
    course: str
    rule: CourseRule

    def __repr__(self):
        return self.course

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "state": self.state(),
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": self.claims(),
        }

    def state(self):
        return "solution"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    def flatten(self):
        return [self.course]

    def audit(self, *, ctx: RequirementContext, path: List) -> Result:
        found_course = ctx.find_course(self.course)

        if found_course:
            claimed = [found_course]
            return CourseResult(course=self.course, rule=self.rule, claimed=claimed)

        logger.debug(f"{path} course '{self.course}' does not exist in the transcript")
        return CourseResult(course=self.course, rule=self.rule, claimed=[])

    # def audit(self):
    #     path = [*path, f"$c->{self.course}"]
    #     if not ctx.has_course(self.course):
    #         logger.debug(
    #             f'{path}\n\tcourse "{self.course}" does not exist in the transcript'
    #         )
    #         return Solution.fail(self)
    #
    #     claim = ctx.make_claim(
    #         course=self.course, key=path, value={"course": self.course}
    #     )
    #
    #     if claim.failed():
    #         logger.debug(
    #             f'{path}\n\tcourse "{self.course}" exists, but has already been claimed by {claim.conflict.path}'
    #         )
    #         return Solution.fail(self)
    #
    #     logger.debug(
    #         f'{path}\n\tcourse "{self.course}" exists, and has not been claimed'
    #     )
    #     claim.commit()
