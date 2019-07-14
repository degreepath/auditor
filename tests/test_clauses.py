from degreepath import *
from degreepath.clause import SingleClause, AndClause
import pytest
import io
import logging


def test_clauses(caplog):
    caplog.set_level(logging.DEBUG)

    x = SingleClause.load({"attributes": {"$eq": "csci_elective"}})
    expected_single = SingleClause(
        key="attributes", expected="csci_elective", operator=Operator.EqualTo
    )
    assert x == expected_single

    c = CourseInstance.from_s(s="CSCI 121", attributes=["csci_elective"])

    assert c is not None

    result = c.apply_clause(x)

    assert result is True
