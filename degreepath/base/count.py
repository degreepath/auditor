from dataclasses import dataclass
from typing import Tuple, Union, Dict, Any, Sequence
import logging

from .bases import Base, Rule, Solution, Result
from .assertion import BaseAssertionRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BaseCountRule(Base):
    __slots__ = ('count', 'items', 'at_most', 'audit_clauses')
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

    def type(self) -> str:
        return "count"

    def rank(self) -> int:
        return sum(r.rank() for r in self.items)

    def max_rank(self) -> int:
        ranks = (r.max_rank() for r in self.items)
        if len(self.items) == 2 and self.count == 2:
            return sum(sorted(ranks)[:2])
        if self.count == 1 and self.at_most:
            return max(ranks)
        return sum(ranks)
