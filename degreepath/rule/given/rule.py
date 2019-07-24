from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import itertools
import logging

from .source import FromInput
from .assertion import AnyAssertion, load_assertion
from ...limit import LimitSet, Limit
from ...clause import Clause, load_clause
from ...solution import FromSolution
from ...constants import Constants

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FromRule:
    source: FromInput
    action: Optional[Clause]
    limit: LimitSet
    where: Optional[Clause]
    allow_claimed: bool
    in_save: bool = False

    def to_dict(self):
        return {
            "type": "from",
            "source": self.source.to_dict(),
            "limit": self.limit.to_dict(),
            "action": self.action.to_dict() if self.action else None,
            "where": self.where.to_dict() if self.where else None,
            "allow_claimed": self.allow_claimed,
            "status": "skip",
            "state": self.state(),
            "ok": self.ok(),
            "rank": self.rank(),
        }

    def state(self):
        return "rule"

    def ok(self):
        return True

    def rank(self):
        return 0

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "from" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants, *, in_save: bool = False):
        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c)

        limit = LimitSet.load(data=data.get("limit", None), c=c)

        action = None
        if "assert" in data:
            action = load_clause(data["assert"], c)

        allow_claimed = data.get('allow_claimed', False)

        return FromRule(
            source=FromInput.load(data["from"], c),
            action=action,
            limit=limit,
            where=where,
            allow_claimed=allow_claimed,
            in_save=in_save,
        )

    def validate(self, *, ctx):
        self.source.validate(ctx=ctx)
        if self.action:
            self.action.validate(ctx=ctx)

    def solutions_when_student(self, *, ctx, path):
        if self.source.itemtype == "courses":
            data = ctx.transcript

            if self.source.repeat_mode == "first":
                filtered_courses = []
                course_identities = set()
                for course in sorted(data, key=lambda c: c.term):
                    if course.crsid not in course_identities:
                        filtered_courses.append(course)
                        course_identities.add(course.crsid)
                data = filtered_courses

        elif self.source.itemtype == "areas":
            data = ctx.areas

        else:
            raise KeyError(f"{self.source.itemtype} not yet implemented")

        yield data

    def solutions_when_saves(self, *, ctx, path):
        saves = [
            ctx.save_rules[s].solutions(ctx=ctx, path=path)
            for s in self.source.saves
        ]

        for p in itertools.product(*saves):
            data = set(item for save_result in p for item in save_result.stored(ctx=ctx))
            yield data

    def solutions_when_reqs(self, *, ctx, path):
        reqs = [
            ctx.requirements[s].solutions(ctx=ctx, path=path)
            for s in self.source.requirements
        ]

        for p in itertools.product(*reqs):
            data = set(item for req_result in p for item in req_result.matched(ctx=ctx))
            yield data

    def solutions(self, *, ctx, path: List[str]):
        path = [*path, f".from"]
        logger.debug("%s", path)

        if self.source.mode == "student":
            iterable = self.solutions_when_student(ctx=ctx, path=path)
        elif self.source.mode == "saves":
            iterable = self.solutions_when_saves(ctx=ctx, path=path)
        elif self.source.mode == "requirements":
            iterable = self.solutions_when_reqs(ctx=ctx, path=path)
        else:
            raise KeyError(f'unknown "from" type "{self.source.mode}"')

        if not self.in_save:
            assert self.action is not None

        did_iter = False
        for data in iterable:
            if self.where is not None:
                logger.debug("fromrule/filter/clause: %s", self.where)
                if data:
                    for i, c in enumerate(data):
                        logger.debug("fromrule/filter/before/%s: %s", i, c)
                else:
                    logger.debug("fromrule/filter/before: []")

                data = [item for item in data if item.apply_clause(self.where)]

                if data:
                    for i, c in enumerate(data):
                        logger.debug("fromrule/filter/after/%s: %s", i, c)
                else:
                    logger.debug("fromrule/filter/after: []")

            for course_set in self.limit.limited_transcripts(data):
                # for n in self.action.range(items=course_set):
                #     for combo in itertools.combinations(course_set, n):
                #         logger.debug(f"fromrule/combo/size={n} of {len(course_set)} :: {[str(c) for c in combo]}")
                #         did_iter = True
                #         yield FromSolution(output=combo, rule=self)

                # for combo in itertools.combinations(course_set, n):
                #     logger.debug(f"fromrule/combo/size={n} of {len(course_set)} :: {[str(c) for c in combo]}")
                #     did_iter = True
                #     yield FromSolution(output=combo, rule=self)

                # also yield one with the entire set of courses
                yield FromSolution(output=course_set, rule=self)

        if not did_iter:
            # be sure we always yield something
            logger.debug("did not yield anything; yielding empty collection")
            yield FromSolution(output=tuple(), rule=self)
