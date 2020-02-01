import attr
from typing import Tuple, Dict, Any, Sequence, List, cast
import logging
from fractions import Fraction

from .bases import Base
from .assertion import BaseAssertionRule
from ..claim import ClaimAttempt
from ..status import ResultStatus

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseCountRule(Base):
    count: int
    items: Tuple[Base, ...]
    audit_clauses: Tuple[BaseAssertionRule, ...]
    at_most: bool
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

    def claims(self) -> List[ClaimAttempt]:
        return [claim for item in self.items for claim in item.claims()]

    def claims_for_gpa(self) -> List[ClaimAttempt]:
        return [claim for item in self.items for claim in item.claims_for_gpa()]

    def rank(self) -> Fraction:
        if self.waived():
            return Fraction(1, 1)

        item_rank = cast(Fraction, sum(r.rank() for r in self.items))
        post_audit_rank = cast(Fraction, sum(c.rank() for c in self.audits()))

        return cast(Fraction, item_rank + post_audit_rank)

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        allowed_statuses = {ResultStatus.Done, ResultStatus.Waived}
        item_statuses = set(r.status() for r in self.items)
        audit_statuses = set(a.status() for a in self.audits())
        statuses = item_statuses.intersection(audit_statuses)

        if allowed_statuses.issuperset(statuses):
            return ResultStatus.Done

        allowed_statuses.add(ResultStatus.PendingCurrent)
        if allowed_statuses.issuperset(statuses):
            return ResultStatus.PendingCurrent

        allowed_statuses.add(ResultStatus.PendingRegistered)
        if allowed_statuses.issuperset(statuses):
            return ResultStatus.PendingRegistered

        allowed_statuses.add(ResultStatus.NeedsMoreItems)
        if allowed_statuses.issuperset(statuses):
            return ResultStatus.NeedsMoreItems

        return ResultStatus.Empty
