from typing import Sequence, Tuple, Set, Dict, Mapping, FrozenSet, Callable, Collection, Union, cast, TYPE_CHECKING
from collections import Counter, defaultdict
from decimal import Decimal

import attr

from .lib import grade_point_average_items, grade_point_average

if TYPE_CHECKING:
    from .data import CourseInstance, AreaPointer, Clausable  # noqa: F401
    from .clause import SingleClause


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AppliedClauseResult:
    value: Union[int, Decimal]
    data: Union[FrozenSet[str], FrozenSet[Decimal], Tuple[str, ...], Tuple[Decimal, ...]] = tuple()
    courses: Collection['CourseInstance'] = tuple()


def count_items_test(data: Sequence['Clausable']) -> AppliedClauseResult:
    items = frozenset(repr(c) for c in data)

    return AppliedClauseResult(value=len(items), data=items, courses=tuple())


def count_courses(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)

    items = frozenset(c for c in data)
    clbids = tuple(sorted(c.clbid for c in items))
    courses = tuple(items)

    return AppliedClauseResult(value=len(items), data=clbids, courses=courses)


def count_terms_from_most_common_course(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)

    if not data:
        return AppliedClauseResult(value=0)

    counted = Counter(c.crsid for c in data)
    most_common = counted.most_common(1)[0]
    most_common_crsid, _count = most_common

    items = tuple(sorted(str(c.year) + str(c.term) for c in data if c.crsid == most_common_crsid))
    courses = tuple(c for c in data if c.crsid == most_common_crsid)

    return AppliedClauseResult(value=len(items), data=items, courses=courses)


def count_subjects(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        for s in c.subject:
            if s not in items:
                items.add(s)
                courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_terms(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_value = str(c.year) + str(c.term)
        if str_value not in items:
            items.add(str_value)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_years(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_year = str(c.year)
        if str_year not in items:
            items.add(str_year)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_distinct_courses(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    items: Set[str] = set()
    courses = set()

    for c in data:
        if c.crsid not in items:
            items.add(c.crsid)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_areas(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, AreaPointer) for x in data)

    areas: Tuple['AreaPointer', ...] = cast(Tuple['AreaPointer', ...], data)
    area_codes = tuple(sorted(set(a.code for a in areas)))

    return AppliedClauseResult(value=len(area_codes), data=frozenset(area_codes))


def count_performances(data: Sequence['Clausable']) -> AppliedClauseResult:
    # TODO
    raise TypeError('count(performances) is not yet implemented')


def count_seminars(data: Sequence['Clausable']) -> AppliedClauseResult:
    # TODO
    raise TypeError('count(seminars) is not yet implemented')


def sum_grades(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    items = tuple(sorted(c.grade_points for c in data if c.is_in_gpa))
    courses = tuple(c for c in data if c.is_in_gpa)

    return AppliedClauseResult(value=sum(items), data=items, courses=courses)


def sum_credits(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    data = [c for c in data if c.credits > 0]
    data = cast(Tuple['CourseInstance', ...], data)
    items = tuple(sorted(c.credits for c in data))
    courses = tuple(data)

    return AppliedClauseResult(value=sum(items), data=items, courses=courses)


def sum_credits_from_single_subject(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    data = [c for c in data if c.credits > 0]
    data = cast(Tuple['CourseInstance', ...], data)

    if not data:
        return AppliedClauseResult(value=0, data=tuple([Decimal(0)]))

    # This should sort the subjects by the number of credits under that
    # subject code, then pick the one with the most credits as the
    # "single_subject"

    by_credits: Dict[str, Decimal] = defaultdict(Decimal)

    for c in data:
        for s in c.subject:
            by_credits[s] += c.credits

    best_subject = max(by_credits.keys(), key=lambda subject: by_credits[subject])

    items = tuple(sorted(c.credits for c in data if best_subject in c.subject))
    courses = tuple(c for c in data if best_subject in c.subject)

    return AppliedClauseResult(value=sum(items), data=items, courses=tuple(courses))


def average_grades(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)

    data = cast(Tuple['CourseInstance', ...], data)
    avg = grade_point_average(data)
    courses = tuple(grade_point_average_items(data))
    items = tuple(sorted(c.grade_points for c in courses))

    return AppliedClauseResult(value=avg, data=items, courses=courses)


def average_credits(data: Sequence['Clausable']) -> AppliedClauseResult:
    if TYPE_CHECKING:
        assert all(isinstance(x, CourseInstance) for x in data)
    data = cast(Tuple['CourseInstance', ...], data)

    items = tuple(sorted(c.credits for c in data))
    courses = tuple(data)
    avg = avg_or_0(items)

    return AppliedClauseResult(value=avg, data=items, courses=courses)


actions: Mapping[str, Callable[[Sequence['Clausable']], AppliedClauseResult]] = {
    'count(items)': count_items_test,

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


def apply_clause_to_assertion(clause: 'SingleClause', value: Sequence['Clausable']) -> AppliedClauseResult:
    action = actions.get(clause.key, None)

    if action is None:
        raise Exception(f'got {clause.key}; expected one of {sorted(actions.keys())}')

    return action(value)


def avg_or_0(items: Sequence[Decimal]) -> Decimal:
    if not items:
        return Decimal('0.00')

    return sum(items) / Decimal(len(items))
