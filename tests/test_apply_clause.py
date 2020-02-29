from .course_from_str import course_from_str
from decimal import Decimal
import dp.apply_clause as funcs


def test_count_courses__all_different():
    result = funcs.count_courses([
        course_from_str("ECON 123", clbid='1'),
        course_from_str("CSCI 124", clbid='2'),
        course_from_str("ASIAN 125", clbid='3'),
    ])

    assert result.value == 3
    assert result.data == ('1', '2', '3')
    assert len(result.courses) == 3


def test_count_courses__all_same():
    result = funcs.count_courses([
        course_from_str("ECON 123", clbid='1'),
        course_from_str("ECON 123", clbid='1'),
        course_from_str("ECON 123", clbid='1'),
    ])

    assert result.value == 1
    assert result.data == tuple(['1'])
    assert len(result.courses) == 1


def test_count_terms_from_most_common_course():
    result = funcs.count_terms_from_most_common_course([
        course_from_str("MUSIC 111", crsid='1', year='2007', term='1'),
        course_from_str("ECON 123", clbid='b', crsid='2', year='2009', term='1'),
        course_from_str("ECON 123", clbid='c', crsid='2', year='2009', term='3'),
    ])

    assert result.value == 2
    assert result.data == ('20091', '20093')
    assert len(result.courses) == 2


def test_count_terms_from_most_common_course__empty():
    result = funcs.count_terms_from_most_common_course([])

    assert result.value == 0
    assert result.data == ()
    assert len(result.courses) == 0


def test_count_terms_from_most_common_course__two_sections_same_term():
    result = funcs.count_terms_from_most_common_course([
        course_from_str("ECON 123", section='A', clbid='123', crsid='1', year='2009', term='3'),
        course_from_str("ECON 123", section='B', clbid='124', crsid='1', year='2009', term='3'),
    ])

    assert result.value == 1
    assert result.data == ('20093',)
    assert len(result.courses) == 2


def test_count_subjects__one_course():
    result = funcs.count_subjects([
        course_from_str("ECON 123"),
    ])

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


def test_count_terms():
    result = funcs.count_terms([
        course_from_str("MUSIC 111", crsid='1', year='2007', term='1'),
        course_from_str("ECON 123", clbid='b', crsid='2', year='2009', term='1'),
        course_from_str("ECON 123", clbid='c', crsid='2', year='2009', term='3'),
        course_from_str("ECON 124", clbid='d', crsid='3', year='2009', term='3'),
    ])

    assert result.value == 3
    assert result.data == ('20071', '20091', '20093')
    assert len(result.courses) == 3


def test_count_years():
    result = funcs.count_years([
        course_from_str("MUSIC 111", crsid='1', year='2007', term='1'),
        course_from_str("ECON 123", clbid='b', crsid='2', year='2009', term='1'),
        course_from_str("ECON 123", clbid='c', crsid='2', year='2009', term='3'),
        course_from_str("ECON 124", clbid='d', crsid='3', year='2009', term='3'),
    ])

    assert result.value == 2
    assert result.data == ('2007', '2009')
    assert len(result.courses) == 2


def test_count_math_perspectives():
    result = funcs.count_math_perspectives([
        course_from_str("MUSIC 111", attributes=('math_perspective_a',)),
        course_from_str("ECON 123", attributes=('math_perspective_a',)),
        course_from_str("ECON 125", attributes=('math_perspective_c',)),
    ])

    assert result.value == 2
    assert result.data == ('math_perspective_a', 'math_perspective_c')
    assert len(result.courses) == 3


def test_count_religion_traditions():
    result = funcs.count_religion_traditions([
        course_from_str("REL 111", attributes=('rel_tradition_a',)),
        course_from_str("REL 123", attributes=('rel_tradition_a',)),
        course_from_str("REL 125", attributes=('rel_tradition_c',)),
    ])

    assert result.value == 2
    assert result.data == ('rel_tradition_a', 'rel_tradition_c')
    assert len(result.courses) == 3


def test_sum_credits():
    result = funcs.sum_credits([
        course_from_str("MUSIC 111", credits=1),
        course_from_str("ECON 123", credits=1),
        course_from_str("ECON 125", credits=1),
    ])

    assert result.value == 3
    assert result.data == (1, 1, 1)
    assert len(result.courses) == 3


def test_sum_credits__fractional():
    result = funcs.sum_credits([
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("ECON 123", credits=Decimal('0.5')),
        course_from_str("ECON 125", credits=Decimal('1')),
    ])

    assert result.value == Decimal('2.00')
    assert result.data == (Decimal('0.25'), Decimal('0.25'), Decimal('0.5'), Decimal('1'))
    assert len(result.courses) == 4


def test_sum_credits__large():
    result = funcs.sum_credits([
        course_from_str("MUSIC 111", credits=Decimal('1')),
        course_from_str("MUSIC 111", credits=Decimal('2')),
    ])

    assert result.value == Decimal('3')
    assert result.data == (Decimal('1'), Decimal('2'))
    assert len(result.courses) == 2


def test_sum_credits__ignores_zeroes():
    result = funcs.sum_credits([
        course_from_str("MUSIC 111", credits=0),
        course_from_str("ECON 123", credits=1),
        course_from_str("ECON 125", credits=1),
    ])

    assert result.value == 2
    assert result.data == (1, 1)
    # this is where we assert that we ignore 0-credit courses.
    # if we didn't ignore them, this would report 3 courses.
    assert len(result.courses) == 2


def test_sum_credits__sorts_output():
    result = funcs.sum_credits([
        course_from_str("MUSIC 111", credits=3),
        course_from_str("MUSIC 111", credits=2),
        course_from_str("MUSIC 111", credits=1),
    ])

    assert result.value == 6
    # we assert that the output data does not match the input data, but is instead sorted
    assert result.data == (1, 2, 3)
    assert sorted(result.data) == sorted([1, 2, 3])
    assert len(result.courses) == 3


def test_sum_credits_from_single_subject__empty():
    result = funcs.sum_credits_from_single_subject([])

    assert result.value == Decimal('0')
    assert result.data == tuple([Decimal('0')])
    assert len(result.courses) == 0


def test_sum_credits_from_single_subject__partial():
    result = funcs.sum_credits_from_single_subject([
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
    ])

    assert result.value == Decimal('0.5')
    assert result.data == tuple([Decimal('0.25'), Decimal('0.25')])
    assert len(result.courses) == 2


def test_sum_credits_from_single_subject__full():
    result = funcs.sum_credits_from_single_subject([
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
    ])

    assert result.value == Decimal('1.0')
    assert result.data == tuple([Decimal('0.25'), Decimal('0.25'), Decimal('0.25'), Decimal('0.25')])
    assert len(result.courses) == 4


def test_sum_credits_from_single_subject__mixed():
    result = funcs.sum_credits_from_single_subject([
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("ART 101", credits=Decimal('1')),
    ])

    assert result.value == Decimal('1.0')
    assert result.data == tuple([Decimal('1')])
    assert len(result.courses) == 1


def test_sum_credits_from_single_subject__multiple_solutions():
    result = funcs.sum_credits_from_single_subject([
        course_from_str("A 100", credits=Decimal('1')),
        course_from_str("B 200", credits=Decimal('1')),
    ])

    assert result.value == Decimal('1.0')
    assert result.data == tuple([Decimal('1')])
    assert len(result.courses) == 1
    result_a = list(result.courses)[0]

    result = funcs.sum_credits_from_single_subject([
        course_from_str("B 200", credits=Decimal('1')),
        course_from_str("A 100", credits=Decimal('1')),
    ])

    assert len(result.courses) == 1
    result_b = list(result.courses)[0]

    # We're asserting that no matter how the input is sorted, when
    # two subjects both have the most credits, the "higher" subject
    # in the alphabet is chosen.
    assert result_a.subject == result_b.subject == 'B'


def test_average_grades__same():
    result = funcs.average_grades([
        course_from_str("A 100", grade_points=Decimal('4.0'), grade_points_gpa=Decimal('4.0')),
        course_from_str("B 200", grade_points=Decimal('4.0'), grade_points_gpa=Decimal('4.0')),
    ])

    assert result.value == Decimal('4.0')
    assert result.data == (Decimal('4.0'), Decimal('4.0'))
    assert len(result.courses) == 2


def test_average_grades__mixed():
    result = funcs.average_grades([
        course_from_str("A 100", grade_points=Decimal('2.0'), grade_points_gpa=Decimal('2.0')),
        course_from_str("B 200", grade_points=Decimal('4.0'), grade_points_gpa=Decimal('4.0')),
    ])

    assert result.value == Decimal('3.0')
    assert result.data == (Decimal('2.0'), Decimal('4.0'))
    assert len(result.courses) == 2


def test_average_grades__all_zeroes():
    result = funcs.average_grades([
        course_from_str("A 100", grade_points=Decimal('0.0'), grade_points_gpa=Decimal('0.0')),
        course_from_str("B 200", grade_points=Decimal('0.0'), grade_points_gpa=Decimal('0.0')),
    ])

    assert result.value == Decimal('0.0')
    assert result.data == (Decimal('0.0'), Decimal('0.0'))
    assert len(result.courses) == 2


def test_average_credits():
    result = funcs.average_credits([
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("MUSIC 111", credits=Decimal('0.25')),
        course_from_str("ART 101", credits=Decimal('1')),
    ])

    assert result.value == Decimal('0.4375')
    assert result.data == (Decimal('0.25'), Decimal('0.25'), Decimal('0.25'), Decimal('1'))
    assert len(result.courses) == 4


def x_test_count_areas():
    result = funcs.count_areas([
    ])

    assert result.value == 0
    assert result.data == frozenset()
    assert len(result.courses) == 0


def x_test_count_items_test():
    result = funcs.count_items_test([
    ])

    assert result.value == 0
    assert result.data == frozenset()
    assert len(result.courses) == 0


def x_test_count_performances():
    result = funcs.count_performances([
    ])

    assert result.value == 0
    assert result.data == ()
    assert len(result.courses) == 0


def x_test_count_seminars():
    result = funcs.count_seminars([
    ])

    assert result.value == 0
    assert result.data == ()
    assert len(result.courses) == 0
