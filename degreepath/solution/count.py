from dataclasses import dataclass
from typing import Tuple, Union
import logging

from ..base import Solution, BaseCountRule, Rule, Result
from ..result.count import CountResult
from .query import apply_clause_to_query_rule
from ..result.assertion import AssertionResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountSolution(Solution, BaseCountRule):
    overridden: bool = False

    @staticmethod
    def from_rule(*, rule: BaseCountRule, items: Tuple[Union[Rule, Solution, Result], ...], overridden: bool = False):
        return CountSolution(
            count=rule.count,
            items=items,
            audit_clauses=rule.audit_clauses,
            at_most=rule.at_most,
            path=rule.path,
            overridden=overridden,
        )

    def audit(self, *, ctx):
        if self.overridden:
            return CountResult.from_solution(
                solution=self,
                items=tuple(self.items),
                audit_results=tuple(self.audit_clauses),
                overridden=self.overridden,
            )

        results = [
            r.audit(ctx=ctx) if isinstance(r, Solution) else r
            for i, r in enumerate(self.items)
        ]

        audit_results = []
        for i, clause in enumerate(self.audit_clauses):
            audit_path = tuple([*self.path, f"[{i}]"])

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

            result = clause.assertion.compare_and_resolve_with(
                value=matched_items,
                map_func=apply_clause_to_query_rule,
            )

            audit_results.append(AssertionResult(
                where=clause.where,
                assertion=result,
                path=audit_path,
            ))

        return CountResult.from_solution(
            solution=self,
            items=tuple(results),
            audit_results=tuple(audit_results),
        )
