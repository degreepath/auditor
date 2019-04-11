from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from .clause import Clause, SingleClause


@dataclass(frozen=True)
class Limit:
    at_most: int
    where: Clause

    def to_dict(self):
        return {"type": "limit", "at_most": self.at_most, "where": self.where.to_dict()}

    @staticmethod
    def load(data: Dict) -> Limit:
        return Limit(at_most=data["at_most"], where=SingleClause.load(data["where"]))
