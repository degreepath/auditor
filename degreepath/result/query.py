from dataclasses import dataclass, field
from typing import Any, Tuple
from .assertion import AssertionResult


@dataclass(frozen=True)
class QueryResult:
    rule: Any
    successful_claims: Tuple
    failed_claims: Tuple
    success: bool
    resolved_assertions: Tuple[AssertionResult, ...]

    _ok: bool = field(init=False)
    _rank: int = field(init=False)

    # def __post_init__(self):
    #     self._ok = self.success == True
    #
    #     # TODO: fix this calculation so that it properly handles #154647's audit
    #     self._rank = len(self.successful_claims) + len(self.failed_claims)

    def __post_init__(self):
        _ok = self.success is True
        object.__setattr__(self, '_ok', _ok)

        _rank = len(self.successful_claims) + int(len(self.failed_claims) * 0.5)
        object.__setattr__(self, '_rank', _rank)

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "state": self.state(),
            "status": "pass" if self.ok() else "skip",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [c.to_dict() for c in self.claims()],
            "failures": [c.to_dict() for c in self.failed_claims],
            "assertions": [a.to_dict() for a in self.resolved_assertions],
        }

    def claims(self):
        return self.successful_claims

    def matched(self, *, ctx):
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)

    def state(self):
        return "result"

    def ok(self) -> bool:
        return self._ok

    def rank(self):
        return self._rank
