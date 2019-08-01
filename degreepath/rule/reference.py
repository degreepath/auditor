from dataclasses import dataclass
from typing import Dict, Mapping

from ..constants import Constants
from .requirement import Requirement


@dataclass(frozen=True)
class ReferenceRule:
    @staticmethod
    def can_load(data: Dict) -> bool:
        if "requirement" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants, children: Mapping):
        return Requirement.load(name=data["requirement"], data=children[data["requirement"]], c=c)
