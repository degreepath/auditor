from decimal import Decimal
from typing import Sequence
from .data.course_enums import GradeCode


def filter_transcript(courses: Sequence):
    return (c for c in courses if not c.is_in_progress)


def grade_point_average_items(courses: Sequence):
    return (c for c in courses if c.is_in_gpa)


def grade_point_average(courses):
    allowed = list(grade_point_average_items(courses))

    if not allowed:
        return Decimal('0.00')

    summed = sum(c.grade_points_gpa for c in allowed)
    credits = sum(c.credits for c in allowed)
    gpa = summed / credits

    # GPA is _truncated_ to two decimal places, not rounded
    return int(gpa * 100) / 100


def grade_to_grade_points(g: GradeCode) -> Decimal:
    grades = {
        GradeCode.Aplus: Decimal("4.00"),
        GradeCode.A: Decimal("4.00"),
        GradeCode.Aminus: Decimal("3.70"),
        GradeCode.Bplus: Decimal("3.30"),
        GradeCode.B: Decimal("3.00"),
        GradeCode.Bminus: Decimal("2.70"),
        GradeCode.Cplus: Decimal("2.30"),
        GradeCode.C: Decimal("2.00"),
        GradeCode.Cminus: Decimal("1.70"),
        GradeCode.Dplus: Decimal("1.30"),
        GradeCode.D: Decimal("1.00"),
        GradeCode.Dminus: Decimal("0.70"),
        GradeCode.F: Decimal("0.00"),
    }

    return grades.get(g, Decimal("0.00"))


def str_to_grade_points(s: str) -> Decimal:
    return grade_to_grade_points(GradeCode(s))
