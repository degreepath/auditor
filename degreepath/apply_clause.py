from typing import Any, Sequence, Tuple, Set, Dict, Mapping, FrozenSet, Callable, Collection, Union, cast, TYPE_CHECKING
from collections import Counter, defaultdict
from decimal import Decimal

import attr

from .data import CourseInstance, AreaPointer, Clausable
from .lib import grade_point_average_items, grade_point_average

if TYPE_CHECKING:  # pragma: no cover
    from .clause import SingleClause


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AppliedClauseResult:
    value: Union[int, Decimal]
    data: Union[FrozenSet[str], FrozenSet[Decimal], Tuple[str, ...], Tuple[Decimal, ...]] = tuple()
    courses: Collection[CourseInstance] = tuple()

    def clbids(self) -> Tuple[str, ...]:
        return tuple(c.clbid for c in self.courses)

    def ip_clbids(self) -> Tuple[str, ...]:
        return tuple(c.clbid for c in self.courses if c.is_in_progress)


def count_items_test(data: Sequence[Any]) -> AppliedClauseResult:
    items = frozenset(repr(c) for c in data)

    return AppliedClauseResult(value=len(items), data=items)


def count_courses(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    items = frozenset(c for c in data)
    clbids = tuple(sorted(c.clbid for c in items))
    courses = tuple(items)

    return AppliedClauseResult(value=len(items), data=clbids, courses=courses)


def count_distinct_courses(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        if c.crsid not in items:
            items.add(c.crsid)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=courses)


def count_terms_from_most_common_course(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    if not data:
        return AppliedClauseResult(value=0)

    counted = Counter(c.crsid for c in data)
    most_common = counted.most_common(1)[0]
    most_common_crsid, _count = most_common

    items = tuple(sorted(set(str(c.year) + str(c.term) for c in data if c.crsid == most_common_crsid)))
    courses = tuple(c for c in data if c.crsid == most_common_crsid)

    return AppliedClauseResult(value=len(items), data=items, courses=courses)


def count_terms_from_most_common_course_by_name(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    if not data:
        return AppliedClauseResult(value=0)

    counted = Counter(f"{c.subject}: {c.name}" for c in data)
    most_common = counted.most_common(1)[0]
    most_common_crsid, _count = most_common

    items = tuple(sorted(set(str(c.year) + str(c.term) for c in data if f"{c.subject}: {c.name}" == most_common_crsid)))
    courses = tuple(c for c in data if f"{c.subject}: {c.name}" == most_common_crsid)

    return AppliedClauseResult(value=len(items), data=items, courses=courses)


def count_subjects(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        subject = c.subject
        if subject == 'CH/BI':
            if c.number in ('125', '126'):
                subject = 'CHEM'
            else:
                subject = 'BIO'

        if subject not in items:
            items.add(subject)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_terms(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_value = str(c.year) + str(c.term)
        if str_value not in items:
            items.add(str_value)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_math_perspectives(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    perspectives: Set[str] = set()
    courses = set()

    for c in data:
        for bucket in c.attributes:
            if bucket.startswith('math_perspective_'):
                perspectives.add(bucket)
                courses.add(c)

    return AppliedClauseResult(value=len(perspectives), data=tuple(sorted(perspectives)), courses=tuple(courses))


def count_years(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_year = str(c.year)
        if str_year not in items:
            items.add(str_year)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(sorted(items)), courses=tuple(courses))


def count_areas(data: Sequence[AreaPointer]) -> AppliedClauseResult:
    area_codes = tuple(sorted(set(a.code for a in data)))

    return AppliedClauseResult(value=len(area_codes), data=frozenset(area_codes))


def count_performances(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    # TODO
    raise TypeError('count(performances) is not yet implemented')


def count_seminars(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    # TODO
    raise TypeError('count(seminars) is not yet implemented')


def sum_credits(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    data = [c for c in data if c.credits > 0]
    items = tuple(sorted(c.credits for c in data))
    courses = tuple(data)

    return AppliedClauseResult(value=sum(items), data=items, courses=courses)


def sum_credits_from_single_subject(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    data = [c for c in data if c.credits > 0]

    if not data:
        return AppliedClauseResult(value=0, data=tuple([Decimal(0)]))

    # This should sort the subjects by the number of credits under that
    # subject code, then pick the one with the most credits as the
    # "single_subject"

    by_credits: Dict[str, Decimal] = defaultdict(Decimal)

    for c in data:
        by_credits[c.subject] += c.credits

    _credits, best_subject = max((credits, subject) for subject, credits in by_credits.items())

    items = tuple(sorted(c.credits for c in data if best_subject == c.subject))
    courses = tuple(c for c in data if best_subject == c.subject)

    return AppliedClauseResult(value=sum(items), data=items, courses=tuple(courses))


def average_grades(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    avg = grade_point_average(data)
    courses = tuple(grade_point_average_items(data))
    items = tuple(sorted(c.gpa_points for c in courses))

    return AppliedClauseResult(value=avg, data=items, courses=courses)


def average_credits(data: Sequence[CourseInstance]) -> AppliedClauseResult:
    items = tuple(sorted(c.credits for c in data))
    courses = tuple(data)
    avg = avg_or_0(items)

    return AppliedClauseResult(value=avg, data=items, courses=courses)


###


course_actions: Mapping[str, Callable[[Sequence[CourseInstance]], AppliedClauseResult]] = {
    'count(courses)': count_courses,
    'count(distinct_courses)': count_distinct_courses,
    'count(terms_from_most_common_course)': count_terms_from_most_common_course,
    'count(terms_from_most_common_course_by_name)': count_terms_from_most_common_course_by_name,
    'count(math_perspectives)': count_math_perspectives,
    'count(subjects)': count_subjects,
    'count(terms)': count_terms,
    'count(years)': count_years,

    'sum(credits)': sum_credits,
    'sum(credits_from_single_subject)': sum_credits_from_single_subject,

    'average(grades)': average_grades,
    'average(credits)': average_credits,
}

area_actions: Mapping[str, Callable[[Sequence[AreaPointer]], AppliedClauseResult]] = {
    'count(areas)': count_areas,
}

other_actions: Mapping[str, Callable[[Sequence[Any]], AppliedClauseResult]] = {
    'count(items)': count_items_test,
    'count(performances)': count_performances,
    'count(seminars)': count_seminars,
}


def apply_clause_to_assertion(clause: 'SingleClause', value: Sequence[Clausable]) -> AppliedClauseResult:
    if not value:
        return AppliedClauseResult(value=0, data=tuple(), courses=tuple())

    if isinstance(value[0], CourseInstance):
        return apply_clause_to_assertion_with_courses(clause, cast(Sequence[CourseInstance], value))

    if isinstance(value[0], AreaPointer):
        return apply_clause_to_assertion_with_areas(clause, cast(Sequence[AreaPointer], value))

    return apply_clause_to_assertion_with_data(clause, cast(Sequence[Any], value))


def apply_clause_to_assertion_with_courses(clause: 'SingleClause', value: Sequence[CourseInstance]) -> AppliedClauseResult:
    action = course_actions.get(clause.key, None)

    if action is None:
        raise Exception(f'got {clause.key}; expected one of {sorted(course_actions.keys())}')

    return action(value)


def apply_clause_to_assertion_with_areas(clause: 'SingleClause', value: Sequence[AreaPointer]) -> AppliedClauseResult:
    action = area_actions.get(clause.key, None)

    if action is None:
        raise Exception(f'got {clause.key}; expected one of {sorted(area_actions.keys())}')

    return action(value)


def apply_clause_to_assertion_with_data(clause: 'SingleClause', value: Sequence[Any]) -> AppliedClauseResult:
    action = other_actions.get(clause.key, None)

    if action is None:
        raise Exception(f'got {clause.key}; expected one of {sorted(other_actions.keys())}')

    return action(value)


###


def avg_or_0(items: Sequence[Decimal]) -> Decimal:
    if not items:
        return Decimal('0.00')

    return sum(items) / Decimal(len(items))
