from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from ..types import OptReqList, OptSaveList


class GivenInput(Enum):
    TheseRequirements = 0
    TheseCourses = 1
    TheseSaves = 2


@dataclass(frozen=True)
class Rule:
    name: str
    given: GivenInput

    requirements: Optional[List[str]] = None
    saves: Optional[List[str]] = None
    courses: Optional[List[str]] = None
    save: Optional[str] = None

    @staticmethod
    def load(data: Dict) -> Rule:
        return Rule(given=data["given"])

    def validate(self, requirements: OptReqList = None, saves: OptSaveList = None):
        assert isinstance(self.given, str)

        if self.given == "these-requirements":
            for name in self.requirements:
                found = [r for r in requirements if r.name == name]
                assert len(found) == 1

        elif self.given == "these-saves":
            for name in self.requirements:
                found = [s for s in saves if s.name == name]
                assert len(found) == 1

        elif self.given == "save":
            found = [s for s in saves if s.name == self.save]
            assert len(found) == 1

        elif self.given == "these-courses":
            assert len(self.courses) >= 1

        elif self.given == "all-courses":
            assert self.requirements is None
            assert self.saves is None
            assert self.courses is None

        else:
            raise NameError(f"unknown 'given' type {self.given}")
