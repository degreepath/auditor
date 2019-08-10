from dataclasses import dataclass
from typing import Tuple, Union
import logging

from .bases import Base, Rule, Solution, Result
from ..rule.assertion import AssertionRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BaseCountRule(Base):
    count: int
    items: Tuple[Union[Rule, Solution, Result], ...]
    at_most: bool
    audit_clauses: Tuple[AssertionRule, ...]

    def to_dict(self):
        return {
            **super().to_dict(),
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
            "audit": [c.to_dict() for c in self.audit_clauses],
        }

    def type(self):
        return "count"
