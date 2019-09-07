from degreepath.clause import SingleClause, Operator, load_clause, apply_operator, AppliedClauseResult
from degreepath.data import course_from_str
from degreepath.constants import Constants
import logging


def test_clauses(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)

    x = load_clause({"attributes": {"$eq": "csci_elective"}}, c=c)
    expected_single = SingleClause(key="attributes", expected="csci_elective", expected_verbatim="csci_elective", operator=Operator.EqualTo)
    assert x == expected_single

    crs = course_from_str(s="CSCI 121", attributes=["csci_elective"])

    assert crs.apply_clause(x) is True


def test_clauses_in(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)
    course = course_from_str(s="CSCI 296")

    values = tuple([296, 298, 396, 398])
    x = load_clause({"number": {"$in": values}}, c=c)
    expected_single = SingleClause(key="number", expected=values, expected_verbatim=values, operator=Operator.In)
    assert x == expected_single

    assert course.apply_clause(x) is True


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

    x = load_clause({"@xyz": {"$eq": 1}}, c=c)
    expected_single = SingleClause(key="@xyz", expected=1, expected_verbatim=1, operator=Operator.EqualTo)
    assert x == expected_single

    result = x.compare_and_resolve_with(value=1, map_func=lambda clause, value: AppliedClauseResult(value=value, data=tuple([value])))
    assert result.ok() is True


def test_ranges_eq(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$eq": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [1]


def test_ranges_eq_2(caplog):
    """ensure that a solution with fewer matching courses than requested is still proposed"""
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    result = load_clause({"count(courses)": {"$eq": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [2]

    result = load_clause({"count(courses)": {"$neq": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2]

    result = load_clause({"count(courses)": {"$lt": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2]

    result = load_clause({"count(courses)": {"$lte": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2, 3]

    result = load_clause({"count(courses)": {"$gt": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [2]

    result = load_clause({"count(courses)": {"$gte": 3}}, c=c).input_size_range(maximum=2)
    assert list(result) == [2]


def test_ranges_gte(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$gte": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [1, 2, 3, 4, 5]


def test_ranges_gte_at_most(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$gte": 1, "at_most": True}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [1]


def test_ranges_gt(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$gt": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [2, 3, 4, 5]


def test_ranges_neq(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$neq": 1}}, c=c)
    result = x.input_size_range(maximum=5)
    assert list(result) == [0, 2, 3, 4, 5]


def test_ranges_lt(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$lt": 5}}, c=c)
    result = x.input_size_range(maximum=7)
    assert list(result) == [0, 1, 2, 3, 4]


def test_ranges_lte(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"count(courses)": {"$lte": 5}}, c=c)
    result = x.input_size_range(maximum=7)
    assert list(result) == [0, 1, 2, 3, 4, 5]


def test_subsets_simple_1(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"attributes": {"$eq": "electives"}}, c=c)
    y = load_clause({"attributes": {"$eq": "doggie"}}, c=c)
    assert x.is_subset(y) is False


def test_subsets_simple_2(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"attributes": {"$in": ["electives"]}}, c=c)
    y = load_clause({"attributes": {"$eq": "electives"}}, c=c)
    assert x.is_subset(y) is False
    assert y.is_subset(x) is True


def test_subsets_simple_3(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"$or": [{"attributes": {"$in": ["electives"]}}]}, c=c)
    y = load_clause({"attributes": {"$eq": "electives"}}, c=c)
    assert x.is_subset(y) is False
    assert y.is_subset(x) is True


def test_subsets_simple_4(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)

    x = load_clause({"$and": [{"attributes": {"$in": ["electives"]}}]}, c=c)
    y = load_clause({"attributes": {"$eq": "electives"}}, c=c)
    assert x.is_subset(y) is False
    assert y.is_subset(x) is True
