from dataclasses import dataclass
from typing import Optional
from ..clause import Clause

from .bases import Base


@dataclass(frozen=True)
class BaseAssertionRule(Base):
    assertion: Clause
    where: Optional[Clause]

    def to_dict(self):
        return {
            **super().to_dict(),
            "assertion": self.assertion.to_dict() if self.assertion else None,
            "where": self.where.to_dict() if self.where else None,
        }

    def type(self):
        return "assertion"
