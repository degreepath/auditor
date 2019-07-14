from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Any


@dataclass(frozen=True)
class CourseResult:
    course: str
    rule: Any
    claim_attempt: Any

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
        return self.claim_attempt and self.claim_attempt.failed() is False

    def rank(self):
        return 1 if self.ok() else 0