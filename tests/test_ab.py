from degreepath.solution.count import CountSolution
from degreepath.solution.course import CourseSolution
from degreepath.rule.course import CourseRule
from degreepath.solution.requirement import RequirementSolution
from degreepath.area import AreaOfStudy
from degreepath.data import course_from_str
import pytest
import io
import yaml


def c(s):
    return CourseSolution(course=s, rule=CourseRule(course=s, hidden=False, grade=None, allow_claimed=False))


def x_test_sample():
    test_data = io.StringIO("""
        result:
          all:
            - requirement: A
            - requirement: B
            - requirement: C

        requirements:
          A:
            result:
              any:
                - course: CSCI 111
                - course: CSCI 112
          B:
            result:
              both:
                - course: CSCI 111
                - course: CSCI 113
          C:
            result:
              count: 2
              of:
                - course: CSCI 111
                - course: CSCI 112
                - course: CSCI 113
                - course: CSCI 114
                - course: CSCI 115
    """)

    area = AreaOfStudy.load(yaml.load(stream=test_data, Loader=yaml.SafeLoader))
    area.validate()

    transcript = [
        course_from_str(c)
        for c in ["CSCI 111", "CSCI 112", "CSCI 113", "CSCI 114", "CSCI 115"]
    ]

    output = list(area.solutions(transcript=transcript))

    expected = [
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 112")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 114")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 112"), c("CSCI 113")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 112"), c("CSCI 114")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 112"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 113"), c("CSCI 114")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 113"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 111")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 114"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 112")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 114")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 112"), c("CSCI 113")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 112"), c("CSCI 114")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 112"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 113"), c("CSCI 114")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 113"), c("CSCI 115")], count=2))], count=3),
        CountSolution(items=[RequirementSolution(solution=CountSolution(items=[c("CSCI 112")], count=1)), RequirementSolution(solution=CountSolution(items=[c("CSCI 111"), c("CSCI 113")], count=2)), RequirementSolution(solution=CountSolution(items=[c("CSCI 114"), c("CSCI 115")], count=2))], count=3),
    ]

    assert expected == output
