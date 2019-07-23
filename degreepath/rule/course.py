from dataclasses import dataclass
from typing import Dict, Union, List, Optional
import re
import itertools
import logging

from ..constants import Constants
from ..solution import CourseSolution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CourseRule:
    course: str
    hidden: bool
    grade: Optional[str]
    allow_claimed: bool

    def to_dict(self):
        return {
            "type": "course",
            "state": self.state(),
            "course": self.course,
            "hidden": self.hidden,
            "grade": self.grade,
            "allow_claimed": self.allow_claimed,
            "status": "skip",
            "ok": self.ok(),
            "rank": self.rank(),
        }

    def state(self):
        return "rule"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants):
        return CourseRule(
            course=data["course"],
            hidden=data.get("hidden", False),
            grade=data.get("grade", None),
            allow_claimed=data.get("including claimed", False),
        )

    def validate(self, *, ctx):
        method_a = re.match(r"[A-Z]{3,5} [0-9]{3}", self.course)
        method_b = re.match(r"[A-Z]{2}/[A-Z]{2} [0-9]{3}", self.course)
        method_c = re.match(r"(IS|ID) [0-9]{3}", self.course)

        assert (method_a or method_b or method_c) is not None, f"{self.course}, {method_a}, {method_b}, {method_c}"

    def solutions(self, *, ctx, path: List):
        logger.debug('{} reference to course "{}"', path, self.course)

        yield CourseSolution(course=self.course, rule=self)

    def estimate(self, *, ctx):
        return 1

    def mc_applies_same(self, other) -> bool:
        """Checks if this clause applies to the same items as the other clause,
        when used as part of a multicountable ruleset."""

        if not isinstance(other, CourseRule):
            return False

        return self.course == other.course

    def applies_to(self, other) -> bool:
        return other.shorthand == self.course or other.identity == self.course
