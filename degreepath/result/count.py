from dataclasses import dataclass
from typing import Tuple, Union

from .assertion import AssertionResult
from ..rule.assertion import AssertionRule
from ..base import Result, BaseCountRule, Rule, ResultStatus, Solution


@dataclass(frozen=True)
class CountResult(Result, BaseCountRule):
    audit_results: Tuple[Union[AssertionResult, AssertionRule], ...]
    overridden: bool = False

    @staticmethod
    def from_solution(
        *,
        solution: BaseCountRule,
        items: Tuple[Union[Rule, Result, Solution], ...],
        audit_results: Tuple[Union[AssertionResult, AssertionRule], ...],
        overridden: bool = False,
    ) -> 'CountResult':
        return CountResult(
            count=solution.count,
            items=tuple(items),
            audit_clauses=solution.audit_clauses,
            at_most=solution.at_most,
            audit_results=audit_results,
            path=solution.path,
            overridden=overridden,
        )

    def audits(self):
        return self.audit_results

    def status(self):
        return ResultStatus.Pass if self.ok() else ResultStatus.Problem

    def claims(self):
        return [claim for item in self.items for claim in item.claims()]

    def was_overridden(self):
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        passed_count = sum(1 if r.ok() else 0 for r in self.items)
        audit_passed = len(self.audit_results) == 0 or all(a.ok() for a in self.audit_results)
        return passed_count >= self.count and audit_passed

    def rank(self):
        return sum(r.rank() for r in self.items)

    def max_rank(self):
        return sum(r.max_rank() for r in self.items)
