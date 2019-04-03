from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
import re


@dataclass(frozen=True)
class Rule:
    course: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> Rule:
        return Rule(course=data['course'])

    def validate(self):
        method_a = re.match(r'[A-Z]{3,5} [0-9]{3}', self.course)
        method_b = re.match(r'[A-Z]{2}/[A-Z]{2} [0-9]{3}', self.course)
        assert (method_a or method_b) is not None
