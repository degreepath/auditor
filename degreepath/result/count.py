import attr
from typing import Tuple, Union, Sequence, List, cast

from ..base import Result, BaseCountRule, BaseCourseRule, Rule, Solution, BaseAssertionRule


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CountResult(Result, BaseCountRule):
    audit_results: Tuple[BaseAssertionRule, ...]
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseCountRule,
        items: Tuple[Union[Rule, Result, Solution, BaseCourseRule], ...],
        audit_results: Tuple[BaseAssertionRule, ...],
        overridden: bool = False,
    ) -> Union['CountResult', BaseCourseRule]:
        filtered: List[Union[Rule, Result, Solution, BaseCourseRule]] = []

        for item in items:
            if not isinstance(item, BaseCourseRule):
                filtered.append(item)
                continue

            if item.ok() is True:
                filtered.append(item)
                continue

            if item.hidden is False:
                filtered.append(item)
                continue

        casted = cast(List[Union[Rule, Result, Solution]], filtered)

        if solution.count == len(items):
            count = len(casted)
        elif solution.count > len(casted):
            count = len(casted)
        else:
            count = solution.count

        if not overridden and not solution.audit_clauses and count == 1 and len(filtered) == 1 and isinstance(filtered[0], BaseCourseRule):
            return cast(Union['CountResult', BaseCourseRule], casted[0])

        return CountResult(
            count=count,
            items=tuple(casted),
            audit_clauses=solution.audit_clauses,
            at_most=solution.at_most,
            audit_results=audit_results,
            path=solution.path,
            overridden=overridden,
        )

    def audits(self) -> Sequence[BaseAssertionRule]:
        return self.audit_results

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        passed_count = sum(1 if r.ok() else 0 for r in self.items)
        audit_passed = len(self.audit_results) == 0 or all(a.ok() for a in self.audit_results)
        return passed_count >= self.count and audit_passed
