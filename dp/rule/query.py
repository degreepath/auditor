import attr
from typing import Dict, List, Optional, Sequence, Iterator, Callable, Collection, FrozenSet, Union, Tuple, cast, TYPE_CHECKING
import itertools
import logging
import decimal

from ..base import Rule, BaseQueryRule
from ..base.query import QuerySource
from ..limit import LimitSet
from ..clause import SingleClause, apply_clause
from ..load_clause import load_clause
from ..data.clausable import Clausable
from ..ncr import ncr
from ..solution.query import QuerySolution
from ..constants import Constants
from ..operator import Operator
from ..data import CourseInstance
from .assertion import AssertionRule, ConditionalAssertionRule
from ..result.assertion import AssertionResult

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QueryRule(Rule, BaseQueryRule):
    load_potentials: bool
    excluded_clbids: FrozenSet[str] = frozenset()

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "from" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: List[str], ctx: Optional['RequirementContext'] = None) -> 'QueryRule':
        path = [*path, f".query"]

        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c=c, ctx=ctx)

        limit = LimitSet.load(data=data.get("limit", None), c=c)

        if 'limits' in data:
            raise ValueError(f'the key is "limit", not "limits": {data}')

        assertions: List[Union[AssertionRule, ConditionalAssertionRule]]
        if "assert" in data:
            assertions = [AssertionRule.load({'assert': data["assert"]}, c=c, ctx=ctx, path=[*path, ".assertions", "[0]"])]
        elif "all" in data:
            assertions = [ConditionalAssertionRule.load(d, c=c, ctx=ctx, path=[*path, ".assertions", f"[{i}]"]) for i, d in enumerate(data["all"])]
        else:
            raise ValueError(f'you must have either an assert: or an all: key in {data}')

        assert len(assertions) > 0

        if 'assert' in data and 'all' in data:
            raise ValueError(f'you cannot have both assert: and all: keys; {data}')

        allowed_keys = {'where', 'limit', 'claim', 'assert', 'all', 'allow_claimed', 'from', 'load_potentials'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        allow_claimed = data.get('allow_claimed', False)

        source = QuerySource(data['from'])
        if source is QuerySource.Claimed:
            allow_claimed = True

        return QueryRule(
            source=source,
            assertions=tuple(assertions),
            limit=limit,
            where=where,
            allow_claimed=allow_claimed,
            attempt_claims=data.get('claim', True) is True,
            record_claims=data.get('claim', True) in ('record', True),
            load_potentials=data.get('load_potentials', True),
            path=tuple(path),
            inserted=tuple(),
            force_inserted=tuple(),
        )

    def exclude_required_courses(self, to_exclude: Collection['CourseInstance']) -> 'QueryRule':
        clbids = frozenset(c.clbid for c in to_exclude)
        logger.debug(f'{self.path} excluding required courses: {sorted(c for c in clbids)}')
        return attr.evolve(self, excluded_clbids=clbids)

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.assertions:
            for a in self.assertions:
                a.validate(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return []

    def get_required_courses(self, *, ctx: 'RequirementContext') -> Collection['CourseInstance']:
        return tuple()

    def get_data(self, *, ctx: 'RequirementContext') -> Sequence[Clausable]:
        if self.source is QuerySource.Courses:
            all_courses = ctx.transcript()
            return [c for c in all_courses if c.clbid not in self.excluded_clbids]

        if self.source is QuerySource.Claimed:
            return []

        elif self.source is QuerySource.Areas:
            return list(ctx.areas)

        elif self.source is QuerySource.MusicPerformances:
            return list(ctx.music_performances)

        elif self.source is QuerySource.MusicAttendances:
            return list(ctx.music_attendances)

        else:
            raise TypeError(f'unknown type of data for query, {self.source}')

    def get_filtered_data(self, *, ctx: 'RequirementContext') -> Tuple[List[Clausable], Tuple[str, ...], Tuple[str, ...]]:
        if self.where is not None:
            data = [item for item in self.get_data(ctx=ctx) if apply_clause(self.where, item)]
        else:
            data = list(self.get_data(ctx=ctx))

        inserted_clbids: Tuple[str, ...] = tuple()
        force_inserted_clbids: Tuple[str, ...] = tuple()
        if self.source in (QuerySource.Courses, QuerySource.Claimed):
            for insert in ctx.get_insert_exceptions(self.path):
                inserted_clbids = (*inserted_clbids, insert.clbid)
                if insert.forced:
                    force_inserted_clbids = (*force_inserted_clbids, insert.clbid)

                matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)
                data.append(matched_course)

        return data, inserted_clbids, force_inserted_clbids

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[QuerySolution]:
        if ctx.get_waive_exception(self.path):
            logger.debug("forced override on %s", self.path)
            yield QuerySolution.from_rule(rule=self, output=tuple(), overridden=True)
            return

        data, inserted_clbids, force_inserted_clbids = self.get_filtered_data(ctx=ctx)

        if self.source is QuerySource.Claimed:
            yield QuerySolution.from_rule(rule=self, output=tuple(), inserted=inserted_clbids, force_inserted=force_inserted_clbids)
            return

        elif self.source is QuerySource.Courses:
            did_iter = False
            for item_set in self.limit.limited_transcripts(cast(Tuple[CourseInstance, ...], data)):
                if self.attempt_claims is False:
                    did_iter = True

                    # If we want to make things go green sooner, turn this on
                    only_completed = tuple(c for c in item_set if c.is_in_progress is False)
                    yield QuerySolution.from_rule(rule=self, output=only_completed, inserted=inserted_clbids, force_inserted=force_inserted_clbids)

                    yield QuerySolution.from_rule(rule=self, output=item_set, inserted=inserted_clbids, force_inserted=force_inserted_clbids)
                    continue

                for combo in iterate_item_set(item_set, rule=self):
                    did_iter = True
                    yield QuerySolution.from_rule(output=combo, rule=self, inserted=inserted_clbids, force_inserted=force_inserted_clbids)

        else:
            for combo in iterate_item_set(data, rule=self):
                did_iter = True
                yield QuerySolution.from_rule(output=combo, rule=self, inserted=inserted_clbids, force_inserted=force_inserted_clbids)

        if not did_iter:
            # be sure we always yield something
            logger.debug("%s did not yield anything; yielding empty collection", self.path)
            yield QuerySolution.from_rule(rule=self, output=tuple(), inserted=inserted_clbids, force_inserted=force_inserted_clbids)

    def estimate(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> int:
        if ctx.get_waive_exception(self.path):
            return 1

        data, _, _ = self.get_filtered_data(ctx=ctx)

        acc = 0
        if self.source in (QuerySource.Courses, QuerySource.Claimed):
            for item_set in self.limit.limited_transcripts(cast(Tuple[CourseInstance, ...], data)):
                if self.attempt_claims is False:
                    acc += 1
                    acc += 1

                acc += estimate_item_set(item_set, rule=self)
        else:
            acc += estimate_item_set(data, rule=self)

        if acc == 0:
            # be sure we always yield something
            acc += 1

        return acc

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if self._has_potential(ctx=ctx):
            logger.debug('%s has potential: yes', self.path)
            return True
        else:
            logger.debug('%s has potential: no', self.path)
            return False

    def _has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if ctx.has_exception(self.path):
            return True

        if has_assertion(self.assertions, key=is_lt_clause):
            return True

        if has_assertion(self.assertions, key=is_at_least_0_clause):
            return True

        if self.source is QuerySource.Claimed:
            return True

        if self.where is None:
            return len(self.get_data(ctx=ctx)) > 0

        return any(apply_clause(self.where, item) for item in self.get_data(ctx=ctx))

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        matches = list(self.get_data(ctx=ctx))

        if self.where is not None:
            matches = [item for item in matches if apply_clause(self.where, item)]

        for insert in ctx.get_insert_exceptions(self.path):
            matches.append(ctx.forced_course_by_clbid(insert.clbid, path=self.path))

        return matches

    def is_always_disjoint(self) -> bool:
        if self.allow_claimed is True and self.attempt_claims is False and self.source is not QuerySource.Claimed:
            return True

        return False

    def is_never_disjoint(self) -> bool:
        if self.source is QuerySource.Claimed:
            return True

        return False


def has_assertion(assertions: Sequence[Union[AssertionRule, ConditionalAssertionRule]], key: Callable[[SingleClause], bool]) -> bool:
    if not assertions:
        return False

    for assertion in assertions:
        if isinstance(assertion, ConditionalAssertionRule):
            if check_assertion(assertion.when_yes, key) or check_assertion(assertion.when_no, key):
                return True

        elif check_assertion(assertion, key):
            return True

    return False


def check_assertion(assertion: Optional[AssertionRule], key: Callable[[SingleClause], bool]) -> Optional[bool]:
    if not assertion:
        return None
    if assertion.where is not None:
        return None
    if key(assertion.assertion):
        return True
    return None


def is_simple_count_clause(clause: SingleClause) -> bool:
    return clause.key in ('count(courses)', 'count(terms)')


def is_simple_sum_clause(clause: SingleClause) -> bool:
    return clause.key in ('sum(credits)',)


def is_lt_clause(clause: SingleClause) -> bool:
    return clause.operator in (Operator.LessThan, Operator.LessThanOrEqualTo)


def is_at_least_0_clause(clause: SingleClause) -> bool:
    return clause.operator is Operator.GreaterThanOrEqualTo and clause.expected == 0


def find_largest_simple_count_assertion(assertions: Sequence[AssertionRule]) -> Optional[AssertionRule]:
    if not assertions:
        return None

    largest_assertion = None
    largest_count = -1
    for assertion in assertions:
        if is_simple_count_clause(assertion.assertion):
            if type(assertion.assertion.expected) == int and assertion.assertion.expected > largest_count:
                largest_assertion = assertion
                largest_count = assertion.assertion.expected

    return largest_assertion


def find_largest_simple_sum_assertion(assertions: Sequence[AssertionRule]) -> Optional[AssertionRule]:
    if not assertions:
        return None

    largest_assertion = None
    largest_expected = -1
    for assertion in assertions:
        if is_simple_sum_clause(assertion.assertion):
            if type(assertion.assertion.expected) in (int, decimal.Decimal) and assertion.assertion.expected > largest_expected:
                largest_assertion = assertion
                largest_expected = assertion.assertion.expected

    return largest_assertion


def iterate_item_set(item_set: Collection[Clausable], *, rule: QueryRule) -> Iterator[Tuple[Clausable, ...]]:
    assertions = []

    for a in rule.all_assertions():
        if isinstance(a, AssertionRule):
            assertions.append(a)
        elif isinstance(a, AssertionResult):
            raise TypeError('unexpected AssertionResult; expected AssertionRule')
        else:
            assertions.append(a.when_yes)
            if a.when_no:
                assertions.append(a.when_no)

    if rule.source is QuerySource.Courses:
        simple_count_assertion = find_largest_simple_count_assertion(assertions)
        if simple_count_assertion is not None:
            logger.debug("%s using simple assertion mode with %s", rule.path, simple_count_assertion)
            for n in simple_count_assertion.input_size_range(maximum=len(item_set)):
                yield from itertools.combinations(item_set, n)
            return

        simple_sum_assertion = find_largest_simple_sum_assertion(assertions)
        if simple_sum_assertion is not None:
            logger.debug("%s using simple-sum assertion mode with %s", rule.path, simple_sum_assertion)
            item_set_courses = cast(Sequence[CourseInstance], item_set)

            # We can skip outputs with impunity here, because the calling
            # function will ensure that the fallback set is attempted
            if sum(c.credits for c in item_set_courses) < simple_sum_assertion.assertion.expected:
                return

            for n in range(1, len(item_set_courses) + 1):
                for combo in itertools.combinations(item_set_courses, n):
                    if sum(c.credits for c in combo) >= simple_sum_assertion.assertion.expected:
                        yield combo
            return

        logger.debug("%s not running single assertion mode", rule.path)
        for n in range(1, len(item_set) + 1):
            yield from itertools.combinations(item_set, n)

    else:
        yield tuple(item_set)


def estimate_item_set(item_set: Collection[Clausable], *, rule: QueryRule) -> int:
    # This is known to over-estimate the number of items, because it doesn't
    # check the credit sum inside of simple_sum_assertion.
    total = 0

    assertions = []
    for a in rule.all_assertions():
        if isinstance(a, AssertionRule):
            assertions.append(a)
        elif isinstance(a, AssertionResult):
            raise TypeError('unexpected AssertionResult; expected AssertionRule')
        else:
            assertions.append(a.when_yes)
            if a.when_no:
                assertions.append(a.when_no)

    if rule.source is QuerySource.Courses:
        simple_count_assertion = find_largest_simple_count_assertion(assertions)
        if simple_count_assertion is not None:
            for n in simple_count_assertion.input_size_range(maximum=len(item_set)):
                total += ncr(n=len(item_set), r=n)
            return total

        simple_sum_assertion = find_largest_simple_sum_assertion(assertions)
        if simple_sum_assertion is not None:
            item_set_courses = cast(Sequence[CourseInstance], item_set)

            # We can skip outputs with impunity here, because the calling
            # function will ensure that the fallback set is attempted
            if sum(c.credits for c in item_set_courses) < simple_sum_assertion.assertion.expected:
                return total

            for n in range(1, len(item_set_courses) + 1):
                total += ncr(n=len(item_set_courses), r=n)
                # for combo in itertools.combinations(item_set_courses, n):
                #     if sum(c.credits for c in combo) >= simple_sum_assertion.expected:
                #         total += 1
            return total

        logger.debug("%s not running single assertion mode", rule.path)
        for n in range(1, len(item_set) + 1):
            total += ncr(n=len(item_set), r=n)

    else:
        total += 1

    return total
