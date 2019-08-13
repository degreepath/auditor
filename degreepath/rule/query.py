from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Sequence, Iterator, TYPE_CHECKING
import itertools
import logging

from ..base import Rule, BaseQueryRule
from ..base.query import QuerySource, QuerySourceType, QuerySourceRepeatMode
from ..limit import LimitSet
from ..clause import Clause, load_clause, SingleClause, OrClause, AndClause
from ..solution.query import QuerySolution
from ..constants import Constants
from ..ncr import ncr
from .assertion import AssertionRule

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryRule(Rule, BaseQueryRule):
    __slots__ = ()

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "from" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: List[str]) -> 'QueryRule':
        path = [*path, f".query"]

        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c)

        limit = LimitSet.load(data=data.get("limit", None), c=c)

        if 'limits' in data:
            raise ValueError(f'the key is "limit", not "limits": {data}')

        attempt_claims = data.get('claim', True)

        assertions: List[AssertionRule] = []
        if "assert" in data:
            assertions = [AssertionRule.load({'assert': data["assert"]}, c=c, path=[*path, ".assertions", "[0]"])]
        elif "all" in data:
            assertions = [AssertionRule.load(d, c=c, path=[*path, ".assertions", f"[{i}]"]) for i, d in enumerate(data["all"])]
        else:
            raise ValueError(f'you must have either an assert: or an all: key in {data}')

        if 'assert' in data and 'all' in data:
            raise ValueError(f'you cannot have both assert: and all: keys; {data}')

        allow_claimed = data.get('allow_claimed', False)

        source_data = data['from']

        if "student" not in source_data:
            raise KeyError(f"expected from:student; got {list(source_data.keys())}")

        source = QuerySource.Student
        source_type = QuerySourceType(source_data["student"])
        source_repeats = QuerySourceRepeatMode(source_data.get('repeats', 'all'))

        return QueryRule(
            source=source,
            source_type=source_type,
            source_repeats=source_repeats,
            assertions=tuple(assertions),
            limit=limit,
            where=where,
            allow_claimed=allow_claimed,
            attempt_claims=attempt_claims,
            path=tuple(path),
        )

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.assertions:
            for a in self.assertions:
                a.validate(ctx=ctx)

    def get_data(self, *, ctx: 'RequirementContext') -> Sequence['Clausable']:
        if self.source_type is QuerySourceType.Courses:
            data = ctx.transcript()

            if self.source_repeats is QuerySourceRepeatMode.First:
                filtered_courses = []
                course_identities: Set[str] = set()

                for course in sorted(data, key=lambda c: f"{c.year}{c.term}"):
                    if course.crsid not in course_identities:
                        filtered_courses.append(course)
                        course_identities.add(course.crsid)

                data = filtered_courses

            return data

        elif self.source_type is QuerySourceType.Areas:
            return list(ctx.areas)

        else:
            logger.info("%s not yet implemented", self.source_type)
            return []

    def solutions(self, *, ctx: 'RequirementContext') -> Iterator[QuerySolution]:  # noqa: C901
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        exception = ctx.get_exception(self.path)
        if exception and exception.is_pass_override():
            logger.debug("forced override on %s", self.path)
            yield QuerySolution.from_rule(rule=self, output=tuple(), overridden=True)
            return

        data = self.get_data(ctx=ctx)
        assert len(self.assertions) > 0

        if self.where is not None:
            logger.debug("%s clause: %s", self.path, self.where)
            logger.debug("%s before filter: %s item(s)", self.path, len(data))

            data = [item for item in data if item.apply_clause(self.where)]

            logger.debug("%s after filter: %s item(s)", self.path, len(data))

        did_iter = False
        for item_set in self.limit.limited_transcripts(data):
            if self.attempt_claims is False:
                did_iter = True
                yield QuerySolution.from_rule(rule=self, output=item_set)
                continue

            item_set = tuple(sorted(item_set))

            if has_simple_count_assertion(self.assertions):
                assertion = get_largest_simple_count_assertion(self.assertions)
                if assertion is None:
                    raise Exception('has_simple_count_assertion and get_largest_simple_count_assertion disagreed')

                logger.debug("%s using simple assertion mode with %s", self.path, assertion)

                for n in assertion.input_size_range(maximum=len(item_set)):
                    for i, combo in enumerate(itertools.combinations(item_set, n)):
                        if debug: logger.debug("%s combo: %s choose %s, round %s", self.path, len(item_set), n, i)
                        did_iter = True
                        yield QuerySolution.from_rule(rule=self, output=combo)
            else:
                logger.debug("not running single assertion mode")
                for n in range(1, len(item_set) + 1):
                    for i, combo in enumerate(itertools.combinations(item_set, n)):
                        if debug: logger.debug("%s combo: %s choose %s, round %s", self.path, len(item_set), n, i)
                        did_iter = True
                        yield QuerySolution.from_rule(rule=self, output=combo)

        if not did_iter:
            # be sure we always yield something
            logger.debug("%s did not yield anything; yielding empty collection", self.path)
            yield QuerySolution.from_rule(rule=self, output=tuple())

    def estimate(self, *, ctx: 'RequirementContext') -> int:
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

        logger.debug('QueryRule.estimate: %s', iterations)

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

        if self.where is None:
            return len(self.get_data(ctx=ctx)) > 0

        return any(item.apply_clause(self.where) for item in self.get_data(ctx=ctx))


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
