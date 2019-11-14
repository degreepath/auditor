from decimal import Decimal, ROUND_DOWN
from typing import Iterable, TYPE_CHECKING
from .data.course_enums import GradeCode, grade_code_to_points

if TYPE_CHECKING:  # pragma: no cover
    from .data import CourseInstance  # noqa: F401


def grade_point_average_items(courses: Iterable['CourseInstance']) -> Iterable['CourseInstance']:
    return (c for c in courses if c.is_in_gpa)


def grade_point_average(courses: Iterable['CourseInstance']) -> Decimal:
    allowed = list(grade_point_average_items(courses))

    summed = sum(c.grade_points_gpa for c in allowed)
    credits = sum(c.credits for c in allowed)

    if credits == 0:
        return Decimal('0.00')

    gpa = summed / credits

    # GPA is _truncated_ to two decimal places, not rounded
    return Decimal(gpa).quantize(Decimal('1.00'), rounding=ROUND_DOWN)


def str_to_grade_points(s: str) -> Decimal:
    return grade_code_to_points.get(GradeCode(s), Decimal("0.00"))
