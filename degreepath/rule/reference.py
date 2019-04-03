from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, List
from ..types import OptReqList


@dataclass(frozen=True)
class Rule:
    requirement: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "requirement" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> Rule:
        return Rule(requirement=data["requirement"])

    def validate(self, *, requirements: OptReqList = None):
        if requirements is None:
            requirements = []

        req = [r for r in requirements if r.name == self.requirement]
        assert len(req) == 1
