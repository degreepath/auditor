from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Tuple, List, Optional, TYPE_CHECKING
import re
import itertools
import logging
from functools import reduce

from ..solution import CountSolution
from .course import CourseRule

if TYPE_CHECKING:
    from ..requirement import RequirementContext
    from . import Rule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountRule:
    count: int
    of: Tuple[Rule, ...]

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

        potentials = [r for r in self.of if (not isinstance(r, CourseRule)) or ctx.find_course(r.course)]
        pot_hi = len(potentials) + 1

        # hi = max(min(hi, pot_hi), lo + 1)

        assert lo < hi

        size = len(self.of)

        all_children = set(self.of)

        for r in range(lo, hi):
            logger.warning(f"{path} {lo}..<{hi}, r={r}, max={len(potentials)}")
            for combo_i, combo in enumerate(itertools.combinations(self.of, r)):
                selected_children = set(combo)

                other_children = all_children.difference(selected_children)

                logger.debug(f"{path} combo={combo_i}: generating product(*solutions)")
                did_iter = True

                solutions = [
                    rule.solutions(ctx=ctx, path=[*path, f"idx={i}"])
                    for i, rule in enumerate(combo)
                ]

                for i, solutionset in enumerate(itertools.product(*solutions)):
                    if len(path) == 3:
                        solset = tuple(solutionset)
                        # flat = [x for s in solutionset for x in ]
                        y = CountSolution(
                            of=solset,
                            ignored=tuple(other_children),
                            count=self.count,
                            size=size,
                        )
                        flat = [x for x in y.flatten()]
                        rank = y.audit(ctx=ctx, path=[]).rank()

                        needle = set(['LATIN 111', 'LATIN 112', 'LATIN 231', 'LATIN 235', 'LATIN 252', 'LATIN 374', 'LATIN 375'])
                        # if needle.issubset(set(flat)):
                        if rank >= 12:
                            print(rank, flat)


                    logger.debug(f"{path} combo={combo_i}: iteration={i}")
                    solset = tuple(solutionset)
                    yield CountSolution(
                        of=solset,
                        ignored=tuple(other_children),
                        count=self.count,
                        size=size,
                    )

        if not did_iter:
            # ensure that we always yield something
            yield CountSolution(
                of=(), ignored=tuple(all_children), count=self.count, size=size
            )

    def estimate(self, *, ctx: RequirementContext):
        lo = self.count
        hi = len(self.of) + 1

        estimates = [rule.estimate(ctx=ctx) for rule in self.of]
        indices = [n for n, _ in enumerate(self.of)]

        count = 0
        for r in range(lo, hi):
            for combo in itertools.combinations(indices, r):
                inner = (estimates[i] for i in combo)
                count += reduce(lambda x, y: x * y, inner)

        return count
