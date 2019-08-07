from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Mapping, Sequence, Iterator
import itertools
import logging

from ..limit import LimitSet
from ..clause import Clause, load_clause, SingleClause, OrClause, AndClause
from ..solution.query import QuerySolution
from ..constants import Constants
from .assertion import AssertionRule
from ..ncr import ncr

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
    attempt_claims: bool

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
            "claims": [],
            "failures": [],
        }

    def state(self):
        return "rule"

    def ok(self):
        return True

    def rank(self):
        return 0

    def claims(self):
        return []

    def matched(self, *, ctx):
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "from" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants, children: Mapping):
        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c)

        limit = LimitSet.load(data=data.get("limit", None), c=c)

        if 'limits' in data:
            raise ValueError(f'the key is "limit", not "limits": {data}')

        attempt_claims = data.get('claim', True)

        assertions: List[AssertionRule] = []
        if "assert" in data:
            assertions = [AssertionRule.load({'assert': data["assert"]}, c)]
        elif "all" in data:
            assertions = [AssertionRule.load(d, c) for d in data["all"]]

        if 'assert' in data and 'all' in data:
            raise ValueError(f'you cannot have both assert: and all: keys; {data}')

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
            attempt_claims=attempt_claims,
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

    def get_data(self, *, ctx):
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
            data = []
            logger.info("%s not yet implemented", self.source_type)

        return data

    def solutions(self, *, ctx, path: List[str]):  # noqa: C901
        path = [*path, f".from"]
        logger.debug("%s", path)

        data = self.get_data(ctx=ctx)
        assert len(self.assertions) > 0

        if self.where is not None:
            logger.debug("%s clause: %s", path, self.where)
            logger.debug("%s before filter: %s item(s)", path, len(data))

            data = [item for item in data if item.apply_clause(self.where)]

            logger.debug("%s after filter: %s item(s)", path, len(data))

        did_iter = False
        for item_set in self.limit.limited_transcripts(data):
            if self.attempt_claims is False:
                did_iter = True
                yield QuerySolution(output=item_set, rule=self)
                continue

            if has_simple_count_assertion(self.assertions):
                assertion = get_largest_simple_count_assertion(self.assertions)
                if assertion is None:
                    raise Exception('has_simple_count_assertion and get_largest_simple_count_assertion disagreed')

                logger.debug("%s using simple assertion mode with %s", path, assertion)

                for n in assertion.input_size_range(maximum=len(item_set)):
                    for i, combo in enumerate(itertools.combinations(item_set, n)):
                        logger.debug("%s combo: %s choose %s, round %s", path, len(item_set), n, i)
                        did_iter = True
                        yield QuerySolution(output=combo, rule=self)
            else:
                logger.debug("not running single assertion mode")
                for n in range(1, len(item_set) + 1):
                    for i, combo in enumerate(itertools.combinations(item_set, n)):
                        logger.debug("%s combo: %s choose %s, round %s", path, len(item_set), n, i)
                        did_iter = True
                        yield QuerySolution(output=combo, rule=self)

        if not did_iter:
            # be sure we always yield something
            logger.debug("%s did not yield anything; yielding empty collection", path)
            yield QuerySolution(output=tuple(), rule=self)

    def estimate(self, *, ctx):
        data = self.get_data(ctx=ctx)

        if self.where is not None:
            data = [item for item in data if item.apply_clause(self.where)]

        did_iter = False
        iterations = 0
        for item_set in self.limit.limited_transcripts(data):
            if self.attempt_claims is False:
                iterations += 1
                continue

            if has_simple_count_assertion(self.assertions):
                assertion = get_largest_simple_count_assertion(self.assertions)
                if assertion is None:
                    raise Exception('has_simple_count_assertion and get_largest_simple_count_assertion disagreed')
                for n in assertion.input_size_range(maximum=len(item_set)):
                    iterations += ncr(len(item_set), n)
            else:
                for n in range(1, len(item_set) + 1):
                    iterations += ncr(len(item_set), n)

        if not did_iter:
            iterations += 1

        return iterations


def has_simple_count_assertion(assertions: Sequence[AssertionRule]) -> bool:
    if not assertions:
        return False

    for assertion in assertions:
        if assertion.where is not None:
            continue
        if has_simple_count_clause(assertion.assertion):
            return True

    return False


def has_simple_count_clause(clause: Clause) -> bool:
    try:
        next(get_simple_count_clauses(clause))
        return True
    except StopIteration:
        return False


def get_simple_count_clauses(clause: Clause) -> Iterator[SingleClause]:
    if isinstance(clause, SingleClause) and clause.key == 'count(courses)':
        yield clause
    elif isinstance(clause, OrClause) or isinstance(clause, AndClause):
        for c in clause.children:
            yield from get_simple_count_clauses(c)


def get_largest_simple_count_assertion(assertions: Sequence[AssertionRule]) -> Optional[SingleClause]:
    if not assertions:
        return None

    largest_clause = None
    largest_count = -1
    for assertion in assertions:
        clauses = get_simple_count_clauses(assertion.assertion)
        for clause in clauses:
            if type(clause.expected) == int and clause.expected > largest_count:
                largest_clause = clause
                largest_count = clause.expected

    return largest_clause
