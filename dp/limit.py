from typing import Dict, Tuple, Collection, Union, Optional, Iterator, Any, List, Set, FrozenSet, TYPE_CHECKING
from collections import defaultdict
from functools import partial
import itertools
import logging
import decimal
import enum

import attr

from .conditional_expression import SomePredicateExpression, load_predicate_expression
from .predicate_clause import SomePredicate, load_predicate
from .data_type import DataType
from .lazy_product import lazy_product
from .constants import Constants
from .ncr import ncr

if TYPE_CHECKING:
    from .data.clausable import Clausable
    from .data.course import CourseInstance  # noqa: F401
    from .context import RequirementContext  # noqa: F401

logger = logging.getLogger(__name__)


@enum.unique
class AtMostWhat(enum.Enum):
    Courses = 0
    Credits = 1


SomeLimit = Union['Limit', 'ConditionalLimit']


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Limit:
    at_most: decimal.Decimal
    at_most_what: AtMostWhat = AtMostWhat.Courses
    where: SomePredicate
    message: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "limit",
            "at_most": str(self.at_most),
            "at_most_what": self.at_most_what.name,
            "where": self.where.to_dict(),
            "message": self.message,
        }

    @staticmethod
    def load(data: Dict, *, c: Constants, ctx: 'RequirementContext') -> SomeLimit:
        if '$if' in data:
            return ConditionalLimit.load(data, c=c, ctx=ctx)

        at_most = data.get("at most", data.get("at-most", data.get("at_most", None)))

        if at_most is None:
            raise Exception(f'expected an at-most key; got {data}')

        allowed_keys = {'at most', 'at-most', 'at_most', 'where', 'message'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty"

        clause = load_predicate(data["where"], c=c, ctx=ctx, mode=DataType.Course)

        try:
            at_most = decimal.Decimal(int(at_most))
            at_most_what = AtMostWhat.Courses
        except ValueError:
            _at_most = at_most
            # must be a string, like "1 course"
            at_most, at_most_what = at_most.split()

            at_most = decimal.Decimal(at_most)
            if at_most_what in ('course', 'courses'):
                at_most_what = AtMostWhat.Courses
            elif at_most_what in ('credit', 'credits'):
                at_most_what = AtMostWhat.Credits
            else:
                raise ValueError(f'expected course|credits, got {at_most_what} (part of {_at_most})')

        return Limit(at_most=at_most, at_most_what=at_most_what, where=clause, message=data.get('message', None))

    def applies(self, to: 'Clausable') -> bool:
        return self.where.apply(to)

    def iterate(self, courses: Collection['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        # Be sure to sort the input, so that the output from the iterator is
        # sorted the same way each time. We need this because our input may
        # be a set, in which case there is no inherent ordering.
        courses = sorted(courses, key=lambda item: item.sort_order())

        # logger.debug("limit/loop/start: limit=%s, matched=%s", self, courses)

        if self.at_most_what is AtMostWhat.Courses:
            yield from self.iterate_courses(courses)
        elif self.at_most_what is AtMostWhat.Credits:
            yield from self.iterate_credits(courses)

    def iterate_courses(self, courses: Collection['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        for n in range(0, int(self.at_most) + 1):
            # logger.debug("limit/loop(%s..<%s): n=%s applying %s", 0, self.at_most + 1, n, self.where)
            for combo in itertools.combinations(courses, n):
                # logger.debug("limit/loop(%s..<%s)/combo: n=%s combo=%s", 0, self.at_most + 1, n, combo)
                yield combo

    def iterate_credits(self, courses: Collection['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        if sum(c.credits for c in courses) <= self.at_most:
            yield tuple(courses)
            return

        for n in range(0, len(courses) + 1):
            # logger.debug("limit/loop(%s..<%s): n=%s applying %s", 0, self.at_most + 1, n, self.where)
            for combo in itertools.combinations(courses, n):
                if sum(c.credits for c in combo) <= self.at_most:
                    # logger.debug("limit/loop(%s..<%s)/combo: n=%s combo=%s", 0, self.at_most + 1, n, combo)
                    yield combo

    def estimate(self, courses: Collection['CourseInstance']) -> int:
        acc = 0

        if self.at_most_what is AtMostWhat.Courses:
            for n in range(0, int(self.at_most) + 1):
                acc += ncr(len(courses), n)

        elif self.at_most_what is AtMostWhat.Credits:
            for n in range(1, len(courses) + 1):
                acc += ncr(len(courses), n)

        return acc


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ConditionalLimit:
    condition: SomePredicateExpression
    when_true: Limit
    when_false: Optional[Limit]
    selected_branch: Optional[Limit] = None

    @staticmethod
    def load(
        data: Dict[str, Any],
        *,
        c: Constants,
        ctx: 'RequirementContext',
    ) -> 'ConditionalLimit':
        condition = load_predicate_expression(data['$if'], ctx=ctx)

        when_true = Limit.load(data['$then'], c=c, ctx=ctx)
        when_false = None
        if data.get('$else', None) is not None:
            when_false = Limit.load(data['$else'], c=c, ctx=ctx)

        selected_branch = when_false
        if condition.result is True:
            selected_branch = when_true

        return ConditionalLimit(
            condition=condition,
            when_true=when_true,
            when_false=when_false,
            selected_branch=selected_branch,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "limit--if",
            "condition": self.condition.to_dict(),
            "when_true": self.when_true.to_dict(),
            "when_false": self.when_false.to_dict() if self.when_false else None,
        }

    def applies(self, to: 'Clausable') -> bool:
        if not self.selected_branch:
            return False
        return self.selected_branch.where.apply(to)

    def evaluate(self, *, ctx: 'RequirementContext') -> 'ConditionalLimit':
        if self.condition.result is not None:
            return self

        evaluated_condition = self.condition.evaluate(ctx=ctx)

        selected_branch = self.when_false
        if evaluated_condition.result is True:
            selected_branch = self.when_true

        return attr.evolve(self, condition=evaluated_condition, selected_branch=selected_branch)

    def iterate(self, courses: Collection['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        if self.selected_branch:
            yield from self.selected_branch.iterate(courses)

    def estimate(self, courses: Collection['CourseInstance']) -> int:
        if self.selected_branch:
            return self.selected_branch.estimate(courses)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class LimitSet:
    limits: Tuple[SomeLimit, ...]

    def has_limits(self) -> bool:
        return bool(self.limits)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [limit.to_dict() for limit in self.limits]

    def evaluate_conditionals(self) -> 'LimitSet':
        limits = tuple(
            limit.evaluate() if isinstance(limit, ConditionalLimit) else limit
            for limit in self.limits
        )
        return attr.evolve(self, limits=limits)

    @staticmethod
    def load(data: Optional[Collection[Dict]], *, c: Constants, ctx: 'RequirementContext') -> 'LimitSet':
        if data is None:
            return LimitSet(limits=tuple())
        return LimitSet(limits=tuple(Limit.load(limit, c=c, ctx=ctx) for limit in data))

    def check(self, courses: Collection['CourseInstance']) -> bool:
        clause_counters: Dict = defaultdict(decimal.Decimal)

        for c in courses:
            for limit in self.limits:
                if not limit.applies(c):
                    continue

                if clause_counters[limit] >= limit.at_most:
                    # break out of the loop once we fill up any limit clause
                    return False

                if limit.at_most_what is AtMostWhat.Courses:
                    clause_counters[limit] += 1
                elif limit.at_most_what is AtMostWhat.Credits:
                    clause_counters[limit] += c.credits

        return True

    def limited_transcripts(
        self,
        courses: Collection['CourseInstance'],
        *,
        forced_clbids: Tuple[str, ...] = tuple(),
    ) -> Iterator[Tuple['CourseInstance', ...]]:
        """
        We need to iterate over each combination of limited courses.

        IE, if we have {at-most: 1, where: subject == CSCI}, and three CSCI courses,
        then we need to generate three transcripts - one with each of them.

        - capture the things that match each limit
        - make a list of the things that matched no limit clause
        - for each set of things that matched…
            - for N in range(0,at_most)…
                - add the result of combinations(matched_things, N) to the unmatched set
                - yield this combined set
        """
        # skip _everything_ in here if there are no limits to apply
        if not self.limits:
            logger.debug("no limits to apply")
            yield tuple(courses)
            return

        logger.debug("applying limits")

        all_courses = set(courses)

        # step 0: figure out which courses have been force-inserted and will thus bypass the limit check
        forced_items = {c.clbid: c for c in all_courses if c.clbid in forced_clbids}
        logger.debug("limit: forced items: %r", forced_items)

        # step 1: find the number of extra iterations we will need for each limiting clause
        matched_items: Dict = defaultdict(set)
        for limit in self.limits:
            logger.debug("limit/probe: checking against %r", limit)
            for c in courses:
                if c.clbid in forced_items:
                    logger.debug("limit/probe: skipping check of %r as it has been forced", c)
                    continue
                logger.debug("limit/probe: checking %r", c)
                if limit.applies(c):
                    matched_items[limit].add(c)

        all_matched_items = set(item for match_set in matched_items.values() for item in match_set)
        unmatched_items = list(all_courses.difference(all_matched_items))

        logger.debug("limit: unmatched items: %r", unmatched_items)

        # we need to attach _a_ combo from each limit clause
        clause_iterators = [
            partial(limit.iterate, match_set)
            for limit, match_set in matched_items.items()
        ]

        emitted_solutions: Set[FrozenSet['CourseInstance']] = set()
        for results in lazy_product(*clause_iterators):
            these_items = frozenset(item for group in results for item in group)

            if not self.check(these_items):
                logger.debug("limit: invalid collection: %r", unmatched_items)
                continue

            if these_items in emitted_solutions:
                logger.debug("limit: duplicate collection: %r", unmatched_items)
                continue
            else:
                emitted_solutions.add(these_items)

            this_combo = [*unmatched_items, *these_items]
            this_combo.sort(key=lambda c: c.sort_order())

            logger.debug("limit: emitting: %r", this_combo)
            yield tuple(this_combo)

    def estimate(self, courses: Collection['CourseInstance']) -> int:
        # TODO: optimize this so that it doesn't need to actually build the results
        return sum(1 for _ in self.limited_transcripts(courses))
