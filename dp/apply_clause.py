from typing import Any, Sequence, Iterable, Tuple, Set, Dict, Mapping, Callable, Collection, Union, TYPE_CHECKING
from collections import Counter, defaultdict
from decimal import Decimal

import attr

from .data.course import CourseInstance
from .data.area_pointer import AreaPointer
from .data.music import MusicPerformance, MusicAttendance
from .lib import grade_point_average_items, grade_point_average

if TYPE_CHECKING:  # pragma: no cover
    from .clause import SingleClause


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AppliedClauseResult:
    value: Union[int, Decimal]
    data: Union[Tuple[str, ...], Tuple[Decimal, ...]] = tuple()
    courses: Collection[CourseInstance] = tuple()


def count_items_test(data: Iterable[Any]) -> AppliedClauseResult:
    items = frozenset(repr(c) for c in data)

    return AppliedClauseResult(value=len(items), data=tuple(items))


def count_courses(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    items = frozenset(c for c in data)
    clbids = tuple(c.clbid for c in items)

    return AppliedClauseResult(value=len(items), data=clbids, courses=items)


def count_distinct_courses(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        if c.crsid not in items:
            items.add(c.crsid)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(items), courses=courses)


def count_terms_from_most_common_course(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    counted = Counter(c.crsid for c in data)

    if not counted:
        return AppliedClauseResult(value=0)

    most_common = counted.most_common(1)[0]
    most_common_crsid, _count = most_common

    courses = tuple(c for c in data if c.crsid == most_common_crsid)
    items = tuple(set(c.yearterm for c in courses))

    return AppliedClauseResult(value=len(items), data=items, courses=courses)


def count_terms_from_most_common_course_by_name(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    counted = Counter(f"{c.subject}: {c.name}" for c in data)

    if not counted:
        return AppliedClauseResult(value=0)

    most_common = counted.most_common(1)[0]
    most_common_ident, _count = most_common

    courses = tuple(c for c in data if f"{c.subject}: {c.name}" == most_common_ident)
    items = tuple(set(c.yearterm for c in courses))

    return AppliedClauseResult(value=len(items), data=items, courses=courses)


def count_subjects(data: Iterable[CourseInstance]) -> AppliedClauseResult:
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

    return AppliedClauseResult(value=len(items), data=tuple(items), courses=courses)


def count_terms(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        yearterm = c.yearterm
        if yearterm not in items:
            items.add(yearterm)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(items), courses=courses)


def count_math_perspectives(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    perspectives: Set[str] = set()
    courses = set()

    for c in data:
        for bucket in c.attributes:
            if bucket.startswith('math_perspective_'):
                perspectives.add(bucket)
                courses.add(c)

    return AppliedClauseResult(value=len(perspectives), data=tuple(perspectives), courses=courses)


def count_religion_traditions(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    traditions: Set[str] = set()
    courses = set()

    for c in data:
        for bucket in c.attributes:
            if bucket.startswith('rel_tradition_'):
                traditions.add(bucket)
                courses.add(c)

    return AppliedClauseResult(value=len(traditions), data=tuple(traditions), courses=courses)


def count_intlr_regions(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    regions: Set[str] = set()
    courses = set()

    for c in data:
        for bucket in c.attributes:
            if bucket.startswith('intlr_region_'):
                regions.add(bucket)
                courses.add(c)

    return AppliedClauseResult(value=len(regions), data=tuple(regions), courses=courses)


def count_years(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    items: Set[str] = set()
    courses = set()

    for c in data:
        str_year = str(c.year)
        if str_year not in items:
            items.add(str_year)
            courses.add(c)

    return AppliedClauseResult(value=len(items), data=tuple(items), courses=courses)


def count_areas(data: Iterable[AreaPointer]) -> AppliedClauseResult:
    area_codes = tuple(set(a.code for a in data))
    return AppliedClauseResult(value=len(area_codes), data=area_codes)


def count_recitals(data: Iterable[MusicAttendance]) -> AppliedClauseResult:
    uniques = tuple(set(a.id for a in data))
    return AppliedClauseResult(value=len(uniques), data=uniques)


def count_performances(data: Iterable[MusicPerformance]) -> AppliedClauseResult:
    uniques = tuple(set(a.id for a in data))
    return AppliedClauseResult(value=len(uniques), data=uniques)


def count_seminars(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    # TODO
    raise TypeError('count(seminars) is not yet implemented')


def sum_credits(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    data = [c for c in data if c.credits != 0]
    items = tuple(c.credits for c in data)
    courses = tuple(data)

    return AppliedClauseResult(value=sum(items), data=items, courses=courses)


def sum_credits_from_single_subject(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    data = [c for c in data if c.credits != 0]

    if not data:
        return AppliedClauseResult(value=0, data=tuple([Decimal(0)]))

    # This should sort the subjects by the number of credits under that
    # subject code, then pick the one with the most credits as the
    # "single_subject"

    by_credits: Dict[str, Decimal] = defaultdict(Decimal)

    for c in data:
        by_credits[c.subject] += c.credits

    _credits, best_subject = max((credits, subject) for subject, credits in by_credits.items())

    courses = tuple(c for c in data if best_subject == c.subject)
    items = tuple(c.credits for c in courses)

    return AppliedClauseResult(value=sum(items), data=items, courses=courses)


def average_grades(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    avg = grade_point_average(data)
    courses = tuple(grade_point_average_items(data))
    items = tuple(c.gpa_points for c in courses)

    return AppliedClauseResult(value=avg, data=items, courses=courses)


def average_credits(data: Iterable[CourseInstance]) -> AppliedClauseResult:
    items = tuple(c.credits for c in data if c.credits != 0)
    courses = tuple(c for c in data if c.credits != 0)
    avg = avg_or_0(items)

    return AppliedClauseResult(value=avg, data=items, courses=courses)


###


course_actions: Mapping[str, Callable[[Iterable[CourseInstance]], AppliedClauseResult]] = {
    'count(courses)': count_courses,
    'count(distinct_courses)': count_distinct_courses,
    'count(terms_from_most_common_course)': count_terms_from_most_common_course,
    'count(terms_from_most_common_course_by_name)': count_terms_from_most_common_course_by_name,
    'count(math_perspectives)': count_math_perspectives,
    'count(religion_traditions)': count_religion_traditions,
    'count(intlr_regions)': count_intlr_regions,
    'count(subjects)': count_subjects,
    'count(terms)': count_terms,
    'count(years)': count_years,

    'sum(credits)': sum_credits,
    'sum(credits_from_single_subject)': sum_credits_from_single_subject,

    'average(grades)': average_grades,
    'average(credits)': average_credits,
}

area_actions: Mapping[str, Callable[[Iterable[AreaPointer]], AppliedClauseResult]] = {
    'count(areas)': count_areas,
}

other_actions: Mapping[str, Callable[[Iterable[Any]], AppliedClauseResult]] = {
    'count(items)': count_items_test,
    'count(performances)': count_performances,
    'count(seminars)': count_seminars,
    'count(recitals)': count_recitals,
}


def apply_clause_to_assertion_with_courses(clause: 'SingleClause', value: Iterable[CourseInstance]) -> AppliedClauseResult:
    action = course_actions.get(clause.key, None)
    assert action is not None, KeyError(f'got {clause.key}; expected one of {sorted(course_actions.keys())}')
    return action(value)


def apply_clause_to_assertion_with_areas(clause: 'SingleClause', value: Iterable[AreaPointer]) -> AppliedClauseResult:
    action = area_actions.get(clause.key, None)
    assert action is not None, KeyError(f'got {clause.key}; expected one of {sorted(area_actions.keys())}')
    return action(value)


def apply_clause_to_assertion_with_data(clause: 'SingleClause', value: Iterable[Any]) -> AppliedClauseResult:
    action = other_actions.get(clause.key, None)
    assert action is not None, KeyError(f'got {clause.key}; expected one of {sorted(other_actions.keys())}')
    return action(value)


###


def avg_or_0(items: Sequence[Decimal]) -> Decimal:
    if not items:
        return Decimal('0.00')

    return sum(items) / Decimal(len(items))
