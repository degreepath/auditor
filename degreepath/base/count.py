from dataclasses import dataclass
from typing import Tuple, Union, Dict, Any, Sequence
import logging

from .bases import Base, Rule, Solution, Result
from .assertion import BaseAssertionRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BaseCountRule(Base):
    count: int
    items: Tuple[Union[Rule, Solution, Result], ...]
    at_most: bool
    audit_clauses: Tuple[BaseAssertionRule, ...]
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
            "audit": [c.to_dict() for c in self.audits()],
        }

    def audits(self) -> Sequence[BaseAssertionRule]:
        return self.audit_clauses

    def type(self):
        return "count"
