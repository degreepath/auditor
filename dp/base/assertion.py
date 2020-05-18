import attr
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal

from ..clause import Clause, SingleClause
from ..status import ResultStatus
from .bases import Base


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseAssertionRule(Base):
    assertion: SingleClause
    where: Optional[Clause]
    path: Tuple[str, ...]
    inserted: Tuple[str, ...]
    message: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "assertion": self.assertion.to_dict() if self.assertion else None,
            "where": self.where.to_dict() if self.where else None,
            "message": self.message,
            "inserted": list(self.inserted),
        }

    def type(self) -> str:
        return "assertion"

    def rank(self) -> Tuple[Decimal, Decimal]:
        status = self.status()

        if status is ResultStatus.Done or status is ResultStatus.Waived:
            return Decimal(1), Decimal(1)

        return self.assertion.rank()

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        return self.assertion.status()
