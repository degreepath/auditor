from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..requirement import ClaimAttempt
    from ..rule import FromRule


@dataclass(frozen=True)
class FromResult:
    rule: FromRule
    successful_claims: List[ClaimAttempt]
    failed_claims: List[ClaimAttempt]
    success: bool

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "state": self.state(),
            "status": "pass" if self.ok() else "skip",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [c.to_dict() for c in self.claims()],
            "failures": [c.to_dict() for c in self.failed_claims],
        }

    def claims(self):
        return self.successful_claims

    def state(self):
        return "result"

    def ok(self) -> bool:
        return self.success

    def rank(self):
        return len(self.successful_claims) + len(self.failed_claims)
