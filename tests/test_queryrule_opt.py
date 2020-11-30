from dp.data.course import course_from_str
from dp.rule.query import iterate_item_set, QueryRule
from dp.constants import Constants
from dp.context import RequirementContext
from decimal import Decimal


c = Constants(matriculation_year=2000)


def test_count_courses_optimization():
    ctx = RequirementContext()

    courses = [
        course_from_str('A 101'),
        course_from_str('B 101'),
        course_from_str('C 101'),
    ]

    rule = QueryRule.load(path=[], c=c, ctx=ctx, data={
        'from': 'courses',
        'assert': {'count(courses)': {'$gte': 2}},
    })

    results = list(iterate_item_set(courses, rule=rule))

    assert results == [
        tuple([courses[0], courses[1]]),
        tuple([courses[0], courses[2]]),
        tuple([courses[1], courses[2]]),
        tuple([courses[0], courses[1], courses[2]]),
    ]


def test_count_credits_optimizations():
    ctx = RequirementContext()

    courses = [
        course_from_str('A 101', credits=Decimal('0.5')),
        course_from_str('B 101', credits=Decimal('0.5')),
        course_from_str('C 101', credits=Decimal('0.5')),
    ]

    rule = QueryRule.load(path=[], c=c, ctx=ctx, data={
        'from': 'courses',
        'assert': {'sum(credits)': {'$gte': 1}},
    })

    results = list(iterate_item_set(courses, rule=rule))

    assert results == [
        tuple([courses[0], courses[1]]),
        tuple([courses[0], courses[2]]),
        tuple([courses[1], courses[2]]),
        tuple([courses[0], courses[1], courses[2]]),
    ]


def test_count_credits_optimizations_2():
    ctx = RequirementContext()

    courses = [
        course_from_str('A 101', credits=Decimal('1')),
        course_from_str('B 101', credits=Decimal('1')),
        course_from_str('C 101', credits=Decimal('1')),
    ]

    rule = QueryRule.load(path=[], c=c, ctx=ctx, data={
        'from': 'courses',
        'assert': {'sum(credits)': {'$gte': 1}},
    })

    results = list(iterate_item_set(courses, rule=rule))

    assert results == [
        tuple([courses[0]]),
        tuple([courses[1]]),
        tuple([courses[2]]),
        tuple([courses[0], courses[1]]),
        tuple([courses[0], courses[2]]),
        tuple([courses[1], courses[2]]),
        tuple([courses[0], courses[1], courses[2]]),
    ]
