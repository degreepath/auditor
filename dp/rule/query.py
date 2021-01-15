import attr
from typing import Dict, List, Optional, Sequence, Iterator, Iterable, Collection, FrozenSet, Tuple, cast, TYPE_CHECKING
import itertools
import logging
import decimal

from ..base import Rule, BaseQueryRule
from ..base.query import QuerySource
from ..data_type import DataType
from ..limit import LimitSet
from ..predicate_clause import load_predicate
from ..assertion_clause import AnyAssertion, SomeAssertion, Assertion, ConditionalAssertion, DynamicConditionalAssertion
from ..data.clausable import Clausable
from ..ncr import ncr
from ..solution.query import QuerySolution
from ..constants import Constants
from ..data.course import CourseInstance
from ..exception import BlockException

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
    def load(data: Dict, *, c: Constants, path: Sequence[str], ctx: 'RequirementContext') -> 'QueryRule':
        path = tuple([*path, ".query"])

        source = QuerySource(data['from'])

        if source in (QuerySource.Courses, QuerySource.Claimed):
            data_type = DataType.Course
        elif source is QuerySource.Areas:
            data_type = DataType.Area
        elif source is QuerySource.MusicAttendances:
            data_type = DataType.Recital
        elif source is QuerySource.MusicPerformances:
            data_type = DataType.MusicPerformance
        else:
            raise TypeError(f'unexpected query source {source!r}')

        where = data.get("where", None)
        if where is not None:
            where = load_predicate(where, c=c, ctx=ctx, mode=data_type)

        limit = LimitSet.load(data=data.get("limit", None), c=c, ctx=ctx)

        if 'limits' in data:
            raise ValueError(f'the key is "limit", not "limits": {data}')

        assertions: Tuple[AnyAssertion, ...]
        if "assert" in data:
            a = DynamicConditionalAssertion.load({'assert': data["assert"]}, data_type=data_type, c=c, ctx=ctx, path=[*path, ".assertions", "[0]"])
            assertions = tuple([a])
        elif "all" in data:
            assertions = tuple(
                DynamicConditionalAssertion.load(d, data_type=data_type, c=c, ctx=ctx, path=[*path, ".assertions", f"[{i}]"])
                for i, d in enumerate(data["all"])
            )
        else:
            raise ValueError(f'you must have either an assert: or an all: key in {data}')

        assert len(assertions) > 0, ValueError(f'there must be at least one assertion: {data}')

        if 'assert' in data and 'all' in data:
            raise ValueError(f'you cannot have both assert: and all: keys; {data}')

        allowed_keys = {'where', 'limit', 'claim', 'assert', 'all', 'allow_claimed', 'from', 'load_potentials', 'include_failed'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        allow_claimed = data.get('allow_claimed', False)

        if source is QuerySource.Claimed:
            allow_claimed = True

        overridden = False
        if ctx.get_waive_exception(path) is not None:
            overridden = True

        return QueryRule(
            source=source,
            data_type=data_type,
            assertions=assertions,
            limit=limit,
            where=where,
            allow_claimed=allow_claimed,
            attempt_claims=data.get('claim', True) is True,
            record_claims=data.get('claim', True) in ('record', True),
            load_potentials=data.get('load_potentials', True),
            path=tuple(path),
            inserted=tuple(),
            force_inserted=tuple(),
            overridden=overridden,
            output=tuple(),
            successful_claims=tuple(),
            failed_claims=tuple(),
            include_failed=data.get('include_failed', False),
        )

    def exclude_required_courses(self, to_exclude: Collection['CourseInstance']) -> 'QueryRule':
        clbids = set(c.clbid for c in to_exclude)
        logger.debug('%s excluding required courses: %s', self.path, clbids)
        return attr.evolve(self, excluded_clbids=frozenset([*self.excluded_clbids, *clbids]))

    def apply_block_exception(self, to_block: BlockException) -> 'QueryRule':
        if self.path != to_block.path:
            return self

        logger.debug('%s excluding blocked clbid %s', self.path, to_block.clbid)
        return attr.evolve(self, excluded_clbids=frozenset([*self.excluded_clbids, to_block.clbid]))

    def get_requirement_names(self) -> List[str]:
        return []

    def get_required_courses(self, *, ctx: 'RequirementContext') -> Collection['CourseInstance']:
        return tuple()

    def get_data(self, *, ctx: 'RequirementContext') -> Iterable[Clausable]:
        if self.source is QuerySource.Courses:
            all_courses = ctx.transcript()
            if self.include_failed:
                all_courses = ctx.transcript_with_failed_

            if self.excluded_clbids:
                return (c for c in all_courses if c.clbid not in self.excluded_clbids)
            else:
                return all_courses

        if self.source is QuerySource.Claimed:
            return []

        elif self.source is QuerySource.Areas:
            return ctx.areas

        elif self.source is QuerySource.MusicPerformances:
            return ctx.music_performances

        elif self.source is QuerySource.MusicAttendances:
            return ctx.music_attendances

        else:
            raise TypeError(f'unknown type of data for query, {self.source}')

    def get_filtered_data(self, *, ctx: 'RequirementContext') -> Tuple[List[Clausable], Tuple[str, ...], Tuple[str, ...]]:
        if self.where is not None:
            data = [item for item in self.get_data(ctx=ctx) if self.where.apply(item)]
        else:
            data = list(self.get_data(ctx=ctx))

        inserted_clbids: Tuple[str, ...] = tuple()
        force_inserted_clbids: Tuple[str, ...] = tuple()
        if self.source in (QuerySource.Courses, QuerySource.Claimed):
            for insert in ctx.get_insert_exceptions(self.path):
                if insert.clbid in self.excluded_clbids:
                    continue

                inserted_clbids = (*inserted_clbids, insert.clbid)
                if insert.forced:
                    force_inserted_clbids = (*force_inserted_clbids, insert.clbid)
                    matched_course = ctx.forced_course_by_clbid(insert.clbid, path=self.path)
                    data.append(matched_course)
                else:
                    maybe_matched_course = ctx.find_course_by_clbid(insert.clbid)
                    if maybe_matched_course is not None:
                        data.append(maybe_matched_course)

        return data, inserted_clbids, force_inserted_clbids

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[QuerySolution]:
        if self.overridden:
            logger.debug("forced override on %s", self.path)
            yield QuerySolution.from_rule(rule=self, output=tuple())
            return

        data, inserted_clbids, force_inserted_clbids = self.get_filtered_data(ctx=ctx)
        did_iter = False

        if self.source is QuerySource.Claimed:
            yield QuerySolution.from_rule(rule=self, output=tuple(), inserted=inserted_clbids, force_inserted=force_inserted_clbids)
            return

        elif self.source is QuerySource.Courses:
            courses = cast(Tuple[CourseInstance, ...], data)

            for item_set in self.limit.limited_transcripts(courses, forced_clbids=force_inserted_clbids):
                if self.attempt_claims is False:
                    did_iter = True
                    yield QuerySolution.from_rule(rule=self, output=item_set, inserted=inserted_clbids, force_inserted=force_inserted_clbids)
                    continue

                for combo in iterate_item_set(item_set, rule=self):
                    for inserted_clbid in set(inserted_clbids).union(set(force_inserted_clbids)):
                        inserted_course = [c for c in item_set if c.clbid == inserted_clbid]
                        if inserted_course:
                            combo = tuple([*combo, inserted_course[0]])

                    did_iter = True
                    yield QuerySolution.from_rule(rule=self, output=combo, inserted=inserted_clbids, force_inserted=force_inserted_clbids)

        else:
            for combo in iterate_item_set(data, rule=self):
                for inserted_clbid in set(inserted_clbids).union(set(force_inserted_clbids)):
                    inserted_course = next(c for c in courses if c.clbid == inserted_clbid)
                    combo = tuple([*combo, inserted_course])

                did_iter = True
                yield QuerySolution.from_rule(rule=self, output=combo, inserted=inserted_clbids, force_inserted=force_inserted_clbids)

        if not did_iter:
            # be sure we always yield something
            logger.debug("%s did not yield anything; yielding empty collection", self.path)
            yield QuerySolution.from_rule(rule=self, output=tuple(), inserted=inserted_clbids, force_inserted=force_inserted_clbids)

    def estimate(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> int:
        if ctx.get_waive_exception(self.path):
            return 1

        data, _, force_inserted_clbids = self.get_filtered_data(ctx=ctx)

        acc = 0
        if self.source in (QuerySource.Courses, QuerySource.Claimed):
            courses = cast(Tuple[CourseInstance, ...], data)
            for item_set in self.limit.limited_transcripts(courses, forced_clbids=force_inserted_clbids):
                if self.attempt_claims is False:
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
        if ctx.has_exception_beneath(self.path):
            return True

        if any(a.is_lt_clause() for a in self.assertions):
            return True

        if any(a.is_at_least_0_clause() for a in self.assertions):
            return True

        if self.source is QuerySource.Claimed:
            return True

        if self.where is None:
            for _ in self.get_data(ctx=ctx):
                return True
            return False

        return any(self.where.apply(item) for item in self.get_data(ctx=ctx))

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        matches, _, _ = self.get_filtered_data(ctx=ctx)
        return matches

    def is_always_disjoint(self) -> bool:
        if self.allow_claimed is True and self.attempt_claims is False and self.source is not QuerySource.Claimed:
            return True

        return False

    def is_never_disjoint(self) -> bool:
        if self.source is QuerySource.Claimed:
            return True

        return False


def find_largest_simple_count_assertion(assertions: Sequence[SomeAssertion]) -> Optional[SomeAssertion]:
    def _expected(a: Optional[SomeAssertion]) -> decimal.Decimal:
        if not a:
            return decimal.Decimal(0)
        return a.max_expected()

    simple_clauses = (a for a in assertions if a.is_simple_count_clause())
    return max(simple_clauses, key=_expected, default=None)


def find_largest_simple_sum_assertion(assertions: Sequence[SomeAssertion]) -> Optional[SomeAssertion]:
    def _expected(a: Optional[SomeAssertion]) -> decimal.Decimal:
        if not a:
            return decimal.Decimal(0)
        return a.max_expected()

    simple_clauses = (a for a in assertions if a.is_simple_sum_clause())
    return max(simple_clauses, key=_expected, default=None)


def flatten_assertions(it: Iterable[AnyAssertion]) -> Iterator[Assertion]:
    for a in it:
        if isinstance(a, Assertion):
            yield a
        elif isinstance(a, ConditionalAssertion):
            yield a.when_true
            if a.when_false:
                yield a.when_false
        elif isinstance(a, DynamicConditionalAssertion):
            yield a.when_true
        else:
            raise ValueError('uh oh')


def iterate_item_set(item_set: Collection[Clausable], *, rule: QueryRule) -> Iterator[Tuple[Clausable, ...]]:
    assertions = list(flatten_assertions(rule.all_assertions()))

    if rule.source is QuerySource.Courses:
        largest_count_assertion = find_largest_simple_count_assertion(assertions)
        if largest_count_assertion is not None:
            yield from iterate_item_set__count_shortcut(assertion=largest_count_assertion, items=item_set, rule=rule)
            return

        largest_sum_assertion = find_largest_simple_sum_assertion(assertions)
        if largest_sum_assertion is not None:
            yield from iterate_item_set__sum_shortcut(
                assertion=largest_sum_assertion,
                items=cast(Sequence[CourseInstance], item_set),
                rule=rule,
            )
            return

        logger.debug("%s not running single assertion mode", rule.path)
        for n in range(1, len(item_set) + 1):
            yield from itertools.combinations(item_set, n)

    else:
        yield tuple(item_set)


def iterate_item_set__count_shortcut(*, assertion: SomeAssertion, items: Collection[Clausable], rule: QueryRule) -> Iterator[Tuple[Clausable, ...]]:
    logger.debug("using simple assertion mode with %r (at %s)", assertion, rule.path)
    for n in assertion.input_size_range(maximum=len(items)):
        yield from itertools.combinations(items, n)


def iterate_item_set__sum_shortcut(*, assertion: SomeAssertion, items: Collection[CourseInstance], rule: QueryRule) -> Iterator[Tuple[Clausable, ...]]:
    logger.debug("using simple-sum assertion mode with %r (at %s)", assertion, rule.path)
    expected_credits = assertion.max_expected()

    # We can skip outputs with impunity here, because the calling
    # function will ensure that the fallback set is attempted
    known_credits = sum(c.credits for c in items)
    if known_credits < expected_credits:
        logger.debug("%s bailing because %s is less than %s", rule.path, known_credits, expected_credits)
        yield tuple(items)
        return

    for n in range(1, len(items) + 1):
        for combo in itertools.combinations(items, n):
            if sum(c.credits for c in combo) >= expected_credits:
                yield combo


def estimate_item_set(item_set: Collection[Clausable], *, rule: QueryRule) -> int:
    # This is known to over-estimate the number of items, because it doesn't
    # check the credit sum inside of simple_sum_assertion.
    total = 0

    assertions = list(flatten_assertions(rule.all_assertions()))

    if rule.source is QuerySource.Courses:
        largest_count_assertion = find_largest_simple_count_assertion(assertions)
        if largest_count_assertion is not None:
            for n in largest_count_assertion.input_size_range(maximum=len(item_set)):
                total += ncr(n=len(item_set), r=n)
            return total

        largest_sum_assertion = find_largest_simple_sum_assertion(assertions)
        if largest_sum_assertion is not None:
            item_set_courses = cast(Sequence[CourseInstance], item_set)

            # We can skip outputs with impunity here, because the calling
            # function will ensure that the fallback set is attempted
            if sum(c.credits for c in item_set_courses) < largest_sum_assertion.max_expected():
                return total + 1

            for n in range(1, len(item_set_courses) + 1):
                total += ncr(n=len(item_set_courses), r=n)
                # for combo in itertools.combinations(item_set_courses, n):
                #     if sum(c.credits for c in combo) >= largest_sum_assertion.expected:
                #         total += 1
            return total

        logger.debug("%s not running single assertion mode", rule.path)
        for n in range(1, len(item_set) + 1):
            total += ncr(n=len(item_set), r=n)

    else:
        total += 1

    return total
