from dataclasses import dataclass
from typing import List, Tuple, Any
import logging

from ..result.count import CountResult
from ..rule.assertion import AssertionRule
from .query import apply_clause_to_query_rule
from ..result.assertion import AssertionResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountSolution:
    count: int
    items: Tuple
    audit_clauses: Tuple[AssertionRule, ...]

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
            "audit": [c.to_dict() for c in self.audit_clauses],
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [item for item in self.claims()],
        }

    def state(self):
        return "solution"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    @staticmethod
    def from_rule(rule: Any, *, items):
        return CountSolution(count=rule.count, items=items, audit_clauses=rule.audit_clauses)

    def audit(self, *, ctx, path: List):
        path = [*path, f".of"]

        results = [
            r.audit(ctx=ctx, path=[*path, i]) if r.state() == "solution" else r
            for i, r in enumerate(self.items)
        ]

        audit_results = []
        for clause in self.audit_clauses:
            matched_items = [
                item for sol in results
                # if hasattr(sol, 'matched')
                for item in sol.matched(ctx=ctx)
            ]

            if clause.where is not None:
                matched_items = [
                    item for item in matched_items
                    if item.apply_clause(clause.where)
                ]

            result = clause.assertion.compare_and_resolve_with(value=matched_items, map_func=apply_clause_to_query_rule)

            audit_results.append(AssertionResult(where=clause.where, assertion=result))

        return CountResult(count=self.count, items=tuple(results), audit_results=tuple(audit_results))
