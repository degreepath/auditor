from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Rule:
    do: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "do" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> Rule:
        return Rule(do=data["do"])

    def validate(self):
        pass
