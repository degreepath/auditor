import attr
from typing import Tuple, Union, Dict, Any, Sequence
import logging

from .bases import Base, Rule, Solution, Result
from .assertion import BaseAssertionRule

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
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

    def type(self) -> str:
        return "count"

    def rank(self) -> int:
        return sum(r.rank() for r in self.items) + sum(c.rank() for c in self.audit_clauses)

    def max_rank(self) -> int:
        audit_max_rank = sum(c.rank() for c in self.audit_clauses)
        if len(self.items) == 2 and self.count == 2:
            return sum(sorted(r.max_rank() for r in self.items)[:2]) + audit_max_rank

        if self.count == 1 and self.at_most:
            return max(r.max_rank() for r in self.items) + audit_max_rank

        return sum(r.max_rank() for r in self.items) + audit_max_rank
