from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class CourseResult:
    course: str
    rule: Any
    claim_attempt: Optional[Any]  # Optional[ClaimAttempt]
    min_grade_not_met: Optional[Any] = None  # Optional[CourseInstance]

    _ok: bool = field(init=False)
    _rank: int = field(init=False)

    def __post_init__(self):
        _ok = self.claim_attempt and self.claim_attempt.failed() is False and self.min_grade_not_met is None
        object.__setattr__(self, '_ok', _ok)

        _rank = 1 if self._ok else 0
        object.__setattr__(self, '_rank', _rank)

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "state": self.state(),
            "status": "pass" if self.ok() else "skip",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [c.to_dict() for c in self.claims()],
            "min_grade_not_met": self.min_grade_not_met.to_dict() if self.min_grade_not_met else None,
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
