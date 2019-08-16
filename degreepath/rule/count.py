from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, Iterator, Collection, Set, FrozenSet, Optional, Union, TYPE_CHECKING
import itertools
import logging

from ..base import Rule, BaseCountRule, Result, Solution
from ..constants import Constants
from ..exception import InsertionException
from ..solution.count import CountSolution
from ..ncr import mult
from .course import CourseRule
from .assertion import AssertionRule

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CountRule(Rule, BaseCountRule):
    __slots__ = ()

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

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[CountSolution]:
        exception = ctx.get_exception(self.path)
        if exception and exception.is_pass_override():
            logger.debug("%s forced override", self.path)
            yield CountSolution.from_rule(rule=self, count=self.count, items=self.items, overridden=True)
            return

        items = self.items
        count = self.count

        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            logger.debug("%s inserting new choice: %s", self.path, exception)

            # if this is an `all` rule, we want to keep it as an `all` rule, so we need to increase `count`
            if count == len(items) and count > 1:
                logger.debug("%s incrementing count b/c 'all' rule", self.path)
                count += 1

            matched_course = ctx.forced_course_by_clbid(exception.clbid)

            new_rule = CourseRule(
                course=matched_course.course(),
                hidden=False,
                grade=None,
                allow_claimed=False,
                path=tuple([*self.path, f"[{len(items)}]", f"*{matched_course.course()}"]),
            )

            logger.debug("%s new choice is %s", self.path, new_rule)

            items = tuple([*items, new_rule])

        lo = count
        hi = len(items) + 1 if self.at_most is False else count + 1

        logger.debug('%s discovering children with potential', self.path)
        all_potential_rules = set(rule for rule in items if rule.has_potential(ctx=ctx))

        if depth == 1 and all_potential_rules and not self.audit_clauses:
            logger.debug('%s searching for disjoint children', self.path)
            separated_children = self.find_independent_children(items=all_potential_rules, ctx=ctx)

            independent_children = separated_children['disjoint']
            codependent_children = separated_children['non_disjoint']

            independent_rule__results = self.solve_independent_children(ctx=ctx, independent_children=independent_children)

            potential_rules = tuple(sorted(codependent_children))
            solved_results: Tuple[Result, ...] = tuple(sorted(result for result in independent_rule__results.values() if result is not None))
            solved_results__rules: Set[Rule] = set(r for r, result in independent_rule__results.items() if result is not None)
        else:
            solved_results = tuple()
            solved_results__rules = set()
            potential_rules = tuple(sorted(all_potential_rules))

        logger.debug('%s potential rules are %s', self.path, [r.path for r in potential_rules])
        logger.debug('%s solved rules are %s', self.path, [r.path for r in solved_results__rules])

        potential_len = len(potential_rules)
        all_children = set(items)

        did_yield = False

        logger.debug("%s iterating over combinations between %s..<%s", self.path, lo, hi)
        for r in range(lo, hi):
            logger.debug("%s %s..<%s, r=%s", self.path, lo, hi, r)
            for combo in self.make_combinations(items=potential_rules, results=solved_results, children_with_results=solved_results__rules, all_children=all_children, r=r, count=count, ctx=ctx):
                did_yield = True
                yield combo

        if not did_yield and potential_len > 0:
            # didn't have enough potential children to iterate in range(lo, hi)
            logger.debug("%s only iterating over the %s children with potential", self.path, potential_len)
            for combo in self.make_combinations(items=potential_rules, results=solved_results, children_with_results=solved_results__rules, all_children=all_children, r=potential_len, count=count, ctx=ctx):
                did_yield = True
                yield combo

        if not did_yield:
            logger.debug("%s did not iterate", self.path)
            # ensure that we always yield something
            logger.debug('all_children: %s', [r.path for r in all_children])
            logger.debug('solved_results__rules: %s', [r.path for r in solved_results__rules])

            children_with_precomputed_solutions: Set[Union[Rule, Result]] = set(all_children - solved_results__rules)
            logger.debug('children_with_precomputed_solutions: %s', [r.path for r in children_with_precomputed_solutions])

            children_with_precomputed_solutions.update(solved_results)
            logger.debug('children_with_precomputed_solutions, post-update: %s', [(r.path, r.state()) for r in children_with_precomputed_solutions])

            to_yield = tuple(sorted(children_with_precomputed_solutions))
            logger.debug('to_yield: %s', [(r.path, r.state()) for r in to_yield])

            yield CountSolution.from_rule(rule=self, count=count, items=to_yield)

    def make_combinations(
        self, *,
        ctx: 'RequirementContext',
        items: Tuple[Rule, ...],
        results: Tuple[Result, ...],
        children_with_results: Set[Rule],
        all_children: Set[Rule],
        r: int,
        count: int,
    ) -> Iterator[CountSolution]:
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        for combo_i, selected_children in enumerate(itertools.combinations(items, r)):
            if debug: logger.debug("%s, r=%s, combo=%s: generating product(*solutions)", self.path, r, combo_i)

            deselected_children_set = set(all_children - children_with_results).difference(set(selected_children))
            deselected_children: Tuple[Union[Rule, Result, Solution], ...] = tuple(deselected_children_set)

            # itertools.product does this internally, so we'll pre-compute the results here
            # to make it obvious that it's not lazy
            solutions_dict = {r: tuple(r.solutions(ctx=ctx)) for r in selected_children}
            solutions = tuple(solutions_dict.values())

            lengths = {r.path: len(s) for r, s in solutions_dict.items()}
            print(lengths)
            logger.debug(f"%s emitting {mult(lengths.values()):,} solutions (%s)" % (self.path, lengths))

            solutionset: Tuple[Union[Rule, Solution, Result], ...]
            for solset_i, solutionset in enumerate(itertools.product(*solutions)):
                if debug and solset_i > 0 and solset_i % 10_000 == 0:
                    logger.debug("%s, r=%s, combo=%s solset=%s: generating product(*solutions)", self.path, r, combo_i, solset_i)

                to_yield = tuple(sorted(solutionset + deselected_children + results))
                yield CountSolution.from_rule(rule=self, count=count, items=to_yield)

    def find_independent_children(self, *, items: Collection[Rule], ctx: 'RequirementContext') -> Dict[str, Collection[Rule]]:
        """
        We want to find each child rule that has no claimable overlap with any other child rule.

        1. We only run this on a top-level CountRule
        2. We collect all of the "matches" of each child rule as sets of courses
        3. We look for the sets that are disjoint with every other set

        I benchmarked five implementations of this logic; see benchmarks/bench_disjoints.py

        Please add a benchmark suite in there, and make sure your changes are
        equivalent/faster, or just more correct.
        """

        logger.debug("%s searching the following for independence %s", self.path, [r.path for r in items])

        all_rule_matches: Dict[Rule, FrozenSet['Clausable']] = {
            r: frozenset(r.all_matches(ctx=ctx))
            for r in items
        }

        if len(all_rule_matches) == 1:
            logger.debug("%s early-exit because there's only one potential child", self.path)
            return {'disjoint': set(all_rule_matches.keys()), 'non_disjoint': set()}

        non_disjoint_rules: Set[Rule] = set()
        disjoint_rules: Set[Rule] = set()

        for (rule_a, a_matches), (rule_b, b_matches) in itertools.combinations(all_rule_matches.items(), 2):
            if a_matches.isdisjoint(b_matches):
                disjoint_rules.add(rule_a)
                disjoint_rules.add(rule_b)
            else:
                non_disjoint_rules.add(rule_a)
                non_disjoint_rules.add(rule_b)

        for s in non_disjoint_rules:
            disjoint_rules.discard(s)

        logger.debug("found disjoint rules: %s", [r.path for r in disjoint_rules])
        logger.debug("found non-disjoint rules: %s", [r.path for r in non_disjoint_rules])

        return {'disjoint': disjoint_rules, 'non_disjoint': non_disjoint_rules}

    def solve_independent_children(self, *, ctx: 'RequirementContext', independent_children: Collection[Rule]) -> Dict[Rule, Optional[Result]]:
        """
        We can go ahead and find the "best" solution for each independent
        child rule here, instead of trying them in combination with the
        co-dependent rules.

        Also, because these rules are each independent of any other rule, we
        can reset the context between each run, because we've already
        guaranteed that there is no claimable overlap.
        """

        claims = ctx.claims

        independent_rule__results: Dict[Rule, Optional[Result]] = {}
        for child in independent_children:
            best_result = None

            ctx.reset_claims()

            for i, sol in enumerate(child.solutions(ctx=ctx)):
                result = sol.audit(ctx=ctx)

                if best_result is None:
                    best_result = result

                if result.ok():
                    best_result = result
                    break

                if best_result.rank() < result.rank():
                    best_result = result

                ctx.reset_claims()

            logger.debug("found solution for %s: %s", child.path, best_result)

            independent_rule__results[child] = best_result

        ctx.set_claims(claims)

        return independent_rule__results

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

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if self._has_potential(ctx=ctx):
            logger.debug('%s has potential: yes', self.path)
            return True
        else:
            logger.debug('%s has potential: no', self.path)
            return False

    def _has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if ctx.get_exception(self.path):
            return True

        return any(r.has_potential(ctx=ctx) for r in self.items)

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        matches = [c for r in self.items for c in r.all_matches(ctx=ctx)]

        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            matches.append(ctx.forced_course_by_clbid(exception.clbid))

        return matches
