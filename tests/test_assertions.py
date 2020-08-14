from dp.assertion_clause import Assertion
from dp.data_type import DataType
from dp.context import RequirementContext
from dp.data.clausable import Clausable
from dp.constants import Constants
import logging
import pytest


def test_resolution(caplog):
    caplog.set_level(logging.DEBUG)

    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    class IntThing(Clausable):
        def apply_predicate(self):
            pass
        def to_dict(self):
            pass
        def sort_order(self):
            return (hash(self))

    x = Assertion.load({"assert": {"count(items)": {"$eq": 1}}}, c=c, ctx=ctx, data_type=DataType.Recital, path=['$'])

    result = x.audit_and_resolve(tuple([IntThing()]), ctx=ctx)
    assert result.ok() is True

    result = x.audit_and_resolve(tuple([IntThing(), IntThing()]), ctx=ctx)
    assert result.ok() is False


def test_ranges_eq(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$eq": 1}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=5)
    assert list(result) == [1]


def test_ranges_eq_2(caplog):
    """ensure that a solution with fewer matching courses than requested is still proposed"""
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    result = Assertion.load({"assert": {"count(courses)": {"$eq": 3}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$']).input_size_range(maximum=2)
    assert list(result) == [2]

    result = Assertion.load({"assert": {"count(courses)": {"$neq": 3}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$']).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2]

    result = Assertion.load({"assert": {"count(courses)": {"$lt": 3}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$']).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2]

    result = Assertion.load({"assert": {"count(courses)": {"$lte": 3}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$']).input_size_range(maximum=2)
    assert list(result) == [0, 1, 2, 3]

    result = Assertion.load({"assert": {"count(courses)": {"$gt": 3}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$']).input_size_range(maximum=2)
    assert list(result) == [2]

    result = Assertion.load({"assert": {"count(courses)": {"$gte": 3}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$']).input_size_range(maximum=2)
    assert list(result) == [2]


def test_ranges_gte(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$gte": 1}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=5)
    assert list(result) == [1, 2, 3, 4, 5]


def test_ranges_gte_at_most(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$gte": 1, "at_most": True}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=5)
    assert list(result) == [1]


def test_ranges_gt(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$gt": 1}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=5)
    assert list(result) == [2, 3, 4, 5]


def test_ranges_neq(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$neq": 1}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=5)
    assert list(result) == [0, 2, 3, 4, 5]


def test_ranges_lt(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$lt": 5}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=7)
    assert list(result) == [0, 1, 2, 3, 4]


def test_ranges_lte(caplog):
    caplog.set_level(logging.DEBUG)
    c = Constants(matriculation_year=2000)
    ctx = RequirementContext()

    x = Assertion.load({"assert": {"count(courses)": {"$lte": 5}}}, c=c, ctx=ctx, data_type=DataType.Course, path=['$'])
    result = x.input_size_range(maximum=7)
    assert list(result) == [0, 1, 2, 3, 4, 5]
