from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..requirement import RequirementContext
from ..solution import CountSolution

if TYPE_CHECKING:
    from . import Rule


@dataclass(frozen=True)
class CountRule:
    count: int
    of: List[Rule]

    def to_dict(self):
        return {
            "type": "count",
            "count": self.count,
            "of": [item.to_dict() for item in self.of],
        }

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "count" in data and "of" in data:
            return True
        if "all" in data:
            return True
        if "any" in data:
            return True
        if "both" in data:
            return True
        if "either" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> CountRule:
        from . import load_rule

        if "all" in data:
            of = data["all"]
            count = len(of)
        elif "any" in data:
            of = data["any"]
            count = 1
        elif "both" in data:
            of = data["both"]
            count = 2
            if len(of) != 2:
                raise Exception(f"expected two items in both; found {len(of)} items")
        elif "either" in data:
            of = data["either"]
            count = 1
            if len(of) != 2:
                raise Exception(f"expected two items in both; found {len(of)} items")
        else:
            of = data["of"]
            if data["count"] == "all":
                count = len(of)
            elif data["count"] == "any":
                count = 1
            else:
                count = int(data["count"])

        return CountRule(count=count, of=[load_rule(r) for r in of])

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.count, int), f"{self.count} should be an integer"
        assert self.count >= 0
        assert self.count <= len(self.of)

        for rule in self.of:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List):
        path = [*path, f".of({self.count}/{len(self.of)})"]
        logging.debug(f"{path}\n\tneed {self.count} of {len(self.of)} items")

        did_iter = False

        lo = self.count
        hi = len(self.of) + 1

        assert lo < hi

        for n in range(lo, hi):
            for combo in itertools.combinations(self.of, lo):
                did_iter = True

                with_solutions = [
                    rule.solutions(ctx=ctx, path=[*path, f"$of[{i}]"])
                    for i, rule in enumerate(combo)
                ]

                for i, ruleset in enumerate(itertools.product(*with_solutions)):
                    msg = f"{[*path, f'$of/product#{i}']}\n\t{ruleset}"
                    yield CountSolution(items=list(ruleset), choices=self.of, rule=self)

        if not did_iter:
            # be sure that we always yield something
            yield CountSolution(items=[], choices=self.of, rule=self)
