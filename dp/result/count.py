import attr
from typing import Tuple, Union, Sequence, TYPE_CHECKING

from .assertion import AssertionResult
from ..base.bases import Result, Rule, Solution
from ..base.count import BaseCountRule
from ..rule.assertion import AssertionRule
from ..status import ResultStatus, PassingStatuses

if TYPE_CHECKING:  # pragma: no cover
    from ..solution.count import CountSolution


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountResult(Result, BaseCountRule):
    items: Tuple[Union[Rule, Solution, Result], ...]
    audit_clauses: Tuple[Union[AssertionResult, AssertionRule], ...]
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: 'CountSolution',
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

    def status(self) -> ResultStatus:
        if self.waived():
            return ResultStatus.Waived

        all_child_statuses = [r.status() for r in self.items]
        all_passing_child_statuses = [s for s in all_child_statuses if s in PassingStatuses]
        passing_child_statuses = set(all_passing_child_statuses)
        passing_child_count = len(all_passing_child_statuses)

        all_audit_statuses = set(a.status() for a in self.audits())

        # if all rules and audits have been waived, pretend that we're waived as well
        if passing_child_statuses == WAIVED_ONLY and all_audit_statuses.issubset(WAIVED_ONLY):
            return ResultStatus.Waived

        if passing_child_count == 0:
            return ResultStatus.Empty

        if passing_child_count < self.count:
            return ResultStatus.NeedsMoreItems

        if passing_child_statuses.issubset(WAIVED_AND_DONE) and all_audit_statuses.issubset(WAIVED_AND_DONE):
            return ResultStatus.Done

        if passing_child_statuses.issubset(WAIVED_DONE_CURRENT) and all_audit_statuses.issubset(WAIVED_DONE_CURRENT):
            return ResultStatus.PendingCurrent

        if passing_child_statuses.issubset(WAIVED_DONE_CURRENT_PENDING) and all_audit_statuses.issubset(WAIVED_DONE_CURRENT_PENDING):
            return ResultStatus.PendingRegistered

        return ResultStatus.NeedsMoreItems


WAIVED_ONLY = frozenset({ResultStatus.Waived})
WAIVED_AND_DONE = frozenset({ResultStatus.Done, ResultStatus.Waived})
WAIVED_DONE_CURRENT = frozenset({ResultStatus.Done, ResultStatus.Waived, ResultStatus.PendingCurrent})
WAIVED_DONE_CURRENT_PENDING = frozenset({ResultStatus.Done, ResultStatus.Waived, ResultStatus.PendingCurrent, ResultStatus.PendingRegistered})
