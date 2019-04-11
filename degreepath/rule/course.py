from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..requirement import RequirementContext
from ..solution import CourseSolution

if TYPE_CHECKING:
    from . import Rule


@dataclass(frozen=True)
class CourseRule:
    course: str

    def to_dict(self):
        return {"type": "course", "course": self.course}

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> CourseRule:
        return CourseRule(course=data["course"])

    def validate(self, *, ctx: RequirementContext):
        method_a = re.match(r"[A-Z]{3,5} [0-9]{3}", self.course)
        method_b = re.match(r"[A-Z]{2}/[A-Z]{2} [0-9]{3}", self.course)
        method_c = re.match(r"(IS|ID) [0-9]{3}", self.course)
        assert (
            method_a or method_b or method_c
        ) is not None, f"{self.course}, {method_a}, {method_b}, {method_c}"

    def solutions(self, *, ctx: RequirementContext, path: List):
        logging.debug(f'{path} reference to course "{self.course}"')

        yield CourseSolution(course=self.course, rule=self)
