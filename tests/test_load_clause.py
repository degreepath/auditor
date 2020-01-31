from dp.load_clause import load_clause
from dp.constants import Constants


def test_load_single_clause_constant_expands_to_several():
    ppm = 'saxophone, jazz saxophone'
    constants = Constants(primary_performing_medium=ppm)
    input_data = {'name': {'$eq': '$primary-performing-medium'}}

    c = load_clause(input_data, c=constants)

    assert list(c.expected) == ['saxophone', 'jazz saxophone']


def test_load_single_clause_constant_expands_to_several_nested():
    ppm = 'saxophone, jazz saxophone'
    constants = Constants(primary_performing_medium=ppm)
    input_data = {'name': {'$in': ['piano', '$primary-performing-medium']}}

    c = load_clause(input_data, c=constants)

    assert list(c.expected) == ['piano', 'saxophone', 'jazz saxophone']
