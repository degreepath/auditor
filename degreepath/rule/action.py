from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..solution import ActionSolution

if TYPE_CHECKING:
    from ..requirement import RequirementContext


@dataclass(frozen=True)
class ActionRule:
    assertion: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> ActionRule:
        return ActionRule(assertion=data["assert"])

    def validate(self, *, ctx: RequirementContext):
        ...
        # TODO: check for input items here

    def solutions(self, *, ctx: RequirementContext, path: List):
        logging.debug(f"{path} ActionRule#solutions")
        yield ActionSolution(result=None)
