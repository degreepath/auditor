from typing import Optional, Dict, Sequence, Any, cast
from decimal import Decimal, ROUND_DOWN
import logging

from .data.course import CourseInstance
from .data.course_enums import GradeOption, SubType, CourseType, TranscriptCode
from .exception import CourseOverrideException, ExceptionAction, CourseCreditOverride, CourseSubjectOverride
from .grades import GradeCode


logger = logging.getLogger(__name__)


def load_course(  # noqa: C901
    data: Dict[str, Any],
    *,
    current_term: Optional[str] = None,
    overrides: Sequence[CourseOverrideException] = tuple(),
    credits_overrides: Optional[Dict[str, str]] = None,
) -> CourseInstance:  # noqa: C901
    if not credits_overrides:
        credits_overrides = {}

    if isinstance(data, CourseInstance):
        return data  # type: ignore

    attributes = data.get('attributes', tuple())
    clbid = data['clbid']
    course_type = data['course_type']
    credits = data['credits']
    crsid = data['crsid']
    flag_gpa = data['flag_gpa']
    flag_incomplete = data['flag_incomplete']
    flag_in_progress = data['flag_in_progress']
    flag_repeat = data['flag_repeat']
    flag_stolaf = data['flag_stolaf']
    gereqs = data['gereqs']
    grade_code = data['grade_code']
    grade_option = data['grade_option']
    grade_points = data['grade_points']
    institution = data['institution_short']
    level = data['level']
    name = data['name']
    number = data['number']
    section = data['section']
    sub_type = data['sub_type']
    subject = data['subject']
    term = data['term']
    transcript_code = data['transcript_code']
    year = data['year']

    applicable_overrides = {o.type: o for o in overrides if o.clbid == clbid}
    subject_override = applicable_overrides.get(ExceptionAction.CourseSubject, None)
    credits_override = applicable_overrides.get(ExceptionAction.CourseCredits, None)

    # find a default credits override, if one exists in the area spec
    credits_override_key = f"name={name}"
    if not credits_override and credits_override_key in credits_overrides:
        amount = Decimal(credits_overrides[credits_override_key])
        credits_override = CourseCreditOverride(path=tuple(), clbid=clbid, type=ExceptionAction.CourseCredits, credits=amount)

    if credits_override:
        credits = cast(CourseCreditOverride, credits_override).credits

    if subject_override:
        subject = cast(CourseSubjectOverride, subject_override).subject

    term = int(term)
    credits = Decimal(credits)
    section = section or None
    level = int(level)

    grade_code = GradeCode(grade_code)
    grade_points = Decimal(grade_points)
    grade_option = GradeOption(grade_option)
    sub_type = SubType(sub_type)
    course_type = CourseType(course_type)
    transcript_code = TranscriptCode(transcript_code)

    in_progress_this_term = False
    in_progress_in_future = False

    if current_term and grade_code in (GradeCode._IP, GradeCode._I):
        if f"{year}{term}" <= current_term:
            in_progress_this_term = True
        elif f"{year}{term}" > current_term:
            in_progress_in_future = True

    # GPA points are the (truncated to two decimal places!) result of GP * credits.
    # If someone gets an A- in a 0.25-credit course, they are supposed to
    # receive 0.92 gpa points, because `0.25 * 3.7 => 0.925` but we truncate
    # everything to do with GPA at 2 decimal places.
    gpa_points = Decimal(grade_points * credits).quantize(Decimal('1.00'), rounding=ROUND_DOWN)

    attributes = tuple(attributes) if attributes else tuple()
    gereqs = tuple(gereqs) if gereqs else tuple()

    if sub_type is SubType.Lab:
        suffix = ".L"
    elif sub_type is SubType.Flac:
        suffix = ".F"
    elif sub_type is SubType.Discussion:
        suffix = ".D"
    else:
        suffix = ""

    course_identity = f"{subject} {number}{suffix}"
    is_chbi = None
    if course_identity == 'CH/BI 125':
        is_chbi = 125
    elif course_identity == 'CH/BI 126':
        is_chbi = 126
    elif course_identity == 'CH/BI 127':
        is_chbi = 127
    elif course_identity == 'CH/BI 227':
        is_chbi = 227

    yearterm = f"{year}{term}"

    return CourseInstance(
        attributes=attributes,
        clbid=clbid,
        credits=credits,
        crsid=crsid,
        course_type=course_type,
        gereqs=gereqs,
        gpa_points=gpa_points,
        grade_code=grade_code,
        grade_option=grade_option,
        grade_points=grade_points,
        institution=institution,
        is_in_gpa=flag_gpa,
        is_in_progress=flag_in_progress,
        is_in_progress_this_term=in_progress_this_term,
        is_in_progress_in_future=in_progress_in_future,
        is_incomplete=flag_incomplete,
        is_repeat=flag_repeat,
        is_stolaf=flag_stolaf,
        is_lab=sub_type is SubType.Lab,
        level=level,
        name=name,
        number=number,
        section=section,
        sub_type=sub_type,
        subject=subject,
        term=term,
        transcript_code=transcript_code,
        year=year,
        identity_=course_identity,
        is_chbi_=is_chbi,
        yearterm=yearterm,
    )
