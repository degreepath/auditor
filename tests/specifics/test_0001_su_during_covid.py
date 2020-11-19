from dp.data.course import course_from_str, apply_single_clause__grade, GradeOption
from dp.constants import Constants
from dp.load_clause import load_clause
from dp.clause import SingleClause

c = Constants(matriculation_year=2000)


def test_graded_during_non_covid() -> None:
    clause = load_clause({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c)
    assert isinstance(clause, SingleClause)

    course = course_from_str(
        'CSCI 251',
        grade_code='C',
        grade_option=GradeOption.Grade,
        year=2019,
        term='1',
    )
    assert apply_single_clause__grade(course, clause) is True


def test_graded_during_covid() -> None:
    clause = load_clause({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c)
    assert isinstance(clause, SingleClause)

    course = course_from_str(
        'CSCI 251',
        grade_code='C',
        grade_option=GradeOption.Grade,
        year=2019,
        term='3',
    )
    assert apply_single_clause__grade(course, clause) is True


def test_su_during_non_covid() -> None:
    clause = load_clause({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c)
    assert isinstance(clause, SingleClause)

    course = course_from_str(
        'CSCI 251',
        grade_code='S',
        grade_option=GradeOption.SU,
        su_grade_code='C',
        year=2019,
        term='1',
    )
    assert apply_single_clause__grade(course, clause) is False


def test_su_during_covid() -> None:
    clause = load_clause({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c)
    assert isinstance(clause, SingleClause)

    course = course_from_str(
        'CSCI 251',
        grade_code='S',
        grade_option=GradeOption.SU,
        su_grade_code='C',
        year=2019,
        term='3',
    )
    assert apply_single_clause__grade(course, clause) is True


def test_failed_su_during_covid() -> None:
    clause = load_clause({"grade": {"$gte": "C", "$during_covid": "C-"}}, c=c)
    assert isinstance(clause, SingleClause)

    course = course_from_str(
        'CSCI 251',
        grade_code='U',
        grade_option=GradeOption.SU,
        su_grade_code='D',
        year=2019,
        term='3',
    )
    assert apply_single_clause__grade(course, clause) is False


def test_su_during_covid_different_clause() -> None:
    clause = load_clause({"grade": {"$gte": "B"}}, c=c)
    assert isinstance(clause, SingleClause)

    course = course_from_str(
        'CSCI 251',
        grade_code='S',
        grade_option=GradeOption.SU,
        su_grade_code='C',
        year=2019,
        term='3',
    )
    assert apply_single_clause__grade(course, clause) is False
