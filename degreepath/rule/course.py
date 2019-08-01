from dataclasses import dataclass
from typing import Dict, List, Optional, Mapping
import re
from decimal import Decimal
import logging

from ..constants import Constants
from ..lib import str_to_grade_points
from ..operator import Operator
from ..solution.course import CourseSolution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CourseRule:
    course: str
    hidden: bool
    grade: Optional[Decimal]
    allow_claimed: bool

    def to_dict(self):
        return {
            "type": "course",
            "state": self.state(),
            "course": self.course,
            "hidden": self.hidden,
            "grade": str(self.grade) if self.grade is not None else None,
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

        yield CourseSolution(course=self.course, rule=self)

    def estimate(self, *, ctx):
        return 1

    def is_equivalent_to_clause(self, clause) -> bool:
        if clause.key != 'course':
            return False

        if clause.operator is Operator.EqualTo:
            return self.course == clause.expected
        elif clause.operator is Operator.In:
            return self.course in clause.expected
        else:
            return False
