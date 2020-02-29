from typing import Any

from dp.load_course import load_course
from dp.data.course import CourseInstance
from dp.data.course_enums import GradeOption, SubType
from dp.grades import str_to_grade_points


def course_from_str(s: str, **kwargs: Any) -> CourseInstance:
    number = s.split(' ')[1]

    grade_code = kwargs.get('grade_code', 'B')
    grade_points = kwargs.get('grade_points', str_to_grade_points(grade_code))
    grade_points_gpa = kwargs.get('grade_points_gpa', grade_points)

    return load_course({
        "attributes": tuple(),
        "clbid": f"<clbid={str(hash(s))} term={str(kwargs.get('term', 'na'))}>",
        "course": s,
        "course_type": "SE",
        "credits": '1.00',
        "crsid": f"<crsid={str(hash(s))}>",
        "flag_gpa": True,
        "flag_in_progress": False,
        "flag_incomplete": False,
        "flag_repeat": False,
        "flag_stolaf": True,
        "gereqs": tuple(),
        "grade_option": GradeOption.Grade,
        "institution_short": "STOLAF",
        "level": int(number) // 100 * 100,
        "name": s,
        "number": s.split(' ')[1],
        "section": "",
        "sub_type": SubType.Normal,
        "subject": s.split(' ')[0],
        "term": "1",
        "transcript_code": "",
        "year": 2000,
        **kwargs,
        "grade_code": grade_code,
        "grade_points": grade_points,
        "grade_points_gpa": grade_points_gpa,
    }, overrides=[], credits_overrides={})
