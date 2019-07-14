from degreepath import *
from degreepath.requirement import Requirement
from degreepath.save import SaveRule
from degreepath.rule.given import FromRule, FromInput
import pytest
import io
import logging


def c(s):
    return CourseSolution(course=s)


def x_test_save():
    rule = SaveRule(
        innards=FromRule(
            source=FromInput(
                mode="student", itemtype="courses", requirements=[], saves=[]
            ),
            action=None,
            limit=None,
            where=AndClause(
                children=[
                    SingleClause(
                        key="attributes", expected="elective", operator=Operator.EqualTo
                    )
                ]
            ),
            store="courses",
        ),
        name="Taken Electives",
    )

    courses = [
        CourseInstance.from_dict(course="ABCD 101", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 102", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 103", attributes=["elective"]),
    ]

    ctx = RequirementContext(transcript=courses, saves={}, child_requirements={})

    solutions = list(rule.solutions(path=["$root"], ctx=ctx))

    assert solutions == [
        FromSolution(
            output=[
                CourseInstance(
                    data={
                        "course": "ABCD 101",
                        "subject": ["ABCD"],
                        "number": 101,
                        "level": 100,
                        "attributes": ["elective"],
                    }
                ),
                CourseInstance(
                    data={
                        "course": "ABCD 102",
                        "subject": ["ABCD"],
                        "number": 102,
                        "level": 100,
                        "attributes": ["elective"],
                    }
                ),
                CourseInstance(
                    data={
                        "course": "ABCD 103",
                        "subject": ["ABCD"],
                        "number": 103,
                        "level": 100,
                        "attributes": ["elective"],
                    }
                ),
            ],
            action=None,
        )
    ]


def x_test_saves(caplog):
    caplog.set_level(logging.DEBUG)

    # test_data = io.StringIO(
    #     r"""
    #         saves:
    #             Taken Electives:
    #                 from: {student: courses}
    #                 where: {attributes: {$eq: elective}}
    #                 store: courses
    #
    #         result:
    #             all:
    #                 - from: {save: Taken Electives}
    #                   assert: {count(courses): {$gte: 7}}
    #
    #                 - from: {save: Taken Electives}
    #                   where: {level: {$eq: 300}}
    #                   assert: {count(courses): {$gte: 1}}
    # """
    # )
    #
    # loaded = yaml.load(test_data, Loader=yaml.SafeLoader)

    req = Requirement(
        name="XYZ",
        saves={
            "Taken Electives": SaveRule(
                innards=FromRule(
                    source=FromInput(
                        mode="student", itemtype="courses", requirements=[], saves=[]
                    ),
                    action=None,
                    limit=None,
                    where=AndClause(
                        children=[
                            SingleClause(
                                key="attributes",
                                expected="elective",
                                operator=Operator.EqualTo,
                            )
                        ]
                    ),
                    store="courses",
                ),
                name="Taken Electives",
            )
        },
        result=Rule(
            rule=CountRule(
                count=2,
                of=[
                    Rule(
                        rule=FromRule(
                            source=FromInput(
                                mode="saves",
                                itemtype=None,
                                requirements=[],
                                saves=["Taken Electives"],
                            ),
                            action=FromAssertion(
                                command="count",
                                source="courses",
                                operator=Operator.GreaterThanOrEqualTo,
                                compare_to=7,
                            ),
                            limit=None,
                            where=None,
                            store=None,
                        )
                    ),
                    Rule(
                        rule=FromRule(
                            source=FromInput(
                                mode="saves",
                                itemtype=None,
                                requirements=[],
                                saves=["Taken Electives"],
                            ),
                            action=FromAssertion(
                                command="count",
                                source="courses",
                                operator=Operator.GreaterThanOrEqualTo,
                                compare_to=1,
                            ),
                            limit=None,
                            store=None,
                            where=AndClause(
                                children=[
                                    SingleClause(
                                        key="level",
                                        expected=300,
                                        operator=Operator.EqualTo,
                                    )
                                ]
                            ),
                        )
                    ),
                ],
            )
        ),
        requirements={},
    )

    courses = [
        CourseInstance.from_dict(course="ABCD 101", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 102", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 103", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 331", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 332", attributes=["elective"]),
        CourseInstance.from_dict(course="ABCD 333", attributes=["elective"]),
    ]

    ctx = RequirementContext(transcript=courses, saves={}, child_requirements={})

    solutions = list(req.solutions(path=["$root"], ctx=ctx))

    expected = [
        RequirementSolution(solution=CountSolution(items=[
            FromSolution(
                output=[],
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=7,
                ),
            ),
            FromSolution(
                output=(
                    CourseInstance(data={"course": "ABCD 331", "subject": ["ABCD"], "number": 331, "level": 300, "attributes": ["elective"]}),
                ),
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=1,
                ),
            ),
        ])),
        RequirementSolution(solution=CountSolution(items=[
            FromSolution(
                output=[],
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=7,
                ),
            ),
            FromSolution(
                output=(
                    CourseInstance(data={"course": "ABCD 332", "subject": ["ABCD"], "number": 332, "level": 300, "attributes": ["elective"]}),
                ),
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=1,
                ),
            ),
        ])),
        RequirementSolution(solution=CountSolution(items=[
            FromSolution(
                output=[],
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=7,
                ),
            ),
            FromSolution(
                output=(
                    CourseInstance(data={"course": "ABCD 333", "subject": ["ABCD"], "number": 333, "level": 300, "attributes": ["elective"]}),
                ),
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=1,
                ),
            ),
        ])),
        RequirementSolution(solution=CountSolution(items=[
            FromSolution(
                output=[],
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=7,
                ),
            ),
            FromSolution(
                output=(
                    CourseInstance(data={"course": "ABCD 331", "subject": ["ABCD"], "number": 331, "level": 300, "attributes": ["elective"]}),
                    CourseInstance(data={"course": "ABCD 332", "subject": ["ABCD"], "number": 332, "level": 300, "attributes": ["elective"]}),
                ),
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=1,
                ),
            ),
        ])),
        RequirementSolution(solution=CountSolution(items=[
            FromSolution(
                output=[],
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=7,
                ),
            ),
            FromSolution(
                output=(
                    CourseInstance(data={"course": "ABCD 331", "subject": ["ABCD"], "number": 331, "level": 300, "attributes": ["elective"]}),
                    CourseInstance(data={"course": "ABCD 333", "subject": ["ABCD"], "number": 333, "level": 300, "attributes": ["elective"]}),
                ),
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=1,
                ),
            ),
        ])),
        RequirementSolution(solution=CountSolution(items=[
            FromSolution(
                output=[],
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=7,
                ),
            ),
            FromSolution(
                output=(
                    CourseInstance(data={"course": "ABCD 332", "subject": ["ABCD"], "number": 332, "level": 300, "attributes": ["elective"]}),
                    CourseInstance(data={"course": "ABCD 333", "subject": ["ABCD"], "number": 333, "level": 300, "attributes": ["elective"]}),
                ),
                action=FromAssertion(
                    command="count",
                    source="courses",
                    operator=Operator.GreaterThanOrEqualTo,
                    compare_to=1,
                ),
            ),
        ])),
    ]

    assert expected == solutions
