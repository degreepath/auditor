from degreepath import *
import pytest
import io


def test_clauses(caplog):
    caplog.set_level(logging.DEBUG)

    x = SingleClause.load({"attributes": {"$eq": "csci_elective"}})
    expected_single = SingleClause(
        key="attributes", expected="csci_elective", operator=Operator.EqualTo
    )
    assert x == AndClause(children=[expected_single])

    c = CourseInstance.from_dict(course="CSCI 121", attributes=["csci_elective"])

    assert c is not None

    result = c.apply_clause(x)

    assert result is True
