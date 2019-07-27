from dataclasses import dataclass
from typing import Dict, List, Tuple, Sequence, Optional
from collections import defaultdict
import logging

from .clause import Clause, str_clause, load_clause
from .constants import Constants

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Limit:
    at_most: int
    where: Clause

    def to_dict(self):
        return {"type": "limit", "at_most": self.at_most, "where": self.where.to_dict()}

    @staticmethod
    def load(data: Dict, c: Constants):
        at_most = data.get("at most", data.get("at-most", data.get("at_most", None)))

        if at_most is None:
            raise Exception(f'expected an at-most key; got {data}')

        return Limit(at_most=at_most, where=load_clause(data["where"], c))

    def __str__(self):
        return f"Limit(at-most: {self.at_most}, where: {str_clause(self.where)})"


@dataclass(frozen=True)
class LimitSet:
    limits: Tuple[Limit, ...]

    def to_dict(self):
        return [l.to_dict() for l in self.limits]

    @staticmethod
    def load(data: Optional[Sequence[Dict]], c: Constants):
        if data is None:
            return LimitSet(limits=tuple())
        return LimitSet(limits=tuple(Limit.load(l, c) for l in data))

    def apply_limits(self, courses: List):
        clause_counters: Dict = defaultdict(int)
        course_set = []

        if courses:
            for i, c in enumerate(courses):
                logger.debug("limit/before/%s: %s", i, c)
        else:
            logger.debug(f"limit/before: []")

        for c in courses:
            may_yield = False

            for l in self.limits:
                logger.debug("limit/check: checking %s against %s", c.identity, l)
                if c.apply_clause(l.where):
                    if clause_counters[l] < l.at_most:
                        logger.debug("limit/increment: %s matched %s", c.identity, l)
                        clause_counters[l] += 1
                        may_yield = True
                    else:
                        logger.debug("limit/maximum: %s matched %s", c.identity, l)
                        may_yield = False
                else:
                    may_yield = True

            if may_yield:
                course_set.append(c)

        if course_set:
            for i, c in enumerate(course_set):
                logger.debug("limit/after/%s: %s", i, c)
        else:
            logger.debug(f"limit/after: []")

        logger.debug("limit/state: %s", clause_counters)

        return tuple(course_set)

    def limited_transcripts(self, courses: List):
        """
        We need to iterate over each combination of limited courses.

        IE, if we have {at-most: 1, where: subject == CSCI}, and three CSCI courses,
        then we need to generate three transcripts - one with each of them.

        To do that, we do … what?
        """
        # skip _everything_ in here if there are no limits to apply
        if not self.limits:
            logger.debug(f"No limits to apply")
            yield tuple(courses)
            return

        # step 1: find the number of extra iterations we will need for each limiting clause
        extra_iter_counters: Dict = defaultdict(int)
        for l in self.limits:
            for c in courses:
                logger.debug("limit/probe: checking %s against %s", c.identity, l)
                if c.apply_clause(l.where):
                    extra_iter_counters[l] += 1
            # set each counter to the number of extra courses, or 0, to find the number of extra iterations
            extra_iter_counters[l] = max(0, extra_iter_counters[l] - l.at_most)

        extra_iter_counters = {k: v for k, v in extra_iter_counters.items() if v > 0}

        # if nothing needs extra iteration, just spit out the limited transcript once
        if not extra_iter_counters:
            logger.debug(f"No limits result in extra combinations")
            yield self.apply_limits(courses)

        logger.debug("Limits result in %s extra combinations", len(extra_iter_counters))
        # TODO: figure out how to do this
        # for _ in extra_iter_counters:
        yield self.apply_limits(courses)
