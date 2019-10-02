from degreepath.data import course_from_str
import degreepath.apply_clause as funcs


def test_count_subjects__one_course():
    c = course_from_str("ECON 123")

    result = funcs.count_subjects([c])

    assert result.value == 1
    assert result.data == ('ECON',)
    assert len(result.courses) == 1


def test_count_subjects__chbi():
    result = funcs.count_subjects([
        course_from_str("CH/BI 125"),
        course_from_str("CH/BI 126"),
        course_from_str("CH/BI 227"),
    ])

    assert result.value == 2
    assert result.data == ('BIO', 'CHEM')
    assert len(result.courses) == 2


def test_count_subjects__several_courses_same_dept():
    result = funcs.count_subjects([
        course_from_str("ECON 123"),
        course_from_str("ECON 124"),
        course_from_str("ECON 125"),
    ])

    assert result.value == 1
    assert result.data == ('ECON',)
    assert len(result.courses) == 1


def test_count_subjects__several_courses():
    result = funcs.count_subjects([
        course_from_str("ECON 123"),
        course_from_str("CSCI 124"),
        course_from_str("ASIAN 125"),
    ])

    assert result.value == 3
    assert result.data == ('ASIAN', 'CSCI', 'ECON')
    assert len(result.courses) == 3
