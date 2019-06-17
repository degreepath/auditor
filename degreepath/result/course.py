from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from ..data import CourseInstance

if TYPE_CHECKING:
    from ..rule import CourseRule
    from ..requirement import Claim, ClaimAttempt


@dataclass(frozen=True)
class CourseResult:
    course: str
    rule: CourseRule
    claim_attempt: Optional[ClaimAttempt]

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
        return self.claim_attempt and self.claim_attempt.failed() == False

    def rank(self):
        return 1 if self.ok() else 0
