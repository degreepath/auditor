from decimal import Decimal
from .data.course_enums import Grade, CourseStatus


def filter_transcript(courses):
    return (c for c in courses if c.status != CourseStatus.Incomplete)


def grade_point_average_items(courses):
    return [c for c in courses if c.in_gpa]


def grade_point_average(courses):
    allowed = grade_point_average_items(courses)

    if not allowed:
        return Decimal('0.00')

    return round(sum(c.grade_points for c in allowed) / len(allowed), 2)


def grade_to_grade_points(g: Grade) -> Decimal:
    grades = {
        Grade.Aplus: Decimal("4.30"),
        Grade.A: Decimal("4.00"),
        Grade.Aminus: Decimal("3.70"),
        Grade.Bplus: Decimal("3.30"),
        Grade.B: Decimal("3.00"),
        Grade.Bminus: Decimal("2.70"),
        Grade.Cplus: Decimal("2.30"),
        Grade.C: Decimal("2.00"),
        Grade.Cminus: Decimal("1.70"),
        Grade.Dplus: Decimal("1.30"),
        Grade.D: Decimal("1.00"),
        Grade.Dminus: Decimal("0.70"),
        Grade.F: Decimal("0.00"),
    }

    return grades.get(g, Decimal("0.00"))


def str_to_grade_points(s: str) -> Decimal:
    return grade_to_grade_points(Grade(s))
