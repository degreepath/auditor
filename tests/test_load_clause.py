from dp.load_clause import load_clause
from dp.clause import SingleClause
from dp.constants import Constants
from dp.context import RequirementContext


def test_load_single_clause_constant_expands_to_several():
    ctx = RequirementContext()

    ppm = tuple(['saxophone', 'jazz saxophone'])
    constants = Constants(primary_performing_medium=ppm)
    input_data = {'name': {'$eq': '$primary-performing-medium'}}

    c = load_clause(input_data, c=constants, ctx=ctx)
    assert isinstance(c, SingleClause)

    assert list(c.expected) == ['saxophone', 'jazz saxophone']


def test_load_single_clause_constant_expands_to_several_nested():
    ctx = RequirementContext()

    ppm = tuple(['saxophone', 'jazz saxophone'])
    constants = Constants(primary_performing_medium=ppm)
    input_data = {'name': {'$in': ['piano', '$primary-performing-medium']}}

    c = load_clause(input_data, c=constants, ctx=ctx)
    assert isinstance(c, SingleClause)

    assert list(c.expected) == ['piano', 'saxophone', 'jazz saxophone']
