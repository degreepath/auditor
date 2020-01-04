from dp.area import AreaOfStudy
from dp.data import course_from_str, Student
from dp.constants import Constants
import pytest
import io
import yaml
import logging

c = Constants(matriculation_year=2000)


def test_from(caplog):
    caplog.set_level(logging.DEBUG)

    test_data = io.StringIO("""
        result:
            from: courses
            where: {gereqs: {$eq: SPM}}
            assert: {count(courses): {$gte: 1}}
    """)

    area = AreaOfStudy.load(specification=yaml.load(stream=test_data, Loader=yaml.SafeLoader), c=c)

    transcript = [
        course_from_str("CSCI 111", gereqs=['SPM'], term=20081),
        course_from_str("ASIAN 110"),
    ]

    s = next(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[]))
    a = s.audit().result

    assert len(a.successful_claims) == 1

    assert a.successful_claims[0].claim.course.clbid == transcript[0].clbid


def __get_data(spec):
    area = AreaOfStudy.load(specification=yaml.load(stream=io.StringIO(spec), Loader=yaml.SafeLoader), c=c)

    transcript = [
        course_from_str("CSCI 113", gereqs=['SPM'], term=20071),
        course_from_str("CSCI 112", gereqs=['SPM'], term=20081),
        course_from_str("CSCI 111", gereqs=['SPM'], term=20091),
    ]

    return (area, transcript)


def test_solution_count_exact(caplog):
    caplog.set_level(logging.DEBUG, logger='dp.rule.given.rule')

    area, transcript = __get_data("""
        result:
            from: courses
            where: {gereqs: {$eq: SPM}}
            assert: {count(courses): {$eq: 1}}
    """)

    solutions = area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[])

    sol = next(solutions)
    assert len(sol.solution.output) == 1

    sol = next(solutions)
    assert len(sol.solution.output) == 1

    sol = next(solutions)
    assert len(sol.solution.output) == 1

    with pytest.raises(StopIteration):
        next(solutions)


def test_solution_count_lessthan(caplog):
    caplog.set_level(logging.DEBUG, logger='dp.rule.given.rule')

    with pytest.raises(AssertionError):
        area, transcript = __get_data("""
            result:
                requirement: Test

            requirements:
                Test:
                    result:
                        from: courses
                        where: {gereqs: {$eq: SPM}}
                        assert: {count(courses): {$lt: 3}}
        """)


def test_solution_count_greaterthan_1(caplog):
    caplog.set_level(logging.DEBUG, logger='dp.rule.given.rule')
    area, transcript = __get_data("""
        result:
            from: courses
            where: {gereqs: {$eq: SPM}}
            assert: {count(courses): {$gt: 1}}
    """)

    solutions = area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[])

    sol = next(solutions)
    assert len(sol.solution.output) == 2

    sol = next(solutions)
    assert len(sol.solution.output) == 2

    sol = next(solutions)
    assert len(sol.solution.output) == 2

    sol = next(solutions)
    assert len(sol.solution.output) == 3

    with pytest.raises(StopIteration):
        next(solutions)


def test_solution_count_always_yield_something(caplog):
    caplog.set_level(logging.DEBUG, logger='dp.rule.given.rule')
    area, transcript = __get_data("""
        result:
            from: courses
            where: {gereqs: {$eq: FOOBAR}}
            assert: {count(courses): {$gt: 1}}
    """)

    solutions = area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[])

    sol = next(solutions)
    assert len(sol.solution.output) == 0

    with pytest.raises(StopIteration):
        next(solutions)
