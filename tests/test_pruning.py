from dp.data.student import Student
from dp.data.course import course_from_str
from dp.area import AreaOfStudy
from dp.constants import Constants
from dp.result.course import CourseResult
import logging

c = Constants(matriculation_year=2000)


def test_pruning_on_count_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
                {"course": "DEPT 234"},
                {"course": "DEPT 345"},
            ],
        },
    }, c=c)

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 234", clbid="1")
    transcript = [course_a, course_b]

    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[]))

    assert [
        [x.course for x in s.solution.items if isinstance(x, CourseResult)]
        for s in solutions
    ] == [['DEPT 123', 'DEPT 234']]
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.count == 1
    assert result.ok() is True
    assert result.waived() is False
    assert result.claims()[0].course.clbid == course_a.clbid
