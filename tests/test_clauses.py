from dp.clause import SingleClause
from dp.operator import Operator, apply_operator
from dp.load_clause import compute_single_clause_diff, load_clause
from dp.context import RequirementContext
from dp.data.music import MusicProficiencies
from dp.data.area_pointer import AreaPointer
from dp.data.clausable import Clausable
from dp.data.course import course_from_str
from dp.constants import Constants
from dp.rule.assertion import AssertionRule
import logging
import pytest
from typing import Any


def load_clause_test(clause: Any, c: Any) -> AssertionRule:
    return AssertionRule.with_clause(load_clause(clause, c=c))


def test_clauses(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)

    x = load_clause({"attributes": {"$eq": "csci_elective"}}, c=c)
    expected_single = SingleClause.from_args(key="attributes", expected="csci_elective", expected_verbatim="csci_elective", operator=Operator.EqualTo)
    assert x == expected_single

    crs = course_from_str(s="CSCI 121", attributes=["csci_elective"])

    assert x.apply(crs) is True


def test_clauses_in(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)
    course = course_from_str(s="CSCI 296")

    values = tuple([296, 298, 396, 398])
    x = load_clause({"number": {"$in": values}}, c=c)
    expected_single = SingleClause.from_args(key="number", expected=values, expected_verbatim=values, operator=Operator.In)
    assert x == expected_single

    assert x.apply(course) is True


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


def test_resolution(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)

    class IntThing(Clausable):
        def apply_single_clause(self):
            pass
        def to_dict(self):
            pass
        def sort_order(self):
            return (hash(self))

    x = load_clause_test({"count(items)": {"$eq": 1}}, c=c)
    expected_single = SingleClause.from_args(key="count(items)", expected=1, expected_verbatim=1, operator=Operator.EqualTo)
    assert x.assertion == expected_single

    result = x.resolve(tuple([IntThing()]))
    assert result.ok() is True

    result = x.resolve(tuple([IntThing(), IntThing()]))
    assert result.ok() is False


def test_ranges_eq(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$eq": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [1]


def test_ranges_eq_2(caplog):
    """ensure that a solution with fewer matching courses than requested is still proposed"""
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    result = load_clause_test({"count(courses)": {"$eq": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [2]

    result = load_clause_test({"count(courses)": {"$neq": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2]

    result = load_clause_test({"count(courses)": {"$lt": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2]

    result = load_clause_test({"count(courses)": {"$lte": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2, 3]

    result = load_clause_test({"count(courses)": {"$gt": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [2]

    result = load_clause_test({"count(courses)": {"$gte": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [2]


def test_ranges_gte(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$gte": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [1, 2, 3, 4, 5]


def test_ranges_gte_at_most(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$gte": 1, "at_most": True}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [1]


def test_ranges_gt(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$gt": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [2, 3, 4, 5]


def test_ranges_neq(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$neq": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [0, 2, 3, 4, 5]


def test_ranges_lt(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$lt": 5}}, c=c)
    result = x.input_size_range(maximum=7)
    assert list(result) == [0, 1, 2, 3, 4]


def test_ranges_lte(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause_test({"count(courses)": {"$lte": 5}}, c=c)
    result = x.input_size_range(maximum=7)
    assert list(result) == [0, 1, 2, 3, 4, 5]


def test_compute_single_clause_diff():
    from decimal import Decimal
    ctx = RequirementContext(areas=(AreaPointer.with_code('711'),))

    assert compute_single_clause_diff({'has-area-code(711)': '+ 0.50'}, ctx=ctx) == Decimal(0.5)
    assert compute_single_clause_diff({'has-area-code(711)': '+  .50'}, ctx=ctx) == Decimal(0.5)

    with pytest.raises(TypeError, match=r'unknown \$ifs key unknown-key'):
        assert compute_single_clause_diff({'unknown-key(711)': '+  .50'}, ctx=ctx) == Decimal(0)

    ctx = RequirementContext(
        areas=(AreaPointer.with_code('711'),),
        music_proficiencies=MusicProficiencies(keyboard_3=True, keyboard_4=False),
    )

    assert compute_single_clause_diff({'has-area-code(711) + passed-proficiency-exam(Keyboard Level III)': '+ 0.50'}, ctx=ctx) == Decimal(0.5)
    assert compute_single_clause_diff({'has-area-code(711) + passed-proficiency-exam(Keyboard Level IV)': '+  .50'}, ctx=ctx) == Decimal(0)

    assert compute_single_clause_diff({
        'has-area-code(711)': '+ 0.50',
        'has-area-code(711) + passed-proficiency-exam(Keyboard Level III)': '+ 0.50',
    }, ctx=ctx) == Decimal(1.0)

    assert compute_single_clause_diff({
        'has-area-code(711)': '+ 0.50',
        'has-area-code(711) + passed-proficiency-exam(Keyboard Level IV)': '+ 0.50',
    }, ctx=ctx) == Decimal(0.5)
