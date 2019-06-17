from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Sequence, Optional, TYPE_CHECKING
from collections import defaultdict
import logging

from .clause import Clause, SingleClause, str_clause

if TYPE_CHECKING:
    from .data import CourseInstance


@dataclass(frozen=True)
class Limit:
    at_most: int
    where: Clause

    def to_dict(self):
        return {"type": "limit", "at_most": self.at_most, "where": self.where.to_dict()}

    @staticmethod
    def load(data: Dict) -> Limit:
        return Limit(at_most=data["at_most"], where=SingleClause.load(data["where"]))

    def __str__(self):
        return f"Limit(at-most: {self.at_most}, where: {str_clause(self.where)})"


@dataclass(frozen=True)
class LimitSet:
    limits: Tuple[Limit, ...]

    def to_dict(self):
        return [l.to_dict() for l in self.limits]

    @staticmethod
    def load(data: Optional[Sequence[Dict]] = None) -> LimitSet:
        if data is None:
            return LimitSet(limits=tuple())
        return LimitSet(limits=tuple(Limit.load(l) for l in data))

    def apply_limits(self, courses: List[CourseInstance]):
        clause_counters = defaultdict(int)
        course_set = []

        if courses:
            for i, c in enumerate(courses):
                logging.debug(f"limit/before/{i}: {c}")
        else:
            logging.debug(f"limit/before: []")

        for c in courses:
            may_yield = False

            for l in self.limits:
                logging.debug(f"limit/check: checking {c.identity} against {l}")
                if c.apply_clause(l.where):
                    if clause_counters[l] < l.at_most:
                        logging.debug(f"limit/increment: {c.identity} matched {l}")
                        clause_counters[l] += 1
                        may_yield = True
                    else:
                        logging.debug(f"limit/maximum: {c.identity} matched {l}")
                        may_yield = False
                else:
                    may_yield = True

            if may_yield:
                course_set.append(c)

        if course_set:
            for i, c in enumerate(course_set):
                logging.debug(f"limit/after/{i}: {c}")
        else:
            logging.debug(f"limit/after: []")

        logging.debug(f"limit/state: {clause_counters}")

        return course_set

    def limited_transcripts(self, courses: List[CourseInstance]):
        """
        We need to iterate over each combination of limited courses.

        IE, if we have {at-most: 1, where: subject == CSCI}, and three CSCI courses,
        then we need to generate three transcripts - one with each of them.

        To do that, we do … what?
        """
        # skip _everything_ in here if there are no limits to apply
        if not self.limits:
            logging.debug(f"No limits to apply")
            yield courses
            return

        # step 1: find the number of extra iterations we will need for each limiting clause
        extra_iter_counters = defaultdict(int)
        for l in self.limits:
            for c in courses:
                logging.debug(f"limit/probe: checking {c.identity} against {l}")
                if c.apply_clause(l.where):
                    extra_iter_counters[l] += 1
            # set each counter to the number of extra courses, or 0, to find the number of extra iterations
            extra_iter_counters[l] = max(0, extra_iter_counters[l] - l.at_most)

        extra_iter_counters = {k: v for k, v in extra_iter_counters.items() if v > 0}

        # if nothing needs extra iteration, just spit out the limited transcript once
        if not extra_iter_counters:
            logging.debug(f"No limits result in extra combinations")
            yield self.apply_limits(courses)

        logging.debug(f"Limits result in {len(extra_iter_counters)} extra combinations")
        # TODO: figure out how to do this
        # for _ in extra_iter_counters:
        yield self.apply_limits(courses)
