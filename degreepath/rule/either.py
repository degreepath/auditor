from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
import degreepath.rule as rule
from ..types import OptReqList, OptSaveList


@dataclass(frozen=True)
class Rule:
    a: rule.Rule
    b: rule.Rule

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "either" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> Rule:
        return Rule(
            a=rule.Rule.load(data["either"][0]), b=rule.Rule.load(data["either"][1])
        )

    def validate(self, *, requirements: OptReqList = None, saves: OptSaveList = None):
        if requirements is None:
            requirements = []

        if saves is None:
            saves = []

        self.a.validate(requirements=requirements, saves=saves)
        self.b.validate(requirements=requirements, saves=saves)
