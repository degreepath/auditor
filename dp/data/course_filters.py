from typing import Dict, Callable, TYPE_CHECKING

from ..clause import SingleClause

from .course_enums import GradeOption, CourseType

if TYPE_CHECKING:  # pragma: no cover
    from .course import CourseInstance


def apply_single_clause__attributes(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.attributes)


def apply_single_clause__gereqs(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.gereqs)


def apply_single_clause__ap(course: 'CourseInstance', clause: SingleClause) -> bool:
    return course.course_type is CourseType.AP and clause.compare(course.name)


def apply_single_clause__number(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.number)


def apply_single_clause__institution(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.institution)


def apply_single_clause__course(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.identity_)


def apply_single_clause__subject(course: 'CourseInstance', clause: SingleClause) -> bool:
    # CH/BI 125 and 126 are "CHEM" courses, while 127/227 are "BIO".
    # So we pretend that that is the case, but only when checking subject codes.
    if course.is_chbi_ is not None:
        if course.is_chbi_ in (125, 126):
            return clause.compare('CHEM')
        else:
            return clause.compare('BIO')
    else:
        return clause.compare(course.subject)


def apply_single_clause__grade(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.grade_points)


def apply_single_clause__grade_code(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.grade_code.value)


def apply_single_clause__credits(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.credits)


def apply_single_clause__level(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.level)


def apply_single_clause__semester(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.term)


def apply_single_clause__su(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.grade_option is GradeOption.SU)


def apply_single_clause__pn(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.grade_option is GradeOption.PN)


def apply_single_clause__type(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.sub_type.name)


def apply_single_clause__course_type(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.course_type.name)


def apply_single_clause__lab(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.is_lab)


def apply_single_clause__grade_option(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.grade_option)


def apply_single_clause__is_stolaf(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.is_stolaf)


def apply_single_clause__is_in_gpa(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.is_in_gpa)


def apply_single_clause__is_in_progress(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.is_in_progress)


def apply_single_clause__year(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.year)


def apply_single_clause__clbid(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.clbid)


def apply_single_clause__crsid(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.crsid)


def apply_single_clause__name(course: 'CourseInstance', clause: SingleClause) -> bool:
    return clause.compare(course.name)


clause_application_lookup: Dict[str, Callable[['CourseInstance', SingleClause], bool]] = {
    'ap': apply_single_clause__ap,
    'attributes': apply_single_clause__attributes,
    'clbid': apply_single_clause__clbid,
    'course': apply_single_clause__course,
    'course_type': apply_single_clause__course_type,
    'credits': apply_single_clause__credits,
    'crsid': apply_single_clause__crsid,
    'gereqs': apply_single_clause__gereqs,
    'grade': apply_single_clause__grade,
    'grade_code': apply_single_clause__grade_code,
    'grade_option': apply_single_clause__grade_option,
    'institution': apply_single_clause__institution,
    'is_in_gpa': apply_single_clause__is_in_gpa,
    'is_in_progress': apply_single_clause__is_in_progress,
    'is_stolaf': apply_single_clause__is_stolaf,
    'lab': apply_single_clause__lab,
    'level': apply_single_clause__level,
    'name': apply_single_clause__name,
    'number': apply_single_clause__number,
    'p/n': apply_single_clause__pn,
    's/u': apply_single_clause__su,
    'semester': apply_single_clause__semester,
    'subject': apply_single_clause__subject,
    'type': apply_single_clause__type,
    'year': apply_single_clause__year,
}
