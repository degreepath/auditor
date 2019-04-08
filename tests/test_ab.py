from degreepath import *
import pytest
import io


def c(s):
    return CourseSolution(course=s)


def test_sample():
    test_data = io.StringIO(
        """
        name: foo
        catalog: 2018-19
        type: major
        degree: Bachelor of Arts

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
    """
    )

    area = load(test_data)
    area.validate()

    transcript = [
        CourseInstance.from_s(c)
        for c in ["CSCI 111", "CSCI 112", "CSCI 113", "CSCI 114", "CSCI 115"]
    ]

    output = list(area.solutions(transcript=transcript))

    expected = [
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 112")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 114")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 112"), c("CSCI 113")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 112"), c("CSCI 114")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 112"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 113"), c("CSCI 114")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 113"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 111")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 114"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 112")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 114")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 112"), c("CSCI 113")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 112"), c("CSCI 114")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 112"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 113"), c("CSCI 114")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 113"), c("CSCI 115")]),
            ]
        ),
        CountSolution(
            items=[
                CountSolution(items=[c("CSCI 112")]),
                CountSolution(items=[c("CSCI 111"), c("CSCI 113")]),
                CountSolution(items=[c("CSCI 114"), c("CSCI 115")]),
            ]
        ),
    ]

    assert output == expected
