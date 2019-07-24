from dataclasses import dataclass
from typing import Union, List, Optional, Any, TYPE_CHECKING
import itertools
import logging

from ..result import CourseResult
from ..data import CourseStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CourseSolution:
    course: str
    rule: Any

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

    def audit(self, *, ctx: Any, path: List):
        path = [*path, f"$c->{self.course}"]

        matched_course = ctx.find_course(self.course)
        if matched_course is None:
            logger.debug('%s course "%s" does not exist in the transcript', path, self.course)
            return CourseResult(course=self.course, rule=self.rule, claim_attempt=None)

        claim = ctx.make_claim(course=matched_course, path=path, clause=self.rule, transcript=ctx.transcript)

        if claim.failed():
            logger.debug('%s course "%s" exists, but has already been claimed by %s', path, self.course, claim.conflict_with)
            return CourseResult(course=self.course, rule=self.rule, claim_attempt=claim)

        logger.debug('%s course "%s" exists, and has not been claimed', path, self.course)

        return CourseResult(course=self.course, rule=self.rule, claim_attempt=claim)
