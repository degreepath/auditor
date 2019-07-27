from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
import itertools
import logging

from ..limit import LimitSet
from ..clause import Clause, load_clause, SingleClause
from ..solution.query import QuerySolution
from ..constants import Constants
from .assertion import AssertionRule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryRule:
    source: str
    source_type: str
    source_repeats: Optional[str]

    assertions: Tuple[AssertionRule, ...]
    limit: LimitSet
    where: Optional[Clause]
    allow_claimed: bool

    def to_dict(self):
        return {
            "type": "from",
            "source": self.source,
            "source_type": self.source_type,
            "source_repeats": self.source_repeats,
            "limit": self.limit.to_dict(),
            "assertions": [a.to_dict() for a in self.assertions],
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

        assertions: List[AssertionRule] = []
        if "assert" in data:
            assertions = [AssertionRule.load({'assert': data["assert"]}, c)]
        if "all" in data:
            assertions = [AssertionRule.load(d, c) for d in data["all"]]

        allow_claimed = data.get('allow_claimed', False)

        source_data = data['from']

        if "student" in source_data:
            source = "student"
            source_type = source_data["student"]
            source_repeats = source_data.get('repeats', 'all')
            assert source_repeats in ['first', 'all']

        elif "saves" in source_data or "save" in source_data:
            raise ValueError('from:saves not supported')

        elif "requirements" in source_data or "requirement" in source_data:
            raise ValueError('from:requirements not supported')

        else:
            raise KeyError(f"expected from:student; got {list(source_data.keys())}")

        return QueryRule(
            source=source,
            source_type=source_type,
            source_repeats=source_repeats,
            assertions=tuple(assertions),
            limit=limit,
            where=where,
            allow_claimed=allow_claimed,
        )

    def validate(self, *, ctx):
        assert isinstance(self.source, str)

        if self.source == "student":
            allowed = ["courses", "music performances", "areas"]
            assert self.source_type in allowed, f"when from:student, '{self.source_type}' must in in {allowed}"

        else:
            raise NameError(f"unknown 'from' type {self.source}")

        if self.assertions:
            [a.validate(ctx=ctx) for a in self.assertions]

    def solutions(self, *, ctx, path: List[str]):
        path = [*path, f".from"]
        logger.debug("%s", path)

        ###

        if self.source != "student":
            raise KeyError(f'unknown "from" type "{self.source}"')

        if self.source_type == "courses":
            data = ctx.transcript

            if self.source_repeats == "first":
                filtered_courses = []
                course_identities: Set[str] = set()
                for course in sorted(data, key=lambda c: c.term):
                    if course.crsid not in course_identities:
                        filtered_courses.append(course)
                        course_identities.add(course.crsid)
                data = filtered_courses

        elif self.source_type == "areas":
            data = ctx.areas

        else:
            raise KeyError(f"{self.source_type} not yet implemented")

        ###

        assert self.assertions is not None

        did_iter = False

        if self.where is not None:
            logger.debug("clause: %s", self.where)
            logger.debug("before filter: %s items", len(data))

            data = [item for item in data if item.apply_clause(self.where)]

            logger.debug("after filter: %s items", len(data))

        for item_set in self.limit.limited_transcripts(data):
            if len(self.assertions) == 1 and isinstance(self.assertions[0].assertion, SingleClause):
                assertion = self.assertions[0].assertion
                logger.debug("using single assertion mode with %s", assertion)
                for n in assertion.input_size_range(maximum=len(item_set)):
                    for i, combo in enumerate(itertools.combinations(item_set, n)):
                        logger.debug("combo: %s choose %s, round %s", len(item_set), n, i)
                        did_iter = True
                        yield QuerySolution(output=combo, rule=self)
            else:
                did_iter = True
                yield QuerySolution(output=item_set, rule=self)

        if not did_iter:
            # be sure we always yield something
            logger.debug("did not yield anything; yielding empty collection")
            yield QuerySolution(output=tuple(), rule=self)
