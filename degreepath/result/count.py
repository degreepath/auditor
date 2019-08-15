from dataclasses import dataclass
from typing import Tuple, Union, Sequence, List

from ..base import Result, BaseCountRule, Rule, ResultStatus, Solution, BaseAssertionRule
from ..claim import ClaimAttempt


@dataclass(frozen=True)
class CountResult(Result, BaseCountRule):
    __slots__ = ('audit_results', 'overridden')
    audit_results: Tuple[BaseAssertionRule, ...]
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseCountRule,
        items: Tuple[Union[Rule, Result, Solution], ...],
        audit_results: Tuple[BaseAssertionRule, ...],
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

    def audits(self) -> Sequence[BaseAssertionRule]:
        return self.audit_results

    def status(self) -> ResultStatus:
        return ResultStatus.Pass if self.ok() else ResultStatus.Problem

    def claims(self) -> List[ClaimAttempt]:
        return [claim for item in self.items for claim in item.claims()]

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        passed_count = sum(1 if r.ok() else 0 for r in self.items)
        audit_passed = len(self.audit_results) == 0 or all(a.ok() for a in self.audit_results)
        return passed_count >= self.count and audit_passed
