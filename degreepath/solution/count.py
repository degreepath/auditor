from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Optional, Any, TYPE_CHECKING
import itertools
import logging

if TYPE_CHECKING:
    from ..rule import CountRule
    from ..result import Result
    from ..requirement import RequirementContext

from ..result import CountResult


@dataclass(frozen=True)
class CountSolution:
    items: List[Any]
    choices: List[Any]
    rule: CountRule

    def to_dict(self):
        return {
            **self.rule.to_dict(),
            "type": "count",
            "of": [item.to_dict() for item in self.items],
        }

    def audit(self, *, ctx) -> Result:
        lo = self.rule.count
        hi = len(self.items) + 1

        assert lo < hi

        best_combo = None
        best_combo_passed_count = None

        for n in range(lo, hi):
            logging.debug(f"CountSolution lo={lo}, hi={hi}, n={n}")

            for combo in itertools.combinations(self.items, n):
                results = [r.audit(ctx=ctx) for r in combo]
                passed_count = sum(1 for r in results if r.ok())

                if best_combo is None:
                    best_combo = results
                    best_combo_passed_count = passed_count

                if passed_count > best_combo_passed_count:
                    best_combo = results
                    best_combo_passed_count = passed_count

                if passed_count == len(results):
                    best_combo = results
                    best_combo_passed_count = passed_count
                    break

        assert best_combo

        return CountResult(items=best_combo, choices=self.choices)
