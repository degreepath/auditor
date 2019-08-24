import attr
from typing import List, Sequence, Any, Tuple, Collection, Union, Set, FrozenSet, Dict, cast, TYPE_CHECKING
from collections import Counter
import logging
import decimal

from ..base import Solution, BaseQueryRule
from ..result.query import QueryResult
from ..rule.assertion import AssertionRule
from ..result.assertion import AssertionResult
from ..data import CourseInstance, AreaPointer, Clausable
from ..clause import SingleClause, Operator
from ..lib import grade_point_average_items, grade_point_average
from ..exception import InsertionException

if TYPE_CHECKING:
    from ..claim import ClaimAttempt  # noqa: F401
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QuerySolution(Solution, BaseQueryRule):
    output: Tuple[Clausable, ...]
    overridden: bool

    @staticmethod
    def from_rule(*, rule: BaseQueryRule, output: Tuple[Clausable, ...], overridden: bool = False) -> 'QuerySolution':
        return QuerySolution(
            source=rule.source,
            source_type=rule.source_type,
            source_repeats=rule.source_repeats,
            assertions=rule.assertions,
            limit=rule.limit,
            where=rule.where,
            allow_claimed=rule.allow_claimed,
            attempt_claims=rule.attempt_claims,
            output=output,
            path=rule.path,
            overridden=overridden,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "output": [x.to_dict() for x in self.output],
        }

    def audit(self, *, ctx: 'RequirementContext') -> QueryResult:
        debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        if self.overridden:
            return QueryResult.from_solution(
                solution=self,
                resolved_assertions=tuple(),
                successful_claims=tuple(),
                failed_claims=tuple(),
                success=self.overridden,
                overridden=self.overridden,
            )

        claimed_items: List[Clausable] = []
        successful_claims: List['ClaimAttempt'] = []
        failed_claims: List['ClaimAttempt'] = []

        for item in self.output:
            if isinstance(item, CourseInstance):
                if self.attempt_claims:
                    clause = self.where or SingleClause(key='crsid', operator=Operator.NotEqualTo, expected='', expected_verbatim='')
                    claim = ctx.make_claim(course=item, path=self.path, clause=clause, allow_claimed=self.allow_claimed)

                    if claim.failed():
                        if debug: logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, item.clbid, claim.conflict_with)
                        failed_claims.append(claim)
                    else:
                        if debug: logger.debug('%s course "%s" exists, and is available', self.path, item.clbid)
                        successful_claims.append(claim)
                        claimed_items.append(item)
                else:
                    if debug: logger.debug('%s course "%s" exists, and is available', self.path, item.clbid)
                    claimed_items.append(item)

            elif isinstance(item, AreaPointer):
                if debug: logger.debug('%s item "%s" exists, and is available', self.path, item)
                claimed_items.append(item)

            else:
                raise TypeError(f'expected CourseInstance or AreaPointer; got {type(item)}')

        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            matched_course = ctx.forced_course_by_clbid(exception.clbid)
            clause = SingleClause(key='clbid', operator=Operator.EqualTo, expected=exception.clbid, expected_verbatim=exception.clbid)
            claim = ctx.make_claim(course=matched_course, path=self.path, clause=clause)

            if claim.failed():
                logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, exception.clbid, claim.conflict_with)
                failed_claims.append(claim)
            else:
                logger.debug('%s course "%s" exists, and is available', self.path, exception.clbid)
                successful_claims.append(claim)
                claimed_items.append(matched_course)

        resolved_assertions = tuple(
            self.apply_assertion(a, ctx=ctx, output=claimed_items)
            for i, a in enumerate(self.assertions)
        )

        resolved_result = all(a.ok() for a in resolved_assertions)

        if debug:
            if resolved_result:
                logger.debug("%s might possibly succeed", self.path)
            else:
                logger.debug("%s did not succeed", self.path)

        return QueryResult.from_solution(
            solution=self,
            resolved_assertions=resolved_assertions,
            successful_claims=tuple(successful_claims),
            failed_claims=tuple(failed_claims),
            success=resolved_result,
        )

    def apply_assertion(self, clause: AssertionRule, *, ctx: 'RequirementContext', output: Sequence[Clausable] = tuple()) -> AssertionResult:
        if not isinstance(clause, AssertionRule):
            raise TypeError(f"expected a query assertion; found {clause} ({type(clause)})")

        exception = ctx.get_exception(clause.path)
        if exception and exception.is_pass_override():
            logger.debug("forced override on %s", self.path)
            return AssertionResult(where=clause.where, assertion=clause.assertion, path=clause.path, overridden=True)

        filtered_output = output
        if clause.where is not None:
            filtered_output = [item for item in output if item.apply_clause(clause.where)]

        result = clause.assertion.compare_and_resolve_with(value=filtered_output, map_func=apply_clause_to_query_rule)
        return AssertionResult(where=clause.where, assertion=result, path=clause.path, overridden=False)


def apply_clause_to_query_rule(*, value: Sequence[Union[CourseInstance, AreaPointer]], clause: SingleClause) -> Tuple[Union[decimal.Decimal, int], Collection[Any], Tuple[str, ...]]:
    # remove the trailing ) with [:-1], then split on the opening ( to get the two parts
    action, kind = clause.key[:-1].split('(', maxsplit=1)

    if action == 'count':
        return count_items(kind=kind, data=value)

    elif action == 'sum':
        return sum_items(kind=kind, data=value)

    elif action == 'average':
        return avg_items(kind=kind, data=value)

    raise Exception(f'expected a valid clause key; got {clause.key}')


def count_items(data: Sequence[Union[CourseInstance, AreaPointer]], kind: str) -> Tuple[int, FrozenSet[Union[str]], Tuple[str, ...]]:  # noqa: C901
    if kind == 'courses':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        items = frozenset(c.clbid for c in data)
        return (len(items), items, tuple(items))

    if kind == 'terms_from_most_common_course':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        if not data:
            return (0, frozenset(), tuple())
        counted = Counter(c.crsid for c in data)
        most_common = counted.most_common(1)[0]
        most_common_crsid, _count = most_common
        items = frozenset(str(c.year) + str(c.term) for c in data if c.crsid == most_common_crsid)
        return (len(items), items, tuple(c.clbid for c in data if c.crsid == most_common_crsid))

    if kind == 'subjects':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        _items: Set[str] = set()
        _clbids = set()
        for c in data:
            for s in c.subject:
                if s not in _items:
                    _items.add(s)
                    _clbids.add(c.clbid)
        return (len(_items), frozenset(_items), tuple(_clbids))

    if kind == 'terms':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        _items = set()
        _clbids = set()
        for c in data:
            str_value = str(c.year) + str(c.term)
            if str_value not in _items:
                _items.add(str_value)
                _clbids.add(c.clbid)
        return (len(_items), frozenset(_items), tuple(_clbids))

    if kind == 'years':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        _items = set()
        _clbids = set()
        for c in data:
            str_year = str(c.year)
            if str_year not in _items:
                _items.add(str_year)
                _clbids.add(c.clbid)
        return (len(_items), frozenset(_items), tuple(_clbids))

    if kind == 'distinct_courses':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        _items = set()
        _clbids = set()
        for c in data:
            if c.crsid not in _items:
                _items.add(c.crsid)
                _clbids.add(c.clbid)
        return (len(_items), frozenset(_items), tuple(_clbids))

    if kind == 'areas':
        assert all(isinstance(x, AreaPointer) for x in data)
        data = cast(Tuple[AreaPointer, ...], data)
        items = frozenset(c.code for c in data)
        return (len(items), items, tuple())

    if kind == 'performances':
        # TODO
        logger.info('count(performances) is not yet implemented')
        return (0, frozenset(), tuple())

    if kind == 'seminars':
        # TODO
        logger.info('count(seminars) is not yet implemented')
        return (0, frozenset(), tuple())

    raise Exception(f'expected a valid kind; got {kind}')


def sum_items(data: Sequence[Union[CourseInstance, AreaPointer]], kind: str) -> Tuple[Union[decimal.Decimal, int], Tuple[decimal.Decimal, ...], Tuple[str, ...]]:
    if kind == 'grades':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        items = tuple(c.grade_points for c in data if c.is_in_gpa)
        return (sum(items), items, tuple(c.clbid for c in data if c.is_in_gpa))

    if kind == 'credits':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        items = tuple(c.credits for c in data)
        return (sum(items), items, tuple(c.clbid for c in data))

    if kind == 'credits_from_most_common_subject':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        if not data:
            return (decimal.Decimal(0), tuple([decimal.Decimal(0)]), tuple())

        counted = Counter(s for c in data for s in c.subject)
        most_common = sorted(counted.most_common(1))[0]
        most_common_subject, _count = most_common
        items = tuple(c.credits for c in data if most_common_subject in c.subject)
        return (sum(items), items, tuple(c.clbid for c in data if most_common_subject in c.subject))

    raise Exception(f'expected a valid kind; got {kind}')


def avg_items(data: Sequence[Union[CourseInstance, AreaPointer]], kind: str) -> Tuple[decimal.Decimal, Tuple[decimal.Decimal, ...], Tuple[str, ...]]:
    if kind == 'grades':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        avg = grade_point_average(data)
        items = tuple(c.grade_points for c in grade_point_average_items(data))
        return (avg, items, tuple(c.clbid for c in grade_point_average_items(data)))

    if kind == 'credits':
        assert all(isinstance(x, CourseInstance) for x in data)
        data = cast(Tuple[CourseInstance, ...], data)
        items = tuple(c.credits for c in data)
        return (avg_or_0(items), items, tuple(c.clbid for c in data))

    raise Exception(f'expected a valid kind; got {kind}')


def avg_or_0(items: Sequence[decimal.Decimal]) -> decimal.Decimal:
    if not items:
        return decimal.Decimal('0.00')

    return decimal.Decimal(sum(items) / len(items))
