import logging

from dp.op import Operator, apply_operator


def test_operator_eq(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs="1", op=Operator.EqualTo, rhs=1)
    assert apply_operator(lhs=("1",), op=Operator.EqualTo, rhs=1)
    assert apply_operator(lhs=(1,), op=Operator.EqualTo, rhs="1")

    assert apply_operator(lhs=1, op=Operator.EqualTo, rhs=1)
    assert apply_operator(lhs=2, op=Operator.EqualTo, rhs=1) is False
    assert apply_operator(lhs=0, op=Operator.EqualTo, rhs=1) is False

    assert apply_operator(lhs=(1,), op=Operator.EqualTo, rhs=1)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.EqualTo, rhs=1)
    assert apply_operator(lhs=(1, 0, 1,), op=Operator.EqualTo, rhs=0)


def test_operator_neq(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=3, op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=1, op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=2, op=Operator.NotEqualTo, rhs=2) is False

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=(1,), op=Operator.NotEqualTo, rhs=2)
    assert apply_operator(lhs=(2,), op=Operator.NotEqualTo, rhs=2) is False
    assert apply_operator(lhs=(2, 4,), op=Operator.NotEqualTo, rhs=2) is False


def test_operator_in(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=0)
    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=1)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=2) is False

    assert apply_operator(lhs=(), op=Operator.In, rhs=2) is False


def test_operator_in_subset(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.In, rhs=(0, 1))
    assert apply_operator(lhs=(1, 2,), op=Operator.In, rhs=(0, 1)) is True
    assert apply_operator(lhs=(1, 2,), op=Operator.In, rhs=(0,)) is False


def test_operator_nin(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=(1, 0, 1,), op=Operator.NotIn, rhs=2)
    assert apply_operator(lhs=(1,), op=Operator.NotIn, rhs=2)
    assert apply_operator(lhs=(), op=Operator.NotIn, rhs=2)

    assert apply_operator(lhs=(2,), op=Operator.NotIn, rhs=2) is False


def test_operator_lt(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=0, op=Operator.LessThan, rhs=2)
    assert apply_operator(lhs=3, op=Operator.LessThan, rhs=2) is False


def test_operator_lte(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=1, op=Operator.LessThanOrEqualTo, rhs=2)
    assert apply_operator(lhs=2, op=Operator.LessThanOrEqualTo, rhs=2)
    assert apply_operator(lhs=3, op=Operator.LessThanOrEqualTo, rhs=2) is False


def test_operator_gt(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=0, op=Operator.GreaterThan, rhs=2) is False
    assert apply_operator(lhs=3, op=Operator.GreaterThan, rhs=2)


def test_operator_gte(caplog):
    caplog.set_level(logging.DEBUG)

    assert apply_operator(lhs=1, op=Operator.GreaterThanOrEqualTo, rhs=2) is False
    assert apply_operator(lhs=2, op=Operator.GreaterThanOrEqualTo, rhs=2)
    assert apply_operator(lhs=3, op=Operator.GreaterThanOrEqualTo, rhs=2)
