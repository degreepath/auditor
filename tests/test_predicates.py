from dp.predicate_clause import Predicate, load_predicate
from dp.op import Operator
from dp.data_type import DataType
from dp.data.course import course_from_str
from dp.constants import Constants
from dp.context import RequirementContext
import logging
import pytest


def test_clauses(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = load_predicate({"attributes": {"$eq": "csci_elective"}}, c=c, ctx=ctx, mode=DataType.Course)
    expected_single = Predicate.from_args(key="attributes", expected="csci_elective", original="csci_elective", operator=Operator.EqualTo)
    assert x == expected_single

    crs = course_from_str(s="CSCI 121", attributes=["csci_elective"])

    assert x.apply(crs) is True


def test_clauses_in(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()
    course = course_from_str(s="CSCI 296")

    values = tuple([296, 298, 396, 398])
    x = load_predicate({"number": {"$in": values}}, c=c, ctx=ctx, mode=DataType.Course)
    expected_single = Predicate.from_args(key="number", expected=values, original=values, operator=Operator.In)
    assert x == expected_single

    assert x.apply(course) is True


def test_load_predicate_constant_expands_to_several():
    ppm = tuple(['saxophone', 'jazz saxophone'])
    constants = Constants(primary_performing_medium=ppm)
    ctx = RequirementContext()
    input_data = {'name': {'$eq': '$primary-performing-medium'}}

    c = load_predicate(input_data, c=constants, mode=DataType.Course, ctx=ctx)
    assert isinstance(c, Predicate)

    assert list(c.expected) == ['saxophone', 'jazz saxophone']


def test_load_predicate_constant_expands_to_several_nested():
    ppm = tuple(['saxophone', 'jazz saxophone'])
    constants = Constants(primary_performing_medium=ppm)
    ctx = RequirementContext()
    input_data = {'name': {'$in': ['piano', '$primary-performing-medium']}}

    c = load_predicate(input_data, c=constants, mode=DataType.Course, ctx=ctx)
    assert isinstance(c, Predicate)

    assert list(c.expected) == ['piano', 'saxophone', 'jazz saxophone']
