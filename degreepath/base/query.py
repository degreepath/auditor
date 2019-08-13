from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import enum

from .bases import Base
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


@dataclass(frozen=True)
class BaseQueryRule(Base):
    __slots__ = ('source', 'source_type', 'source_repeats', 'assertions', 'limit', 'where', 'allow_claimed', 'attempt_claims')
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
            "failures": [],
        }

    def type(self) -> str:
        return "query"
