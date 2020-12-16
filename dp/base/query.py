from typing import Optional, Tuple, Dict, Any, Sequence, Iterable, cast
from decimal import Decimal
import enum

import attr

from .bases import Base
from ..assertion_clause import AnyAssertion
from ..status import ResultStatus, WAIVED_ONLY, WAIVED_AND_DONE, WAIVED_DONE_CURRENT, WAIVED_DONE_CURRENT_PENDING, WAIVED_DONE_CURRENT_PENDING_INCOMPLETE
from ..limit import LimitSet
from ..predicate_clause import SomePredicate
from ..data_type import DataType
from ..claim import Claim
from ..data.clausable import Clausable


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
    data_type: DataType
    assertions: Tuple[AnyAssertion, ...]
    limit: LimitSet
    where: Optional[SomePredicate]
    allow_claimed: bool
    attempt_claims: bool
    record_claims: bool
    include_failed: bool
    inserted: Tuple[str, ...]
    force_inserted: Tuple[str, ...]
    output: Tuple[Clausable, ...]
    successful_claims: Tuple[Claim, ...]
    failed_claims: Tuple[Claim, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "source": self.source.value,
            "data-type": self.data_type.value,
            "limit": self.limit.to_dict(),
            "assertions": [a.to_dict() for a in self.all_assertions()],
            "where": self.where.to_dict() if self.where else None,
            "claims": [c.to_dict() for c in self.claims()],
            "failures": [c.to_dict() for c in self.only_failed_claims()],
            "inserted": list(self.inserted),
            "include_failed": self.include_failed,
            "allow_claimed": self.allow_claimed,
            "output": list(self._output_to_dicts()),
        }

    def _output_to_dicts(self) -> Iterable[Clausable]:
        for item in self.output:
            yield item.to_identifier().to_dict()

    def only_failed_claims(self) -> Sequence[Claim]:
        return []

    def all_assertions(self) -> Sequence[AnyAssertion]:
        return self.assertions

    def type(self) -> str:
        return "query"

    def is_waived(self) -> bool:
        return self.overridden

    def rank(self) -> Tuple[Decimal, Decimal]:
        if self.is_waived():
            return Decimal(1), Decimal(1)

        assertion_ranks = [a.rank() for a in self.all_assertions()]

        rank = cast(Decimal, sum(r for r, m in assertion_ranks))
        max_rank = cast(Decimal, sum(m for r, m in assertion_ranks))

        return rank, max_rank

    def status(self) -> ResultStatus:
        if self.is_waived():
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
