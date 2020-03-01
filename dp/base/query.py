from typing import Optional, Tuple, Dict, Any, Sequence, Union, cast
from decimal import Decimal
import enum

import attr

from ..claim import Claim
from ..clause import Clause
from ..limit import LimitSet
from ..result.assertion import AssertionResult
from ..rule.assertion import AssertionRule
from ..rule.conditional_assertion import ConditionalAssertionRule
from ..status import ResultStatus, WAIVED_ONLY, WAIVED_AND_DONE, WAIVED_DONE_CURRENT, WAIVED_DONE_CURRENT_PENDING, WAIVED_DONE_CURRENT_PENDING_INCOMPLETE

from .bases import Base


@enum.unique
class QuerySource(enum.Enum):
    Courses = "courses"
    Claimed = "claimed"
    Areas = "areas"
    MusicPerformances = "music performances"
    MusicAttendances = "music recitals"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseQueryRule(Base):
    source: QuerySource
    assertions: Tuple[Union[AssertionRule, ConditionalAssertionRule], ...]
    limit: LimitSet
    where: Optional[Clause]
    allow_claimed: bool
    attempt_claims: bool
    record_claims: bool
    path: Tuple[str, ...]
    inserted: Tuple[str, ...]
    force_inserted: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "source": self.source.value,
            "limit": self.limit.to_dict(),
            "assertions": [a.to_dict() for a in self.all_assertions()],
            "where": self.where.to_dict() if self.where else None,
            "claims": [c.to_dict() for c in self.claims()],
            "failures": [c.to_dict() for c in self.only_failed_claims()],
            "inserted": list(self.inserted),
        }

    def only_failed_claims(self) -> Sequence[Claim]:
        return []

    def all_assertions(self) -> Sequence[Union[AssertionRule, ConditionalAssertionRule, AssertionResult]]:
        return self.assertions

    def type(self) -> str:
        return "query"

    def rank(self) -> Tuple[Decimal, Decimal]:
        if self.waived():
            return Decimal(1), Decimal(1)

        assertion_ranks = [a.rank() for a in self.all_assertions()]

        rank = cast(Decimal, sum(r for r, m in assertion_ranks))
        max_rank = cast(Decimal, sum(m for r, m in assertion_ranks))

        return rank, max_rank

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        statuses = set(a.status() for a in self.all_assertions())

        if ResultStatus.FailedInvariant in statuses:
            return ResultStatus.FailedInvariant

        if statuses.issubset(WAIVED_ONLY):
            return ResultStatus.Waived

        if statuses.issubset(WAIVED_AND_DONE):
            return ResultStatus.Done

        if statuses.issubset(WAIVED_DONE_CURRENT):
            return ResultStatus.PendingCurrent

        if statuses.issubset(WAIVED_DONE_CURRENT_PENDING):
            return ResultStatus.PendingRegistered

        if statuses.issubset(WAIVED_DONE_CURRENT_PENDING_INCOMPLETE):
            return ResultStatus.NeedsMoreItems

        if ResultStatus.Empty in statuses and statuses.intersection(WAIVED_DONE_CURRENT_PENDING_INCOMPLETE):
            return ResultStatus.NeedsMoreItems

        return ResultStatus.Empty
