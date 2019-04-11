from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Tuple, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..requirement import RequirementContext
from ..solution import CountSolution

if TYPE_CHECKING:
    from . import Rule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountRule:
    count: int
    of: Tuple[Rule]

    def to_dict(self):
        return {
            "type": "count",
            "count": self.count,
            "size": len(self.of),
            "of": tuple(item.to_dict() for item in self.of),
            "ignored": tuple(),
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

        return CountRule(count=count, of=tuple(load_rule(r) for r in of))

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.count, int), f"{self.count} should be an integer"
        assert self.count >= 0
        assert self.count <= len(self.of)

        for rule in self.of:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List):
        path = [*path, f".of"]
        logger.debug(f"{path}")

        did_iter = False

        lo = self.count
        hi = len(self.of) + 1

        assert lo < hi

        size = len(self.of)

        # print(self.of)
        all_children = set(self.of)

        for r in range(lo, hi):
            logger.debug(f"{path} {lo}..<{hi}, r={r}")
            for combo_i, combo in enumerate(itertools.combinations(self.of, r)):
                selected_children = set(combo)

                other_children = all_children.difference(selected_children)
                # print(all_children)
                # print(selected_children)
                # print(other_children)
                # print()

                logger.debug(f"{path} combo={combo_i}: generating product(*solutions)")
                did_iter = True

                solutions = [
                    rule.solutions(ctx=ctx, path=[*path, f"idx={i}"])
                    for i, rule in enumerate(combo)
                ]

                for i, solutionset in enumerate(itertools.product(*solutions)):
                    logger.debug(f"{path} combo={combo_i}: iteration={i}")
                    solset = list(solutionset)
                    yield CountSolution(of=solset, ignored=other_children, count=self.count, size=size)

        if not did_iter:
            # ensure that we always yield something
            yield CountSolution(of=[], ignored=all_children, rule=self, count=self.count, size=size)
