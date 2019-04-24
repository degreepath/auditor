from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
import re
import itertools
import logging
from functools import reduce

if TYPE_CHECKING:
    from ..requirement import RequirementContext
    from . import Rule

from ..solution import CountSolution
from .course import CourseRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountRule:
    count: int
    items: Tuple[Rule, ...]

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
            "ok": self.ok(),
            "status": "skip",
            "claims": self.claims(),
        }

    def state(self):
        return "rule"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

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
            items = data["all"]
            count = len(items)
        elif "any" in data:
            items = data["any"]
            count = 1
        elif "both" in data:
            items = data["both"]
            count = 2
            if len(items) != 2:
                raise Exception(f"expected two items in both; found {len(items)} items")
        elif "either" in data:
            items = data["either"]
            count = 1
            if len(items) != 2:
                raise Exception(f"expected two items in both; found {len(items)} items")
        else:
            items = data["of"]
            if data["count"] == "all":
                count = len(items)
            elif data["count"] == "any":
                count = 1
            else:
                count = int(data["count"])

        return CountRule(count=count, items=tuple(load_rule(r) for r in items))

    def validate(self, *, ctx: RequirementContext):
        assert isinstance(self.count, int), f"{self.count} should be an integer"
        assert self.count >= 0
        assert self.count <= len(self.items)

        for rule in self.items:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List):
        path = [*path, f".of"]
        logger.debug(f"{path}")

        did_iter = False

        lo = self.count
        hi = len(self.items) + 1

        potentials = [
            r
            for r in self.items
            if (not isinstance(r, CourseRule)) or ctx.find_course(r.course)
        ]
        pot_hi = len(potentials) + 1

        assert lo < hi

        size = len(self.items)

        all_children = set(self.items)

        item_indices = {r: self.items.index(r) for r in self.items}

        for r in range(lo, hi):
            logger.debug(f"{path} {lo}..<{hi}, r={r}, max={len(potentials)}")

            for combo_i, combo in enumerate(itertools.combinations(self.items, r)):
                selected_children = set(combo)

                other_children = sorted(
                    list(all_children.difference(selected_children)),
                    key=lambda r: item_indices[r],
                )

                selected_original_indices = {}
                last_missing_idx = 0
                for idx, item in enumerate(self.items):
                    if item not in other_children:
                        selected_original_indices[item] = idx

                logger.debug(f"{path} combo={combo_i}: generating product(*solutions)")
                did_iter = True

                solutions = [rule.solutions(ctx=ctx, path=path) for rule in combo]

                # print("combo", combo)

                for solutionset in itertools.product(*solutions):

                    # print("solset", solutionset)

                    # todo: clean up this block
                    req_ident_map: Dict[int, int] = {}
                    do_not_yield = False

                    cleaned = []

                    for rulesol in solutionset:
                        if isinstance(rulesol, tuple):
                            req_ident, req_idx = rulesol[0]

                            req_ident_map.setdefault(req_ident, req_idx)

                            if req_ident_map[req_ident] != req_idx:
                                do_not_yield = True
                                break

                            solution = rulesol[1]
                        else:
                            solution = rulesol

                        cleaned.append(solution)

                    if do_not_yield:
                        continue
                    # end clean-up-this-block

                    solset = cleaned + other_children

                    # ordered_solset = sorted(
                    #     solset,
                    #     key=lambda r: item_indices[r]
                    #     # if r in item_indices
                    #     # else selected_original_indices[r],
                    # )

                    tuple_solset = tuple(solset)

                    yield CountSolution.from_rule(self, items=tuple_solset)

        if not did_iter:
            # ensure that we always yield something
            yield CountSolution.from_rule(self, items=self.items)

    def estimate(self, *, ctx: RequirementContext):
        lo = self.count
        hi = len(self.items) + 1

        estimates = [rule.estimate(ctx=ctx) for rule in self.items]
        indices = [n for n, _ in enumerate(self.items)]

        count = 0
        for r in range(lo, hi):
            for combo in itertools.combinations(indices, r):
                inner = (estimates[i] for i in combo)
                count += reduce(lambda x, y: x * y, inner)

        return count
