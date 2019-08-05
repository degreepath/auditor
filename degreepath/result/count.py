from dataclasses import dataclass, field
from typing import Tuple
from .assertion import AssertionResult


@dataclass(frozen=True)
class CountResult:
    count: int
    items: Tuple
    audit_results: Tuple[AssertionResult, ...]

    _ok: bool = field(init=False)
    _rank: int = field(init=False)

    # def __post_init__(self):
    #     self._ok = sum(1 if r.ok() else 0 for r in self.items) >= self.count
    #
    #     self._rank = sum(r.rank() for r in self.items)

    def __post_init__(self):
        passed_count = sum(1 if r.ok() else 0 for r in self.items)
        audit_passed = len(self.audit_results) == 0 or all(a.ok() for a in self.audit_results)
        _ok = passed_count >= self.count and audit_passed
        object.__setattr__(self, '_ok', _ok)

        _rank = sum(r.rank() for r in self.items)
        object.__setattr__(self, '_rank', _rank)

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "audit": [a.to_dict() for a in self.audit_results],
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

    def matched(self, *, ctx):
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)

    def ok(self) -> bool:
        return self._ok

    def rank(self):
        return self._rank
