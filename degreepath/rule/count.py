from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
import degreepath.rule as rule
from ..types import OptReqList, OptSaveList


@dataclass(frozen=True)
class Rule:
    count: Union[int, "all", "any"]
    greedy: bool = False
    of: List[rule.Rule]

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "count" in data and "of" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> Rule:
        of = [rule.Rule.load(r) for r in data["of"]]
        return Rule(count=data["count"], of=of)

    def validate(self, *, requirements: OptReqList = None, saves: OptSaveList = None):
        if requirements is None:
            requirements = []

        if saves is None:
            saves = []

        assert self.count >= 0
        assert self.count <= len(self.of)

        for rule in self.of:
            rule.validate(requirements=requirements, saves=saves)
