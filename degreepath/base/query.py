import attr
from typing import Optional, Tuple, Dict, Any
import enum

from .bases import Base, Summable
from ..limit import LimitSet
from ..clause import Clause
from ..rule.assertion import AssertionRule


@enum.unique
class QuerySource(enum.Enum):
    Student = "student"


@enum.unique
class QuerySourceType(enum.Enum):
    Courses = "courses"
    Areas = "areas"
    MusicPerformances = "music performances"


@enum.unique
class QuerySourceRepeatMode(enum.Enum):
    First = "first"
    All = "all"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseQueryRule(Base):
    source: QuerySource
    source_type: QuerySourceType
    source_repeats: QuerySourceRepeatMode
    assertions: Tuple[AssertionRule, ...]
    limit: LimitSet
    where: Optional[Clause]
    allow_claimed: bool
    attempt_claims: bool
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "source": self.source.value,
            "source_type": self.source_type.value,
            "source_repeats": self.source_repeats.value,
            "limit": self.limit.to_dict(),
            "assertions": [a.to_dict() for a in self.assertions],
            "where": self.where.to_dict() if self.where else None,
            "allow_claimed": self.allow_claimed,
            "claims": [c.to_dict() for c in self.claims()],
            "failures": [],
        }

    def type(self) -> str:
        return "query"

    def rank(self) -> Summable:
        return 0

    def max_rank(self) -> Summable:
        return sum(a.max_rank() for a in self.assertions)
