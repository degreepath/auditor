from dataclasses import dataclass
from typing import Dict, Tuple, Sequence, Optional, Iterator, TypeVar, Any, List
import itertools
from collections import defaultdict
import logging

from .clause import Clause, str_clause, load_clause
from .constants import Constants

from .data.clausable import Clausable

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=Clausable)


@dataclass(frozen=True)
class Limit:
    at_most: int
    where: Clause

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "limit", "at_most": self.at_most, "where": self.where.to_dict()}

    @staticmethod
    def load(data: Dict, c: Constants) -> 'Limit':
        at_most = data.get("at most", data.get("at-most", data.get("at_most", None)))

        if at_most is None:
            raise Exception(f'expected an at-most key; got {data}')

        return Limit(at_most=at_most, where=load_clause(data["where"], c))

    def __str__(self):
        return f"Limit(at-most: {self.at_most}, where: {str_clause(self.where)})"

    def iterate(self, courses: Sequence[T]) -> Iterator[Tuple[T, ...]]:
        logger.debug("limit/loop/start: limit=%s, matched=%s", self, courses)

        for n in range(0, self.at_most + 1):
            logger.debug("limit/loop(%s..<%s): n=%s applying %s", 0, self.at_most + 1, n, self.where)
            for combo in itertools.combinations(courses, n):
                logger.debug("limit/loop(%s..<%s)/combo: n=%s combo=%s", 0, self.at_most + 1, n, combo)
                yield combo


@dataclass(frozen=True)
class LimitSet:
    limits: Tuple[Limit, ...]

    def has_limits(self) -> bool:
        return len(self.limits) > 0

    def to_dict(self) -> List[Dict[str, Any]]:
        return [l.to_dict() for l in self.limits]

    @staticmethod
    def load(data: Optional[Sequence[Dict]], c: Constants) -> 'LimitSet':
        if data is None:
            return LimitSet(limits=tuple())
        return LimitSet(limits=tuple(Limit.load(l, c) for l in data))

    def apply_limits(self, courses: Sequence[T]) -> Iterator[T]:
        clause_counters: Dict = defaultdict(int)

        logger.debug("limit/before: %s", courses)

        for c in courses:
            may_yield = True

            for l in self.limits:
                logger.debug("limit/check: checking %s against %s (counter: %s)", c, l, clause_counters[l])
                if c.apply_clause(l.where):
                    if clause_counters[l] < l.at_most:
                        logger.debug("limit/increment: %s matched %s (counter: %s)", c, l, clause_counters[l])
                        clause_counters[l] += 1
                    else:
                        logger.debug("limit/maximum: %s matched %s (counter: %s)", c, l, clause_counters[l])
                        may_yield = False
                        # break out of the loop once we fill up any limit clause
                        break

            if may_yield is True:
                logger.debug("limit/state: %s", clause_counters)
                logger.debug("limit/allow: %s", c)
                yield c

    def limited_transcripts(self, courses: Sequence[T]) -> Iterator[Tuple[T, ...]]:
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
        for l in self.limits:
            for c in courses:
                logger.debug("limit/probe: checking %s against %s", c, l)
                if c.apply_clause(l.where):
                    matched_items[l].add(c)

        all_matched_items = set(item for matchset in matched_items.values() for item in matchset)
        unmatched_items = list(all_courses.difference(all_matched_items))

        logger.debug("limit: unmatched items: %s", unmatched_items)

        # we need to attach _a_ combo from each limit clause
        clause_iterators = [limit.iterate(matchset) for limit, matchset in matched_items.items()]
        for results in itertools.product(*clause_iterators):
            this_combo = tuple(unmatched_items) + tuple(item for group in results for item in group)
            logger.debug("limit/combos: %s", this_combo)
            yield this_combo
