from dp.data.course_enums import GradeCode


def test_grade_ordering():
    assert GradeCode.B >= GradeCode.C
    assert GradeCode.B > GradeCode.C
