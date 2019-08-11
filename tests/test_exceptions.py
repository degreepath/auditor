from degreepath.data import course_from_str
from degreepath.area import AreaOfStudy
from degreepath.constants import Constants
from degreepath.base import Solution
from degreepath.exception import load_exception
import logging

c = Constants(matriculation_year=2000)


def test_insertion_on_course_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={"result": {"course": "DEPT 345"}}, c=c)

    exception = load_exception({
        "action": "insert",
        "path": ["$", "*DEPT 345"],
        "clbid": "1",
    })

    course_a = course_from_str("OTHER 123", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    transcript = [course_a, course_b]

    solutions = list(area.solutions(transcript=transcript, areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=transcript, areas=[], exceptions=[exception])

    assert result.ok() is True
    assert result.was_overridden() is False
    assert result.claims()[0].claim.clbid == course_b.clbid


def test_insertion_on_query_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {
            "from": {"student": "courses"},
            "where": {"subject": {"$eq": "ABC"}},
            "assert": {"count(courses)": {"$gte": 1}},
        },
    }, c=c)

    exception = load_exception({
        "action": "insert",
        "path": ["$", ".query"],
        "clbid": "0",
    })

    course_a = course_from_str("OTHER 123", clbid="0")
    transcript = [course_a]

    solutions = list(area.solutions(transcript=transcript, areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=transcript, areas=[], exceptions=[exception])

    assert result.ok() is True
    assert result.was_overridden() is False
    assert result.claims()[0].claim.clbid == course_a.clbid


def test_insertion_on_count_rule__any(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
            ],
        },
    }, c=c)

    exception = load_exception({
        "action": "insert",
        "path": ['$', '.count'],
        "clbid": "1",
    })

    course_a = course_from_str("OTHER 345", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    transcript = [course_a, course_b]

    solutions = list(area.solutions(transcript=transcript, areas=[], exceptions=[exception]))
    # for s in solutions:
    #     print(s.solution.items)

    assert [
        [x.course for x in s.solution.items if isinstance(x, Solution)]
        for s in solutions
    ] == [['OTHER 234'], ['DEPT 123'], ['OTHER 234', 'DEPT 123']]
    assert len(solutions) == 3

    result = solutions[0].audit(transcript=transcript, areas=[], exceptions=[exception])

    assert result.count == 1
    assert result.ok() is True
    assert result.was_overridden() is False
    assert result.claims()[0].claim.clbid == course_b.clbid


def test_insertion_on_count_rule__all(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {
            "all": [
                {"course": "DEPT 123"},
                {"course": "DEPT 234"},
            ],
        },
    }, c=c)

    exception = load_exception({
        "action": "insert",
        "path": ['$', '.count'],
        "clbid": "2",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 234", clbid="1")
    course_c = course_from_str("DEPT 345", clbid="2")
    transcript = [course_a, course_b, course_c]

    solutions = list(area.solutions(transcript=transcript, areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=transcript, areas=[], exceptions=[exception])

    assert result.count == 3
    assert result.ok() is True
    assert result.was_overridden() is False


def test_insertion_on_count_rule_assertion_clause(): ...


def test_insertion_on_requirement_rule(): ...


def test_override_on_course_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={"result": {"course": "DEPT 123"}}, c=c)

    exception = load_exception({
        "action": "override",
        "path": ["$", "*DEPT 123"],
        "status": "pass",
    })

    solutions = list(area.solutions(transcript=[], areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=[], areas=[], exceptions=[exception])

    assert result.ok() is True
    assert result.was_overridden() is True


def test_override_on_query_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {
            "from": {"student": "courses"},
            "assert": {"count(courses)": {"$gte": 1}},
        },
    }, c=c)

    exception = load_exception({
        "action": "override",
        "path": ["$", ".query"],
        "status": "pass",
    })

    solutions = list(area.solutions(transcript=[], areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=[], areas=[], exceptions=[exception])

    assert result.ok() is True
    assert result.was_overridden() is True


def test_override_on_count_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
            ],
        },
    }, c=c)

    exception = load_exception({
        "action": "override",
        "path": ["$", ".count"],
        "status": "pass",
    })

    solutions = list(area.solutions(transcript=[], areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=[], areas=[], exceptions=[exception])

    assert result.ok() is True
    assert result.was_overridden() is True


def test_override_on_count_rule_assertion_clause(): ...


def test_override_on_requirement_rule(caplog):
    caplog.set_level(logging.DEBUG)

    area = AreaOfStudy.load(specification={
        "result": {"requirement": "req"},
        "requirements": {
            "req": {"department_audited": True},
        },
    }, c=c)

    exception = load_exception({
        "action": "override",
        "path": ["$", r"%req"],
        "status": "pass",
    })

    solutions = list(area.solutions(transcript=[], areas=[], exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit(transcript=[], areas=[], exceptions=[exception])

    assert result.ok() is True
    assert result.was_overridden() is True
