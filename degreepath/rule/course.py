from dataclasses import dataclass
from typing import Dict, List, Mapping
import re
import logging

from ..base import Rule, BaseCourseRule
from ..constants import Constants
from ..lib import str_to_grade_points
from ..solution.course import CourseSolution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CourseRule(Rule, BaseCourseRule):
    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants, children: Mapping):
        return CourseRule(
            course=data["course"],
            hidden=data.get("hidden", False),
            grade=str_to_grade_points(data['grade']) if 'grade' in data else None,
            allow_claimed=data.get("including claimed", False),
        )

    def validate(self, *, ctx):
        method_a = re.match(r"[A-Z]{3,5} [0-9]{3}", self.course)
        method_b = re.match(r"[A-Z]{2}/[A-Z]{2} [0-9]{3}", self.course)
        method_c = re.match(r"(IS|ID) [0-9]{3}", self.course)

        assert (method_a or method_b or method_c) is not None, f"{self.course}, {method_a}, {method_b}, {method_c}"

    def solutions(self, *, ctx, path: List):
        logger.debug('%s reference to course "%s"', path, self.course)

        yield CourseSolution.from_rule(rule=self)

    def estimate(self, *, ctx):
        logger.debug('CourseRule.estimate: 1')
        return 1
