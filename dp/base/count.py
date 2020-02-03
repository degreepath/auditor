import attr
from typing import Tuple, Dict, Any, Sequence, List, cast
import logging
from decimal import Decimal

from .bases import Base
from .assertion import BaseAssertionRule
from ..claim import ClaimAttempt
from ..status import ResultStatus, PassingStatuses, WAIVED_ONLY, WAIVED_AND_DONE, WAIVED_DONE_CURRENT, WAIVED_DONE_CURRENT_PENDING

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

    def max_rank(self, ranks: Sequence[Decimal]) -> Decimal:
        if not ranks:
            return Decimal(1)

        if len(self.items) == 2 and self.count == 2:
            return cast(Decimal, sum(sorted(m for m in ranks)[:2]))

        if self.count == 1 and self.at_most:
            return max(m for m in ranks)

        return cast(Decimal, sum(m for m in ranks))

    def rank(self) -> Tuple[Decimal, Decimal]:
        if self.waived():
            return Decimal(1), Decimal(1)

        item_ranks = [r.rank() for r in self.items]
        item_ranks_actual = (r for r, m, in item_ranks)
        item_ranks_max = (m for r, m, in item_ranks)

        if len(self.items) == 2 and self.count == 2:
            item_max_rank = cast(Decimal, sum(sorted(m for m in item_ranks_max)[:2]))
        elif self.count == 1 and self.at_most:
            item_max_rank = max(m for m in item_ranks_max)
        else:
            item_max_rank = cast(Decimal, sum(m for m in item_ranks_max))

        item_rank = cast(Decimal, sum(item_ranks_actual))
        item_max_rank = max(item_rank, item_max_rank)

        audit_ranks = [c.rank() for c in self.audits()]
        audit_ranks_actual = (r for r, m in audit_ranks)
        audit_ranks_max = (m for r, m in audit_ranks)

        audit_rank = cast(Decimal, sum(audit_ranks_actual))
        audit_max_rank = max(audit_rank, cast(Decimal, sum(audit_ranks_max)))

        return item_rank + audit_rank, item_max_rank + audit_max_rank

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        all_child_statuses = [r.status() for r in self.items]
        all_passing_child_statuses = [s for s in all_child_statuses if s in PassingStatuses]
        passing_child_statuses = set(all_passing_child_statuses)
        passing_child_count = len(all_passing_child_statuses)

        all_audit_statuses = set(a.status() for a in self.audits())

        # if all rules and audits have been waived, pretend that we're waived as well
        if passing_child_statuses == WAIVED_ONLY and all_audit_statuses.issubset(WAIVED_ONLY):
            return ResultStatus.Waived

        if passing_child_count == 0:
            return ResultStatus.Empty

        if passing_child_count < self.count:
            return ResultStatus.NeedsMoreItems

        if passing_child_statuses.issubset(WAIVED_AND_DONE) and all_audit_statuses.issubset(WAIVED_AND_DONE):
            return ResultStatus.Done

        if passing_child_statuses.issubset(WAIVED_DONE_CURRENT) and all_audit_statuses.issubset(WAIVED_DONE_CURRENT):
            return ResultStatus.PendingCurrent

        if passing_child_statuses.issubset(WAIVED_DONE_CURRENT_PENDING) and all_audit_statuses.issubset(WAIVED_DONE_CURRENT_PENDING):
            return ResultStatus.PendingRegistered

        return ResultStatus.NeedsMoreItems
