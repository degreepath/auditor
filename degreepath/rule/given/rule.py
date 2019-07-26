from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, TYPE_CHECKING
import itertools
import logging

from .source import FromInput
from .assertion import AnyAssertion, load_assertion
from ...limit import LimitSet, Limit
from ...clause import Clause, load_clause, SingleClause
from ...solution.given import FromSolution
from ...constants import Constants
from ...operator import Operator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FromRule:
    source: FromInput
    action: Optional[Clause]
    limit: LimitSet
    where: Optional[Clause]
    allow_claimed: bool

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
    def load(data: Dict, c: Constants):
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
        )

    def validate(self, *, ctx):
        self.source.validate(ctx=ctx)
        if self.action:
            self.action.validate(ctx=ctx)

    def solutions_when_student(self, *, ctx, path):


        yield data

    def solutions(self, *, ctx, path: List[str]):
        path = [*path, f".from"]
        logger.debug("%s", path)

        ###

        if self.source.mode != "student":
            raise KeyError(f'unknown "from" type "{self.source.mode}"')

        if self.source.itemtype == "courses":
            data = ctx.transcript

            if self.source.repeat_mode == "first":
                filtered_courses = []
                course_identities: Set[str] = set()
                for course in sorted(data, key=lambda c: c.term):
                    if course.crsid not in course_identities:
                        filtered_courses.append(course)
                        course_identities.add(course.crsid)
                data = filtered_courses

        elif self.source.itemtype == "areas":
            data = ctx.areas

        else:
            raise KeyError(f"{self.source.itemtype} not yet implemented")

        ###

        assert self.action is not None

        did_iter = False

        if self.where is not None:
            logger.debug("clause: %s", self.where)
            logger.debug("before filter: %s items", len(data))

            data = [item for item in data if item.apply_clause(self.where)]

            logger.debug("after filter: %s items", len(data))

        for item_set in self.limit.limited_transcripts(data):
            if isinstance(self.action, SingleClause):
                for n in self.action.input_size_range(maximum=len(item_set)):
                    for i, combo in enumerate(itertools.combinations(item_set, n)):
                        logger.debug("combo: %s choose %s, round %s", len(item_set), n, i)
                        did_iter = True
                        yield FromSolution(output=combo, rule=self)

        if not did_iter:
            # be sure we always yield something
            logger.debug("did not yield anything; yielding empty collection")
            yield FromSolution(output=tuple(), rule=self)


@dataclass(frozen=True)
class PartialFromRule:
    where: Optional[Clause]
    action: Clause

    def to_dict(self):
        return {
            "type": "partial-from",
            "action": self.action.to_dict() if self.action else None,
            "where": self.where.to_dict() if self.where else None,
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
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants):
        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c)

        assertion = load_clause(data["assert"], c)

        return PartialFromRule(action=assertion, where=where)
