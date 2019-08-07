from dataclasses import dataclass, field
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequirementResult:
    name: str
    message: Optional[str] = None
    result: Optional[Any] = None
    audited_by: Optional[str] = None
    contract: bool = False

    _ok: bool = field(init=False)
    _rank: int = field(init=False)
    _max_rank: int = field(init=False)

    def __post_init__(self):
        _ok = self.result.ok() if self.result else False
        # _ok = True if self.audited_by is not None else _ok
        object.__setattr__(self, '_ok', _ok)

        boost = 1 if self._ok else 0
        _rank = self.result.rank() + boost if self.result else 0
        object.__setattr__(self, '_rank', _rank)

        _max_rank = self.result.max_rank() + 1 if self.result else 0
        object.__setattr__(self, '_max_rank', _max_rank)

    # sol: RequirementSolution
    @staticmethod
    def from_solution(sol: Any, *, result: Optional[Any]):
        return RequirementResult(
            name=sol.name,
            message=sol.message,
            audited_by=sol.audited_by,
            contract=sol.contract,
            result=result,
        )

    def to_dict(self):
        return {
            "type": "requirement",
            "name": self.name,
            "message": self.message,
            "result": self.result.to_dict() if self.result else None,
            "audited_by": self.audited_by,
            "contract": self.contract,
            "state": self.state(),
            "status": "pass" if self.ok() else "problem",
            "ok": self.ok(),
            "rank": self.rank(),
            "max_rank": self.max_rank(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    def state(self):
        if self.audited_by:
            return "result"
        if not self.result:
            return []
        return self.result.state()

    def claims(self):
        if self.audited_by:
            return []
        if not self.result:
            return []
        return self.result.claims()

    def matched(self, *, ctx):
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)

    def ok(self) -> bool:
        return self._ok

    def rank(self):
        return self._rank

    def max_rank(self):
        return self._max_rank
