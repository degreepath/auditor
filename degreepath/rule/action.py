from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..solution import ActionSolution


@dataclass(frozen=True)
class ActionRule:
    assertion: str

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict):
        return ActionRule(assertion=data["assert"])

    def validate(self, *, ctx):
        ...
        # TODO: check for input items here

    def solutions(self, *, ctx, path: List):
        logging.debug("%s ActionRule#solutions", path)
        yield ActionSolution(result=None)
