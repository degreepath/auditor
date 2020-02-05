from typing import Dict, Tuple, Sequence, Optional, Iterator, Any, List, Set, TYPE_CHECKING
from collections import defaultdict
from functools import partial
import itertools
import logging
import decimal
import enum

import attr

from .clause import Clause, apply_clause
from .lazy_product import lazy_product
from .load_clause import load_clause
from .constants import Constants
from .ncr import ncr

if TYPE_CHECKING:
    from .data.course import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@enum.unique
class AtMostWhat(enum.Enum):
    Courses = 0
    Credits = 1


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Limit:
    at_most: decimal.Decimal
    at_most_what: AtMostWhat = AtMostWhat.Courses
    where: Clause
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
    def load(data: Dict, c: Constants) -> 'Limit':
        at_most = data.get("at most", data.get("at-most", data.get("at_most", None)))

        if at_most is None:
            raise Exception(f'expected an at-most key; got {data}')

        allowed_keys = {'at most', 'at-most', 'at_most', 'where', 'message'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty"

        clause = load_clause(data["where"], c=c)
        assert clause, 'limits are not allowed to have conditional clauses'

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

    def iterate(self, courses: Sequence['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        # Be sure to sort the input, so that the output from the iterator is
        # sorted the same way each time. We need this because our input may
        # be a set, in which case there is no inherent ordering.
        courses = sorted(courses, key=lambda item: item.sort_order())

        # logger.debug("limit/loop/start: limit=%s, matched=%s", self, courses)

        if self.at_most_what is AtMostWhat.Courses:
            yield from self.iterate_courses(courses)
        elif self.at_most_what is AtMostWhat.Credits:
            yield from self.iterate_credits(courses)

    def iterate_courses(self, courses: Sequence['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        for n in range(0, int(self.at_most) + 1):
            # logger.debug("limit/loop(%s..<%s): n=%s applying %s", 0, self.at_most + 1, n, self.where)
            for combo in itertools.combinations(courses, n):
                # logger.debug("limit/loop(%s..<%s)/combo: n=%s combo=%s", 0, self.at_most + 1, n, combo)
                yield combo

    def iterate_credits(self, courses: Sequence['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
        if sum(c.credits for c in courses) <= self.at_most:
            yield tuple(courses)
            return

        for n in range(0, len(courses) + 1):
            # logger.debug("limit/loop(%s..<%s): n=%s applying %s", 0, self.at_most + 1, n, self.where)
            for combo in itertools.combinations(courses, n):
                if sum(c.credits for c in combo) <= self.at_most:
                    # logger.debug("limit/loop(%s..<%s)/combo: n=%s combo=%s", 0, self.at_most + 1, n, combo)
                    yield combo

    def estimate(self, courses: Sequence['CourseInstance']) -> int:
        acc = 0

        if self.at_most_what is AtMostWhat.Courses:
            for n in range(0, int(self.at_most) + 1):
                acc += ncr(len(courses), n)

        elif self.at_most_what is AtMostWhat.Credits:
            for n in range(1, len(courses) + 1):
                acc += ncr(len(courses), n)

        return acc


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class LimitSet:
    limits: Tuple[Limit, ...]

    def has_limits(self) -> bool:
        return len(self.limits) > 0

    def to_dict(self) -> List[Dict[str, Any]]:
        return [limit.to_dict() for limit in self.limits]

    @staticmethod
    def load(data: Optional[Sequence[Dict]], c: Constants) -> 'LimitSet':
        if data is None:
            return LimitSet(limits=tuple())
        return LimitSet(limits=tuple(Limit.load(limit, c) for limit in data))

    def apply_limits(self, courses: Sequence['CourseInstance']) -> Iterator['CourseInstance']:
        clause_counters: Dict = defaultdict(int)
        logger.debug("limit/before: %s", courses)

        for c in courses:
            may_yield = True

            for limit in self.limits:
                logger.debug("limit/check: checking %s against %s (counter: %s)", c, limit, clause_counters[limit])
                if apply_clause(limit.where, c):
                    if clause_counters[limit] >= limit.at_most:
                        logger.debug("limit/maximum: %s matched %s (counter: %s)", c, limit, clause_counters[limit])
                        may_yield = False
                        # break out of the loop once we fill up any limit clause
                        break

                    logger.debug("limit/increment: %s matched %s (counter: %s)", c, limit, clause_counters[limit])
                    clause_counters[limit] += 1

            if may_yield is True:
                logger.debug("limit/state: %s", clause_counters)
                logger.debug("limit/allow: %s", c)
                yield c

    def check(self, courses: Sequence['CourseInstance']) -> bool:
        clause_counters: Dict = defaultdict(decimal.Decimal)

        for c in courses:
            for limit in self.limits:
                if not apply_clause(limit.where, c):
                    continue

                if clause_counters[limit] >= limit.at_most:
                    # break out of the loop once we fill up any limit clause
                    return False

                if limit.at_most_what is AtMostWhat.Courses:
                    clause_counters[limit] += 1
                elif limit.at_most_what is AtMostWhat.Credits:
                    clause_counters[limit] += c.credits

        return True

    def limited_transcripts(self, courses: Sequence['CourseInstance']) -> Iterator[Tuple['CourseInstance', ...]]:
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

        # step 1: find the number of extra iterations we will need for each limiting clause
        matched_items: Dict = defaultdict(set)
        for limit in self.limits:
            for c in courses:
                logger.debug("limit/probe: checking %s against %s", c, limit)
                if apply_clause(limit.where, c):
                    matched_items[limit].add(c)

        all_matched_items = set(item for match_set in matched_items.values() for item in match_set)
        unmatched_items = list(all_courses.difference(all_matched_items))

        logger.debug("limit: unmatched items: %s", unmatched_items)

        # we need to attach _a_ combo from each limit clause
        clause_iterators = [
            partial(limit.iterate, match_set)
            for limit, match_set in matched_items.items()
        ]

        emitted_solutions: Set[Tuple['CourseInstance', ...]] = set()
        for results in lazy_product(*clause_iterators):
            these_items = tuple(sorted((item for group in results for item in group), key=lambda item: item.sort_order()))

            if not self.check(these_items):
                continue

            if these_items in emitted_solutions:
                continue
            else:
                emitted_solutions.add(these_items)

            this_combo = unmatched_items + list(these_items)
            this_combo.sort(key=lambda c: c.sort_order())

            logger.debug("limit/combos: %s", this_combo)
            yield tuple(this_combo)

    def estimate(self, courses: Sequence['CourseInstance']) -> int:
        # TODO: optimize this so that it doesn't need to actually build the results
        return sum(1 for _ in self.limited_transcripts(courses))
