from typing import Iterable, Dict
from decimal import Decimal, ROUND_DOWN

from .data.course_enums import GradeCode
from .data.course import CourseInstance


grade_code_to_points: Dict[GradeCode, Decimal] = {
    GradeCode.A_plus: Decimal("4.00"),
    GradeCode.A: Decimal("4.00"),
    GradeCode.A_minus: Decimal("3.70"),
    GradeCode.B_plus: Decimal("3.30"),
    GradeCode.B: Decimal("3.00"),
    GradeCode.B_minus: Decimal("2.70"),
    GradeCode.C_plus: Decimal("2.30"),
    GradeCode.C: Decimal("2.00"),
    GradeCode.C_minus: Decimal("1.70"),
    GradeCode.D_plus: Decimal("1.30"),
    GradeCode.D: Decimal("1.00"),
    GradeCode.D_minus: Decimal("0.70"),
    GradeCode.F: Decimal("0.00"),
}


def grade_point_average_items(courses: Iterable[CourseInstance]) -> Iterable[CourseInstance]:
    return (c for c in courses if c.is_in_gpa)


def grade_point_average(courses: Iterable[CourseInstance]) -> Decimal:
    gp_sum = Decimal('0')
    credit_sum = Decimal('0')

    for c in grade_point_average_items(courses):
        gp_sum += c.gpa_points
        credit_sum += c.credits

    if credit_sum == 0:
        return Decimal('0.00')

    gpa = gp_sum / credit_sum

    # GPA is _truncated_ to two decimal places, not rounded
    return Decimal(gpa).quantize(Decimal('1.00'), rounding=ROUND_DOWN)


def str_to_grade_points(s: str) -> Decimal:
    return grade_code_to_points.get(GradeCode(s), Decimal("0.00"))
