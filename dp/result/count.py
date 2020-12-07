import attr
from typing import Tuple, Union, Sequence, TYPE_CHECKING

from ..assertion_clause import SomeAssertion
from ..base.bases import Result, Rule, Solution
from ..base.count import BaseCountRule

if TYPE_CHECKING:  # pragma: no cover
    from ..solution.count import CountSolution


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountResult(Result, BaseCountRule):
    items: Tuple[Union[Rule, Solution, Result], ...]

    @staticmethod
    def from_solution(
        *,
        solution: 'CountSolution',
        items: Tuple[Union[Rule, Solution, Result], ...],
        audit_results: Tuple[SomeAssertion, ...],
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

    def audits(self) -> Sequence[SomeAssertion]:
        return self.audit_clauses

    def is_waived(self) -> bool:
        return self.overridden
