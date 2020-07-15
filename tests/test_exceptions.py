from dp.data.student import Student
from dp.data.course import course_from_str
from dp.area import AreaOfStudy
from dp.constants import Constants
from dp.result.course import CourseResult
from dp.exception import load_exception
import logging

c = Constants(matriculation_year=2000)


def test_insertion_on_course_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ["$", "*DEPT 345"],
        "clbid": "1",
    })

    course_a = course_from_str("OTHER 123", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    transcript = [course_a, course_b]

    area = AreaOfStudy.load(specification={"result": {"course": "DEPT 345"}}, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is True
    assert result.claims()[0].course.clbid == course_b.clbid


def test_multi_insertion_on_course_rule(caplog):
    """We expect the first insertion to take hold"""
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ["$", "*DEPT 345"],
        "clbid": "1",
    })
    exception2 = load_exception({
        "type": "insert",
        "path": ["$", "*DEPT 345"],
        "clbid": "2",
    })

    course_a = course_from_str("OTHER 123", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    course_c = course_from_str("OTHER 235", clbid="2")
    transcript = [course_a, course_b, course_c]

    area = AreaOfStudy.load(specification={"result": {"course": "DEPT 345"}}, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2]))
    assert len(solutions) == 2

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is True
    assert result.claims()[0].course.clbid == course_b.clbid
    assert len(result.claims()) == 1


def test_insertion_on_query_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ["$", ".query"],
        "clbid": "0",
    })

    course_a = course_from_str("OTHER 123", clbid="0")
    transcript = [course_a]

    area = AreaOfStudy.load(specification={
        "result": {
            "from": "courses",
            "where": {"subject": {"$eq": "ABC"}},
            "assert": {"count(courses)": {"$gte": 1}},
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is False
    assert result.claims()[0].course.clbid == course_a.clbid


def test_multi_insertion_on_query_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ["$", ".query"],
        "clbid": "0",
    })
    exception2 = load_exception({
        "type": "insert",
        "path": ["$", ".query"],
        "clbid": "1",
    })

    course_a = course_from_str("OTHER 123", clbid="0")
    course_b = course_from_str("OTHER 111", clbid="1")
    transcript = [course_a, course_b]

    area = AreaOfStudy.load(specification={
        "result": {
            "from": "courses",
            "where": {"subject": {"$eq": "ABC"}},
            "assert": {"count(courses)": {"$gte": 1}},
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2]))
    assert len(solutions) == 3

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is False
    assert result.claims()[0].course.clbid == course_a.clbid
    assert len(result.claims()) == 1


def test_insertion_on_count_rule__any(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.count'],
        "clbid": "1",
    })

    course_a = course_from_str("OTHER 345", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    transcript = [course_a, course_b]

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
            ],
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    print([s.solution for s in solutions])

    assert [
        [x.course for x in s.solution.items if isinstance(x, CourseResult)]
        for s in solutions
    ] == [['OTHER 234']]
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.count == 1
    assert result.ok() is True
    assert result.waived() is False
    assert result.claims()[0].course.clbid == course_b.clbid


def test_multi_insertion_on_count_rule__any(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.count'],
        "clbid": "1",
    })
    exception2 = load_exception({
        "type": "insert",
        "path": ['$', '.count'],
        "clbid": "2",
    })

    course_a = course_from_str("OTHER 345", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    course_c = course_from_str("OTHER 222", clbid="2")
    transcript = [course_a, course_b, course_c]

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
            ],
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2]))
    print([s.solution for s in solutions])

    assert [
        [x.course for x in s.solution.items if isinstance(x, CourseResult)]
        for s in solutions
    ] == [['OTHER 234', 'OTHER 222']]
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.count == 1
    assert result.ok() is True
    assert result.waived() is False
    assert result.claims()[0].course.clbid == course_b.clbid
    assert result.claims()[1].course.clbid == course_c.clbid


def test_multi_insertion_on_count_rule__any_with_natural(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.count'],
        "clbid": "1",
    })
    exception2 = load_exception({
        "type": "insert",
        "path": ['$', '.count'],
        "clbid": "2",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("OTHER 234", clbid="1")
    course_c = course_from_str("OTHER 222", clbid="2")
    transcript = [course_a, course_b, course_c]

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
            ],
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2]))
    print([s.solution for s in solutions])

    assert [
        [x.course for x in s.solution.items if isinstance(x, CourseResult)]
        for s in solutions
    ] == [['DEPT 123', 'OTHER 234', 'OTHER 222']]
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.count == 1
    assert result.ok() is True
    assert result.waived() is False
    assert result.claims()[0].course.clbid == course_a.clbid
    assert result.claims()[1].course.clbid == course_b.clbid
    assert result.claims()[2].course.clbid == course_c.clbid


def test_insertion_on_count_rule__all(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.count'],
        "clbid": "2",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 234", clbid="1")
    course_c = course_from_str("DEPT 345", clbid="2")
    transcript = [course_a, course_b, course_c]

    area = AreaOfStudy.load(specification={
        "result": {
            "all": [
                {"course": "DEPT 123"},
                {"course": "DEPT 234"},
            ],
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.count == 3
    assert result.ok() is True
    assert result.waived() is False


def test_insertion_on_requirement_rule(caplog):
    '''the long and short of this test is, attempting to insert a course
    directly into a Requirement directly should do nothing.'''

    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ["$", r"%req"],
        "clbid": "2",
    })

    print('start')

    area = AreaOfStudy.load(specification={
        "result": {"requirement": "req"},
        "requirements": {
            "req": {"result": {"course": "DEPT 123"}},
        },
    }, c=c, student=Student.load({}), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load({}), exceptions=[exception]))
    assert len(solutions) == 1

    print('begin audit')

    result = solutions[0].audit()

    print(result)

    assert result.ok() is False
    assert result.waived() is False


def test_override_on_course_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "override",
        "path": ["$", "*DEPT 123"],
        "status": "pass",
    })

    area = AreaOfStudy.load(specification={"result": {"course": "DEPT 123"}}, c=c, student=Student.load({}), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load({}), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is True


def test_override_on_query_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "override",
        "path": ["$", ".query"],
        "status": "pass",
    })

    area = AreaOfStudy.load(specification={
        "result": {
            "from": "courses",
            "assert": {"count(courses)": {"$gte": 1}},
        },
    }, c=c, student=Student.load({}), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load({}), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is True


def test_override_on_count_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "override",
        "path": ["$", ".count"],
        "status": "pass",
    })

    area = AreaOfStudy.load(specification={
        "result": {
            "any": [
                {"course": "DEPT 123"},
            ],
        },
    }, c=c, student=Student.load({}), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load({}), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is True


def test_override_on_requirement_rule(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "override",
        "path": ["$", r"%req"],
        "status": "pass",
    })

    area = AreaOfStudy.load(specification={
        "result": {"requirement": "req"},
        "requirements": {
            "req": {"department_audited": True},
        },
    }, c=c, student=Student.load({}), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load({}), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is True


def test_override_on_count_rule_assertion_clause(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "override",
        "path": ['$', '.count', '.audit', '[0]', '.assert'],
        "status": "pass",
    })

    course_a = course_from_str("DEPT 234", clbid="0")
    course_b = course_from_str("DEPT 345", clbid="1")
    transcript = [course_a, course_b]

    area = AreaOfStudy.load(specification={
        "result": {
            "all": [{"course": "DEPT 123"}],
            "audit": {"assert": {"count(courses)": {"$gte": 1}}},
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.audits()[0].waived() is True
    assert result.ok() is False
    assert result.waived() is False


def test_insertion_on_count_rule_assertion_clause(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.count', '.audit', '[0]', '.assert'],
        "clbid": "1",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 345", clbid="1")
    transcript = [course_a, course_b]

    area = AreaOfStudy.load(specification={
        "result": {
            "all": [{"course": "DEPT 123"}],
            "audit": {"assert": {"count(courses)": {"$gte": 1}}},
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is False
    assert result.result.audits()[0].waived() is False
    assert set(result.result.audits()[0].assertion.resolved_items) == set(['1', '0'])

    assert result.claims()[0].course.clbid == course_a.clbid
    assert len(result.claims()) == 1


def test_multi_insertion_on_count_rule_assertion_clause(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.count', '.audit', '[0]', '.assert'],
        "clbid": "1",
    })
    exception2 = load_exception({
        "type": "insert",
        "path": ['$', '.count', '.audit', '[0]', '.assert'],
        "clbid": "2",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 345", clbid="1")
    course_c = course_from_str("DEPT 234", clbid="2")
    transcript = [course_a, course_b, course_c]

    area = AreaOfStudy.load(specification={
        "result": {
            "all": [{"course": "DEPT 123"}],
            "audit": {"assert": {"count(courses)": {"$gte": 1}}},
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.ok() is True
    assert result.waived() is False
    assert result.result.audits()[0].waived() is False
    assert set(result.result.audits()[0].assertion.resolved_items) == set(['1', '0', '2'])

    assert result.claims()[0].course.clbid == course_a.clbid
    assert len(result.claims()) == 1


def test_override_on_query_rule_audit_clause(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "override",
        "path": ['$', '.query', '.assertions', '[0]', '.assert'],
        "status": "pass",
    })

    area = AreaOfStudy.load(specification={
        "result": {
            "from": "courses",
            "all": [{"assert": {"count(courses)": {"$gte": 1}}}],
        },
    }, c=c, exceptions=[exception])
    solutions = list(area.solutions(student=Student.load({}), exceptions=[exception]))
    assert len(solutions) == 1

    result = solutions[0].audit()

    assert result.result.resolved_assertions[0].waived() is True
    assert result.ok() is True
    assert result.waived() is False


def test_insertion_on_query_rule_audit_clause(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.query', '.assertions', '[0]', '.assert'],
        "clbid": "1",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 345", clbid="1")
    transcript = [course_a, course_b]

    area = AreaOfStudy.load(specification={
        "result": {
            "from": "courses",
            "all": [{"assert": {"count(courses)": {"$gte": 1}}}],
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception]))
    assert len(solutions) == 3

    result = solutions[0].audit()

    assert result.result.resolved_assertions[0].waived() is False

    assert result.ok() is True
    assert result.waived() is False

    assert result.result.resolved_assertions[0].waived() is False
    assert set(result.result.resolved_assertions[0].assertion.resolved_items) == set(['1', '0'])

    assert result.claims()[0].course.clbid == course_a.clbid
    assert len(result.claims()) == 1


def test_multi_insertion_on_query_rule_audit_clause(caplog):
    caplog.set_level(logging.DEBUG)

    exception = load_exception({
        "type": "insert",
        "path": ['$', '.query', '.assertions', '[0]', '.assert'],
        "clbid": "1",
    })
    exception2 = load_exception({
        "type": "insert",
        "path": ['$', '.query', '.assertions', '[0]', '.assert'],
        "clbid": "2",
    })

    course_a = course_from_str("DEPT 123", clbid="0")
    course_b = course_from_str("DEPT 345", clbid="1")
    course_c = course_from_str("DEPT 234", clbid="2")
    transcript = [course_a, course_b, course_c]

    area = AreaOfStudy.load(specification={
        "result": {
            "from": "courses",
            "all": [{"assert": {"count(courses)": {"$gte": 1}}}],
        },
    }, c=c, student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2])
    solutions = list(area.solutions(student=Student.load(dict(courses=transcript)), exceptions=[exception, exception2]))
    assert len(solutions) == 7

    result = solutions[0].audit()

    assert result.result.resolved_assertions[0].waived() is False

    assert result.ok() is True
    assert result.waived() is False

    assert result.result.resolved_assertions[0].waived() is False
    assert set(result.result.resolved_assertions[0].assertion.resolved_items) == set(['1', '0', '2'])

    assert result.claims()[0].course.clbid == course_a.clbid
    assert len(result.claims()) == 1
