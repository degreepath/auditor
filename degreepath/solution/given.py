from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Optional, Any, TYPE_CHECKING, Sequence
import itertools
import logging
import decimal

if TYPE_CHECKING:
    from ..rule import FromRule
    from ..result import Result
    from ..requirement import RequirementContext

from ..result import CourseResult
from ..data import CourseInstance, Term


@dataclass(frozen=True)
class FromSolution:
    output: Sequence[Union[CourseInstance, Term, decimal.Decimal, int]]
    rule: FromRule

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "type": "from",
            "output": [x.to_dict() for x in self.output],
        }

    def stored(self):
        return self.output
