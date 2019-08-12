from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, Iterator, TYPE_CHECKING
import itertools
import logging

from ..base import Rule, BaseCountRule
from ..constants import Constants
from ..exception import InsertionException
from ..solution.count import CountSolution
from ..ncr import mult
from .course import CourseRule
from .assertion import AssertionRule

if TYPE_CHECKING:
    from ..context import RequirementContext

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
    def load(
        data: Dict, *,
        c: Constants,
        children: Dict[str, Dict],
        path: List[str],
        emphases: Sequence[Dict[str, Dict]] = tuple(),
    ) -> 'CountRule':
        from ..load_rule import load_rule

        path = [*path, f".count"]

        children_with_emphases = {**children}
        extra_items: List = []
        if emphases:
            for r in emphases:
                emphasis_key = f"Emphasis: {r['name']}"
                children_with_emphases[emphasis_key] = r
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
        audit_clauses: Tuple[AssertionRule, ...] = tuple()

        if audit_clause is not None:
            if 'all' in audit_clause:
                audit_clauses = tuple(
                    AssertionRule.load(audit, c=c, path=[*path, ".audit", f"[{i}]"])
                    for i, audit in enumerate(audit_clause['all'])
                )
            else:
                audit_clauses = tuple([AssertionRule.load(audit_clause, c=c, path=[*path, ".audit", "[0]"])])

        loaded_items = tuple(
            load_rule(data=r, c=c, children=children_with_emphases, path=[*path, f"[{i}]"])
            for i, r in enumerate(items)
        )

        return CountRule(
            count=count,
            items=loaded_items,
            at_most=at_most,
            audit_clauses=audit_clauses,
            path=tuple(path),
        )

    def validate(self, *, ctx: 'RequirementContext') -> None:
        assert isinstance(self.count, int), f"{self.count} should be an integer"

        lo = self.count
        assert lo >= 0

        hi = self.count + 1 if self.at_most is True else len(self.items) + 1
        assert lo < hi

        for rule in self.items:
            rule.validate(ctx=ctx)

    def solutions(self, *, ctx: 'RequirementContext') -> Iterator[CountSolution]:
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        exception = ctx.get_exception(self.path)
        if exception and exception.is_pass_override():
            logger.debug("forced override on %s", self.path)
            yield CountSolution.from_rule(rule=self, count=self.count, items=self.items, overridden=True)
            return

        items = self.items
        count = self.count

        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            logger.debug("inserting new choice into %s: %s", self.path, exception)

            # if this is an `all` rule, we want to keep it as an `all` rule, so we need to increase `count`
            if count == len(items) and count > 1:
                logger.debug("incrementing count b/c 'all' rule at %s", self.path)
                count += 1

            matched_course = ctx.forced_course_by_clbid(exception.clbid)

            new_rule = CourseRule(
                course=matched_course.course(),
                hidden=False,
                grade=None,
                allow_claimed=False,
                path=tuple([*self.path, f"*{matched_course.course()}"]),
            )

            logger.debug("new choice at %s is %s", self.path, new_rule)

            items = tuple([new_rule, *self.items])

        lo = count
        hi = len(items) + 1 if self.at_most is False else count + 1

        all_children = set(items)
        item_indices = {r: items.index(r) for r in items}

        did_yield = False
        for r in range(lo, hi):
            # logger.debug("%s %s..<%s, r=%s", path, lo, hi, r)

            for combo_i, combo in enumerate(itertools.combinations(items, r)):
                if debug: logger.debug("%s %s..<%s, r=%s, combo=%s: generating product(*solutions)", self.path, lo, hi, r, combo_i)

                selected_children = set(combo)
                deselected_children = all_children.difference(selected_children)
                other_children = sorted(deselected_children, key=lambda r: item_indices[r])

                # itertools.product does this internally, so we'll pre-compute the results here
                # to make it obvious that it's not lazy
                solutions = [tuple(r.solutions(ctx=ctx)) for r in combo]

                for solset_i, solutionset in enumerate(itertools.product(*solutions)):
                    did_yield = True

                    if debug and solset_i > 0 and solset_i % 10_000 == 0:
                        logger.debug("%s %s..<%s, r=%s, combo=%s solset=%s: generating product(*solutions)", self.path, lo, hi, r, combo_i, solset_i)

                    yield CountSolution.from_rule(rule=self, count=count, items=solutionset + tuple(other_children))

        if not did_yield:
            logger.debug("%s did not iterate", self.path)
            # ensure that we always yield something
            yield CountSolution.from_rule(rule=self, count=count, items=items)

    def estimate(self, *, ctx: 'RequirementContext') -> int:
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
