from dataclasses import dataclass
from typing import Tuple

from .assertion import AssertionResult
from ..base import Result, BaseCountRule, Rule


@dataclass(frozen=True)
class CountResult(Result, BaseCountRule):
    audit_results: Tuple[AssertionResult, ...]

    @staticmethod
    def from_solution(*, solution: BaseCountRule, items: Tuple[Rule, ...], audit_results=Tuple[AssertionResult, ...]):
        return CountResult(
            count=solution.count,
            items=items if isinstance(items, tuple) else tuple(items),
            audit_clauses=solution.audit_clauses,
            at_most=solution.at_most,
            audit_results=audit_results,
            path=solution.path,
        )

    def status(self):
        return "pass" if self.ok() else "problem"

    def claims(self):
        return [claim for item in self.items for claim in item.claims()]

    def ok(self) -> bool:
        passed_count = sum(1 if r.ok() else 0 for r in self.items)
        audit_passed = len(self.audit_results) == 0 or all(a.ok() for a in self.audit_results)
        return passed_count >= self.count and audit_passed

    def rank(self):
        return sum(r.rank() for r in self.items)

    def max_rank(self):
        return sum(r.max_rank() for r in self.items)
