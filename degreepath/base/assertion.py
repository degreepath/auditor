import attr
from typing import Optional, Tuple, Dict, Any
from ..clause import Clause

from .bases import Base


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseAssertionRule(Base):
    assertion: Clause
    where: Optional[Clause]
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "assertion": self.assertion.to_dict() if self.assertion else None,
            "where": self.where.to_dict() if self.where else None,
        }

    def type(self) -> str:
        return "assertion"

    def rank(self) -> int:
        return self.assertion.rank()

    def max_rank(self) -> int:
        return self.assertion.max_rank()
