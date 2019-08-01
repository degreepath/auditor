from dataclasses import dataclass
from typing import Dict, List, Tuple
import itertools
import logging

from ..constants import Constants
from ..solution.count import CountSolution
from .assertion import AssertionRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountRule:
    count: int
    items: Tuple
    at_most: bool
    audit_clauses: Tuple[AssertionRule, ...]

    def to_dict(self):
        return {
            "type": "count",
            "state": self.state(),
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
            "audit": [c.to_dict() for c in self.audit_clauses],
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

    @staticmethod  # noqa: C901
    def load(data: Dict, c: Constants):
        from ..load_rule import load_rule

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
            items=tuple(load_rule(r, c) for r in items),
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
        logger.debug("%s", path)

        lo = self.count
        hi = len(self.items) + 1 if self.at_most is False else self.count + 1

        all_children = set(self.items)
        item_indices = {r: self.items.index(r) for r in self.items}

        did_yield = False
        for r in range(lo, hi):
            logger.debug("%s %s..<%s, r=%s", path, lo, hi, r)

            for combo_i, combo in enumerate(itertools.combinations(self.items, r)):
                logger.debug("%s %s..<%s, r=%s, combo=%s: generating product(*solutions)", path, lo, hi, r, combo_i)

                selected_children = set(combo)
                other_children = sorted(all_children.difference(selected_children), key=lambda r: item_indices[r])

                solutions = [rule.solutions(ctx=ctx, path=[*path, item_indices[rule]]) for rule in combo]

                for solset_i, solutionset in enumerate(itertools.product(*solutions)):
                    if solset_i > 0 and solset_i % 10_000 == 0:
                        logger.debug("%s %s..<%s, r=%s, combo=%s solset=%s: generating product(*solutions)", path, lo, hi, r, combo_i, solset_i)

                    did_yield = True

                    solset = solutionset + tuple(other_children)

                    yield CountSolution.from_rule(self, items=solset)

        if not did_yield:
            logger.debug("%s did not iterate", path)
            # ensure that we always yield something
            yield CountSolution.from_rule(self, items=self.items)
