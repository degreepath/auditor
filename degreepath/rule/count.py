from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple
import itertools
import logging

from ..base import Rule, BaseCountRule
from ..constants import Constants
from ..solution.count import CountSolution
from ..ncr import mult
from .assertion import AssertionRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountRule(Rule, BaseCountRule):
    items: Tuple[Rule, ...]

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

    @staticmethod  # noqa: C901
    def load(data: Dict, c: Constants, children: Dict, emphases: Sequence[Dict] = tuple()):
        from ..load_rule import load_rule

        extra_items: List = []
        if emphases:
            for r in emphases:
                emphasis_key = f"Emphasis: {r['name']}"
                children[emphasis_key] = r
                extra_items.append({"requirement": emphasis_key})

        if "all" in data:
            items = data["all"] + extra_items
            count = len(items)
        elif "any" in data:
            items = data["any"] + extra_items
            count = 1
        elif "both" in data:
            items = data["both"] + extra_items
            count = 2
            if len(items) != 2:
                raise Exception(f"expected two items in both; found {len(items)} items")
        elif "either" in data:
            items = data["either"] + extra_items
            count = 1
            if len(items) != 2:
                raise Exception(f"expected two items in both; found {len(items)} items")
        else:
            items = data["of"] + extra_items
            if data["count"] == "all":
                count = len(items)
            elif data["count"] == "any":
                count = 1
            else:
                count = int(data["count"])

        at_most = data.get('at_most', False)

        audit_clause = data.get('audit', None)
        if audit_clause is not None:
            if 'all' in audit_clause:
                audit_clauses = tuple([AssertionRule.load(audit, c=c) for audit in audit_clause['all']])
            else:
                audit_clauses = tuple([AssertionRule.load(audit_clause, c=c)])
        else:
            audit_clauses = tuple()

        return CountRule(
            count=count,
            items=tuple(load_rule(r, c, children) for r in items),
            at_most=at_most,
            audit_clauses=audit_clauses,
        )

    def validate(self, *, ctx):
        assert isinstance(self.count, int), f"{self.count} should be an integer"

        lo = self.count
        assert lo >= 0

        hi = self.count + 1 if self.at_most is True else len(self.items) + 1
        assert lo < hi

        for rule in self.items:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx, path: List):
        path = [*path, f".of"]
        # logger.debug("%s", path)

        lo = self.count
        hi = len(self.items) + 1 if self.at_most is False else self.count + 1

        all_children = set(self.items)
        item_indices = {r: self.items.index(r) for r in self.items}

        did_yield = False
        for r in range(lo, hi):
            # logger.debug("%s %s..<%s, r=%s", path, lo, hi, r)

            for combo_i, combo in enumerate(itertools.combinations(self.items, r)):
                logger.debug("%s %s..<%s, r=%s, combo=%s: generating product(*solutions)", path, lo, hi, r, combo_i)

                selected_children = set(combo)
                deselected_children = all_children.difference(selected_children)
                other_children = sorted(deselected_children, key=lambda r: item_indices[r])

                solutions = [
                    r.solutions(ctx=ctx, path=[*path, str(item_indices[r])])
                    for r in combo
                ]

                for solset_i, solutionset in enumerate(itertools.product(*solutions)):
                    did_yield = True

                    if solset_i > 0 and solset_i % 10_000 == 0:
                        logger.debug("%s %s..<%s, r=%s, combo=%s solset=%s: generating product(*solutions)", path, lo, hi, r, combo_i, solset_i)

                    yield CountSolution.from_rule(rule=self, items=solutionset + tuple(other_children))

        if not did_yield:
            logger.debug("%s did not iterate", path)
            # ensure that we always yield something
            yield CountSolution.from_rule(rule=self, items=self.items)

    def estimate(self, *, ctx):
        logger.debug('CountRule.estimate')

        lo = self.count
        hi = len(self.items) + 1 if self.at_most is False else self.count + 1

        did_yield = False
        iterations = 0
        for r in range(lo, hi):
            for combo in itertools.combinations(self.items, r):
                estimates = [rule.estimate(ctx=ctx) for rule in combo]
                product = mult(estimates)
                if product == 0 or product == 1:
                    iterations += sum(estimates)
                else:
                    iterations += product

        if not did_yield:
            iterations += 1

        logger.debug('CountRule.estimate: %s', iterations)

        return iterations
