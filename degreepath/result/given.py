from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Any


@dataclass(frozen=True)
class FromResult:
    rule: Any
    successful_claims: List
    failed_claims: List
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
        # TODO: fix this calculation so that it properly handles #154647's audit
        return len(self.successful_claims) + len(self.failed_claims)
