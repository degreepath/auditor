from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Optional, Any, TYPE_CHECKING
import itertools
import logging

if TYPE_CHECKING:
    from ..rule import CountRule
    from ..result import Result
    from ..requirement import RequirementContext

from ..result import CountResult


@dataclass(frozen=True)
class ActionSolution:
    result: Optional[bool]
