from degreepath import *
import pytest
import io
import yaml


def c(s):
    return CourseSolution(course=s)


def x_test_no_courses_in_from():
    test_data = io.StringIO(
        r"""
        name: Computer Science
        type: major
        degree: Bachelor of Arts
        catalog: 2018-19

        result:
          all:
            - requirement: Foundation
            - requirement: Core
            - requirement: Electives
            - requirement: Capstone

        attributes:
          courses:
            CSCI 273: [csci_elective]
            CSCI 276: [csci_elective]
            CSCI 284: [csci_elective]
            CSCI 300: [csci_elective]
            CSCI 315: [csci_elective]
            CSCI 316: [csci_elective]
            CSCI 333: [csci_elective]
            CSCI 336: [csci_elective]
            CSCI 350: [csci_elective]
            ID 259 2000.1: [csci_elective]

        requirements:
          Foundation:
            result:
              count: all
              of:
                - either:
                    - course: CSCI 121
                    - course: CSCI 125
                - course: CSCI 241
                - both:
                    - course: CSCI 251
                    - course: CSCI 252
                - count: 1
                  of:
                    - course: MATH 232
                    - course: MATH 252
                    - course: MATH 244

          Core:
            result:
              all:
                - course: CSCI 253
                - course: CSCI 263
                - requirement: Languages
                - requirement: Systems

            requirements:
              Languages:
                result:
                  any:
                    - course: CSCI 276
                    - course: CSCI 333
                    - course: CSCI 336

              Systems:
                result:
                  any:
                    - course: CSCI 273
                    - course: CSCI 284
                    - {course: CSCI 300, year: 2000, semester: Fall}

          Electives:
            result:
              from: {student: courses}
              where: {attributes: {$eq: csci_elective}}
              assert: {count(courses): {$gte: 2}}

          Capstone:
            result:
              course: CSCI 390
    """
    )

    area = AreaOfStudy.load(yaml.load(stream=test_data, Loader=yaml.SafeLoader))
    area.validate()

    transcript = [
        CourseInstance.from_s(c)
        for c in ["CSCI 111", "CSCI 112", "CSCI 113", "CSCI 114", "CSCI 115"]
    ]

    output = sum(1 for _ in area.solutions(transcript=transcript))

    expected = 54

    assert output == expected


def x_test_five_courses_in_from():
    test_data = io.StringIO(
        r"""
        name: Computer Science
        type: major
        degree: Bachelor of Arts
        catalog: 2018-19

        result:
          all:
            - requirement: Foundation
            - requirement: Core
            - requirement: Electives
            - requirement: Capstone

        attributes:
          courses:
            CSCI 273: [csci_elective]
            CSCI 276: [csci_elective]
            CSCI 284: [csci_elective]
            CSCI 300: [csci_elective]
            CSCI 315: [csci_elective]
            CSCI 316: [csci_elective]
            CSCI 333: [csci_elective]
            CSCI 336: [csci_elective]
            CSCI 350: [csci_elective]
            ID 259 2000.1: [csci_elective]

        requirements:
          Foundation:
            result:
              count: all
              of:
                - either:
                    - course: CSCI 121
                    - course: CSCI 125
                - course: CSCI 241
                - both:
                    - course: CSCI 251
                    - course: CSCI 252
                - count: 1
                  of:
                    - course: MATH 232
                    - course: MATH 252
                    - course: MATH 244

          Core:
            result:
              all:
                - course: CSCI 253
                - course: CSCI 263
                - requirement: Languages
                - requirement: Systems

            requirements:
              Languages:
                result:
                  any:
                    - course: CSCI 276
                    - course: CSCI 333
                    - course: CSCI 336

              Systems:
                result:
                  any:
                    - course: CSCI 273
                    - course: CSCI 284
                    - {course: CSCI 300, year: 2000, semester: Fall}

          Electives:
            result:
              from: {student: courses}
              where: {attributes: {$eq: csci_elective}}
              assert: {count(courses): {$gte: 2}}

          Capstone:
            result:
              course: CSCI 390
    """
    )

    area = AreaOfStudy.load(yaml.load(stream=test_data, Loader=yaml.SafeLoader))
    area.validate()

    transcript = [
        CourseInstance.from_dict(course=c, attributes=["csci_elective"])
        for c in ["CSCI 111", "CSCI 112", "CSCI 113", "CSCI 114", "CSCI 115"]
    ]

    output = sum(1 for _ in area.solutions(transcript=transcript))

    expected = 1350

    assert output == expected
