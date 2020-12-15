from dp.context import RequirementContext
from dp.data.course import course_from_str, apply_predicate__grade, GradeOption
from dp.constants import Constants
from dp.data_type import DataType
from dp.predicate_clause import load_predicate
from dp.predicate_clause import Predicate

c = Constants(matriculation_year=2000)
mode = DataType.Course


def test_graded_during_non_covid() -> None:
    ctx = RequirementContext()
    clause = load_predicate({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c, mode=mode, ctx=ctx)
    assert isinstance(clause, Predicate)

    course = course_from_str(
        'CSCI 251',
        grade_code='C',
        grade_option=GradeOption.Grade,
        year=2019,
        term='1',
    )
    assert apply_predicate__grade(course, clause) is True


def test_graded_during_covid() -> None:
    ctx = RequirementContext()
    clause = load_predicate({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c, mode=mode, ctx=ctx)
    assert isinstance(clause, Predicate)

    course = course_from_str(
        'CSCI 251',
        grade_code='C',
        grade_option=GradeOption.Grade,
        year=2019,
        term='3',
    )
    assert apply_predicate__grade(course, clause) is True


def test_su_during_non_covid() -> None:
    ctx = RequirementContext()
    clause = load_predicate({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c, mode=mode, ctx=ctx)
    assert isinstance(clause, Predicate)

    course = course_from_str(
        'CSCI 251',
        grade_code='S',
        grade_option=GradeOption.SU,
        su_grade_code='C',
        year=2019,
        term='1',
    )
    assert apply_predicate__grade(course, clause) is False


def test_su_during_covid() -> None:
    ctx = RequirementContext()
    clause = load_predicate({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c, mode=mode, ctx=ctx)
    assert isinstance(clause, Predicate)

    course = course_from_str(
        'CSCI 251',
        grade_code='S',
        grade_option=GradeOption.SU,
        su_grade_code='C',
        year=2019,
        term='3',
    )
    assert apply_predicate__grade(course, clause) is True


def test_failed_su_during_covid() -> None:
    ctx = RequirementContext()
    clause = load_predicate({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c, mode=mode, ctx=ctx)
    assert isinstance(clause, Predicate)

    course = course_from_str(
        'CSCI 251',
        grade_code='U',
        grade_option=GradeOption.SU,
        su_grade_code='D',
        year=2019,
        term='3',
    )
    assert apply_predicate__grade(course, clause) is False


def test_su_during_covid_different_clause() -> None:
    ctx = RequirementContext()
    clause = load_predicate({"grade": {"$gte": "B"}}, c=c, mode=mode, ctx=ctx)
    assert isinstance(clause, Predicate)

    course = course_from_str(
        'CSCI 251',
        grade_code='S',
        grade_option=GradeOption.SU,
        su_grade_code='C',
        year=2019,
        term='3',
    )
    assert apply_predicate__grade(course, clause) is False
