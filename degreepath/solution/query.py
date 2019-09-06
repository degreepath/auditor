import attr
from typing import List, Sequence, Any, Tuple, TypeVar, Union, Set, FrozenSet, Dict, cast, TYPE_CHECKING
from collections import Counter, defaultdict
import logging
import decimal

from ..base import Solution, BaseQueryRule
from ..result.query import QueryResult
from ..rule.assertion import AssertionRule
from ..result.assertion import AssertionResult
from ..data import CourseInstance, AreaPointer, Clausable
from ..clause import SingleClause, Operator
from ..lib import grade_point_average_items, grade_point_average

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
            inserted=rule.inserted,
            load_potentials=rule.load_potentials,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "output": [x.to_dict() for x in self.output],
        }

    def audit(self, *, ctx: 'RequirementContext') -> QueryResult:  # noqa: C901
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

        inserted_clbids = []
        for insert in ctx.get_insert_exceptions(self.path):
            matched_course = ctx.forced_course_by_clbid(insert.clbid)
            clause = SingleClause(key='clbid', operator=Operator.EqualTo, expected=insert.clbid, expected_verbatim=insert.clbid)
            claim = ctx.make_claim(course=matched_course, path=self.path, clause=clause)

            if claim.failed():
                if debug: logger.debug('%s course "%s" exists, but has already been claimed by %s', self.path, insert.clbid, claim.conflict_with)
                failed_claims.append(claim)
            else:
                if debug: logger.debug('%s course "%s" exists, and is available', self.path, insert.clbid)
                successful_claims.append(claim)
                claimed_items.append(matched_course)
                inserted_clbids.append(matched_course.clbid)

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
            inserted=tuple(inserted_clbids),
        )

    def apply_assertion(self, clause: AssertionRule, *, ctx: 'RequirementContext', output: Sequence[Clausable] = tuple()) -> AssertionResult:
        if not isinstance(clause, AssertionRule):
            raise TypeError(f"expected a query assertion; found {clause} ({type(clause)})")

        exception = ctx.get_waive_exception(clause.path)
        if exception:
            logger.debug("forced override on %s", self.path)
            return AssertionResult(
                where=clause.where,
                assertion=clause.assertion,
                path=clause.path,
                message=clause.message,
                overridden=True,
                inserted=tuple(),
            )

        if clause.where is not None:
            filtered_output = [item for item in output if item.apply_clause(clause.where)]
        else:
            filtered_output = list(output)

        inserted_clbids = []
        for insert in ctx.get_insert_exceptions(clause.path):
            logger.debug("inserted %s into %s", insert.clbid, self.path)
            matched_course = ctx.forced_course_by_clbid(insert.clbid)
            filtered_output.append(matched_course)
            inserted_clbids.append(matched_course.clbid)

        result = clause.assertion.compare_and_resolve_with(value=filtered_output, map_func=apply_clause_to_query_rule)
        return AssertionResult(
            where=clause.where,
            assertion=result,
            path=clause.path,
            message=clause.message,
            overridden=False,
            inserted=tuple(inserted_clbids),
        )


T = TypeVar('T', str, decimal.Decimal)
QueryActionInput = Sequence[Union[CourseInstance, AreaPointer]]
FrozenCollection = Union[FrozenSet[T], Tuple[T, ...]]

QueryItemCollection = Tuple[
    Union[decimal.Decimal, int],
    FrozenCollection[T],
    Tuple[CourseInstance, ...],
]


def count_courses(data: QueryActionInput) -> QueryItemCollection[str]:
    # if TYPE_CHECKING:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items = frozenset(c for c in data)
    clbids = tuple(c.clbid for c in items)
    courses = tuple(items)
    return (len(items), clbids, courses)


def count_terms_from_most_common_course(data: QueryActionInput) -> QueryItemCollection[str]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)

    if not data:
        return (0, frozenset(), tuple())

    counted = Counter(c.crsid for c in data)
    most_common = counted.most_common(1)[0]
    most_common_crsid, _count = most_common

    items = frozenset(str(c.year) + str(c.term) for c in data if c.crsid == most_common_crsid)
    courses = tuple(c for c in data if c.crsid == most_common_crsid)
    return (len(items), items, courses)


def count_subjects(data: QueryActionInput) -> QueryItemCollection[str]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        for s in c.subject:
            if s not in items:
                items.add(s)
                courses.add(c)

    return (len(items), frozenset(items), tuple(courses))


def count_terms(data: QueryActionInput) -> QueryItemCollection[str]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_value = str(c.year) + str(c.term)
        if str_value not in items:
            items.add(str_value)
            courses.add(c)

    return (len(items), frozenset(items), tuple(courses))


def count_years(data: QueryActionInput) -> QueryItemCollection[str]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_year = str(c.year)
        if str_year not in items:
            items.add(str_year)
            courses.add(c)

    return (len(items), frozenset(items), tuple(courses))


def count_distinct_courses(data: QueryActionInput) -> QueryItemCollection[str]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        if c.crsid not in items:
            items.add(c.crsid)
            courses.add(c)

    return (len(items), frozenset(items), tuple(courses))


def count_areas(data: QueryActionInput) -> QueryItemCollection[str]:
    assert all(isinstance(x, AreaPointer) for x in data)
    areas: Tuple[AreaPointer, ...] = cast(Tuple[AreaPointer, ...], data)
    area_codes = frozenset(a.code for a in areas)
    return (len(area_codes), area_codes, tuple())


def count_performances(data: QueryActionInput) -> QueryItemCollection[str]:
    # TODO
    raise TypeError('count(performances) is not yet implemented')


def count_seminars(data: QueryActionInput) -> QueryItemCollection[str]:
    # TODO
    raise TypeError('count(seminars) is not yet implemented')


def sum_grades(data: QueryActionInput) -> QueryItemCollection[decimal.Decimal]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items = tuple(c.grade_points for c in data if c.is_in_gpa)
    courses = tuple(c for c in data if c.is_in_gpa)

    return (sum(items), items, courses)


def sum_credits(data: QueryActionInput) -> QueryItemCollection[decimal.Decimal]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    data = [c for c in data if c.credits > 0]
    data = cast(Tuple[CourseInstance, ...], data)
    items = tuple(c.credits for c in data)
    courses = tuple(data)
    return (sum(items), items, courses)


def sum_credits_from_single_subject(data: QueryActionInput) -> QueryItemCollection[decimal.Decimal]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    data = [c for c in data if c.credits > 0]
    data = cast(Tuple[CourseInstance, ...], data)

    if not data:
        return (decimal.Decimal(0), tuple([decimal.Decimal(0)]), tuple())

    # This should sort the subjects by the number of credits under that
    # subject code, then pick the one with the most credits as the
    # "single_subject"

    by_credits: Dict[str, decimal.Decimal] = defaultdict(decimal.Decimal)

    for c in data:
        for s in c.subject:
            by_credits[s] += c.credits

    best_subject = max(by_credits.keys(), key=lambda subject: by_credits[subject])

    items = tuple(c.credits for c in data if best_subject in c.subject)
    courses = tuple(c for c in data if best_subject in c.subject)
    return (sum(items), items, courses)


def average_grades(data: QueryActionInput) -> QueryItemCollection[decimal.Decimal]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    avg = grade_point_average(data)
    courses = tuple(grade_point_average_items(data))
    items = tuple(c.grade_points for c in courses)
    return (avg, items, courses)


def average_credits(data: QueryActionInput) -> QueryItemCollection[decimal.Decimal]:
    assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple[CourseInstance, ...], data)
    items = tuple(c.credits for c in data)
    courses = tuple(data)
    return (avg_or_0(items), items, courses)


actions = {
    'count(courses)': count_courses,
    'count(terms_from_most_common_course)': count_terms_from_most_common_course,
    'count(subjects)': count_subjects,
    'count(terms)': count_terms,
    'count(years)': count_years,
    'count(distinct_courses)': count_distinct_courses,
    'count(areas)': count_areas,
    'count(performances)': count_performances,
    'count(seminars)': count_seminars,

    'sum(grades)': sum_grades,
    'sum(credits)': sum_credits,
    'sum(credits_from_single_subject)': sum_credits_from_single_subject,

    'average(grades)': average_grades,
    'average(credits)': average_credits,
}


def apply_clause_to_query_rule(*, value: QueryActionInput, clause: SingleClause) -> QueryItemCollection:
    action = actions.get(clause.key, None)

    if action is None:
        raise Exception(f'got {clause.key}; expected one of {sorted(actions.keys())}')

    return action(value)


def avg_or_0(items: Sequence[decimal.Decimal]) -> decimal.Decimal:
    if not items:
        return decimal.Decimal('0.00')

    return sum(items) / decimal.Decimal(len(items))
