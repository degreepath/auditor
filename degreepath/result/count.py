from dataclasses import dataclass, field
from typing import Tuple, Optional
from ..clause import ResolvedClause


@dataclass(frozen=True)
class CountResult:
    count: int
    items: Tuple
    audit_result: Optional[ResolvedClause]

    _ok: bool = field(init=False)
    _rank: int = field(init=False)

    # def __post_init__(self):
    #     self._ok = sum(1 if r.ok() else 0 for r in self.items) >= self.count
    #
    #     self._rank = sum(r.rank() for r in self.items)

    def __post_init__(self):
        passed_count = sum(1 if r.ok() else 0 for r in self.items)
        audit_passed = self.audit_result is None or self.audit_result.result == True
        _ok = passed_count >= self.count and audit_passed
        object.__setattr__(self, '_ok', _ok)

        _rank = sum(r.rank() for r in self.items)
        object.__setattr__(self, '_rank', _rank)

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "audit": self.audit_result.to_dict() if self.audit_result is not None else None,
            "items": [x.to_dict() for x in self.items],
            "status": "pass" if self.ok() else "problem",
            "rank": self.rank(),
            "ok": self.ok(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    def state(self):
        return "result"

    def claims(self):
        return [claim for item in self.items for claim in item.claims()]

    def ok(self) -> bool:
        return self._ok

    def rank(self):
        return self._rank
