from typing import Tuple, Union, Sequence

import attr

from ..base.bases import Result, Rule, Solution
from ..base.count import BaseCountRule
from ..rule.assertion import AssertionRule

from .assertion import AssertionResult


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountResult(Result, BaseCountRule):
    items: Tuple[Union[Rule, Solution, Result], ...]
    audit_clauses: Tuple[Union[AssertionResult, AssertionRule], ...]
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseCountRule,
        items: Tuple[Union[Rule, Solution, Result], ...],
        audit_results: Tuple[Union[AssertionResult, AssertionRule], ...],
        overridden: bool = False,
    ) -> 'CountResult':
        return CountResult(
            count=solution.count,
            items=tuple(items),
            audit_clauses=audit_results,
            at_most=solution.at_most,
            path=solution.path,
            overridden=overridden,
        )

    def audits(self) -> Sequence[Union[AssertionResult, AssertionRule]]:
        return self.audit_clauses

    def waived(self) -> bool:
        return self.overridden
