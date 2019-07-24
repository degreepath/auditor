from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING, Any


@dataclass(frozen=True)
class CourseResult:
    course: str
    rule: Any
    claim_attempt: Any

    _ok: bool = field(init=False)
    _rank: int = field(init=False)

    def __post_init__(self):
        _ok = self.claim_attempt and self.claim_attempt.failed() is False
        object.__setattr__(self, '_ok', _ok)
        # self._ok = self.claim_attempt and self.claim_attempt.failed() is False

        _rank = 1 if self._ok else 0
        object.__setattr__(self, '_rank', _rank)
        # self._rank = 1 if self._ok else 0

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "state": self.state(),
            "status": "pass" if self.ok() else "skip",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    def claims(self):
        if self.claim_attempt:
            return [self.claim_attempt]
        else:
            return []

    def state(self):
        return "result"

    def ok(self) -> bool:
        return self._ok

    def rank(self):
        return self._rank
