from decimal import Decimal, ROUND_DOWN
from typing import Iterable, TYPE_CHECKING
from .data.course_enums import GradeCode, grade_code_to_points

if TYPE_CHECKING:  # pragma: no cover
    from .data.course import CourseInstance  # noqa: F401


def grade_point_average_items(courses: Iterable['CourseInstance']) -> Iterable['CourseInstance']:
    return (c for c in courses if c.is_in_gpa)


def grade_point_average(courses: Iterable['CourseInstance']) -> Decimal:
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
