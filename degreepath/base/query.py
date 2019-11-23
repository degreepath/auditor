import attr
from typing import Optional, Tuple, Dict, Any, Sequence, Union
import enum

from .bases import Base, Summable
from ..limit import LimitSet
from ..clause import Clause
from ..claim import ClaimAttempt
from ..rule.assertion import AssertionRule, ConditionalAssertionRule
from .assertion import BaseAssertionRule


@enum.unique
class QuerySource(enum.Enum):
    Courses = "courses"
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
    path: Tuple[str, ...]
    inserted: Tuple[str, ...]

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

    def only_failed_claims(self) -> Sequence[ClaimAttempt]:
        return []

    def all_assertions(self) -> Sequence[Union[BaseAssertionRule, ConditionalAssertionRule]]:
        return self.assertions

    def type(self) -> str:
        return "query"

    def rank(self) -> Summable:
        return 0

    def max_rank(self) -> Summable:
        return sum(a.max_rank() for a in self.assertions)

    def in_progress(self) -> bool:
        if 0 < self.rank() < self.max_rank():
            return True

        if any(c.is_in_progress for c in self.matched()):
            return True

        if any(c.in_progress() for c in self.all_assertions()):
            return True

        return False
