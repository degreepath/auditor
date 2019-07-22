from degreepath import *
from degreepath.clause import SingleClause, AndClause, Operator, load_clause, apply_operator
import pytest
import io
import logging


def test_clauses(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)

    x = load_clause({"attributes": {"$eq": "csci_elective"}}, c=c)
    expected_single = SingleClause(key="attributes", expected="csci_elective", expected_verbatim="csci_elective", operator=Operator.EqualTo)
    assert x == expected_single

    c = CourseInstance.from_s(s="CSCI 121", attributes=["csci_elective"])
    assert c is not None

    result = c.apply_clause(x)
    assert result is True


def test_operator_eq(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs="1", op=Operator.EqualTo, rhs=1)


def test_operator_eq(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=1, op=Operator.EqualTo, rhs=1)
    assert apply_operator(lhs=2, op=Operator.EqualTo, rhs=1) == False
    assert apply_operator(lhs=0, op=Operator.EqualTo, rhs=1) == False

    assert apply_operator(lhs=(1,), op=Operator.EqualTo, rhs=1)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.EqualTo, rhs=1)
    assert apply_operator(lhs=(1, 0, 1,), op=Operator.EqualTo, rhs=0)


def test_operator_neq(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=3, op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=1, op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=2, op=Operator.NotEqualTo, rhs=2) == False

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=(1,), op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=(2,), op=Operator.NotEqualTo, rhs=2) == False
    assert apply_operator(lhs=(2, 4,), op=Operator.NotEqualTo, rhs=2) == False


def test_operator_in(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=0)
    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=1)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=2) == False

    assert apply_operator(lhs=(), op=Operator.In, rhs=2) == False


def test_operator_nin(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.NotIn, rhs=2)
    assert apply_operator(lhs=(1,), op=Operator.NotIn, rhs=2)
    assert apply_operator(lhs=(), op=Operator.NotIn, rhs=2)

    assert apply_operator(lhs=(2,), op=Operator.NotIn, rhs=2) == False


def test_operator_lt(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=0, op=Operator.LessThan, rhs=2)
    assert apply_operator(lhs=3, op=Operator.LessThan, rhs=2) == False


def test_operator_lte(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=1, op=Operator.LessThanOrEqualTo, rhs=2)
    assert apply_operator(lhs=2, op=Operator.LessThanOrEqualTo, rhs=2)
    assert apply_operator(lhs=3, op=Operator.LessThanOrEqualTo, rhs=2) == False


def test_operator_gt(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=0, op=Operator.GreaterThan, rhs=2) == False
    assert apply_operator(lhs=3, op=Operator.GreaterThan, rhs=2)


def test_operator_gte(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=1, op=Operator.GreaterThanOrEqualTo, rhs=2) == False
    assert apply_operator(lhs=2, op=Operator.GreaterThanOrEqualTo, rhs=2)
    assert apply_operator(lhs=3, op=Operator.GreaterThanOrEqualTo, rhs=2)


def test_resolution(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)

    x = load_clause({"@xyz": {"$eq": 1}}, c=c)
    expected_single = SingleClause(key="@xyz", expected=1, expected_verbatim=1, operator=Operator.EqualTo)
    assert x == expected_single

    result = x.compare_and_resolve_with(value=1, map=lambda clause, value: (value, tuple([value])))
    assert result.result is True
