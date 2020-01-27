from functools import partial
from dp.lazy_product import lazy_product
import itertools


def check_equivalence(*iter_funcs, **kwargs):
    lazy_result = lazy_product(*iter_funcs, **kwargs)
    iters = (f() for f in iter_funcs)
    itertools_result = itertools.product(*iters, **kwargs)
    return list(lazy_result) == list(itertools_result)


def lazy_product_func(*a, **k):
    return partial(lazy_product, *a, **k)


def range_func(*a, **k):
    return partial(range, *a, **k)


def test_equivalence():
    assert check_equivalence()
    assert check_equivalence(repeat=0)
    assert check_equivalence(repeat=1)
    assert check_equivalence(repeat=2)
    assert check_equivalence(range_func(1))
    assert check_equivalence(range_func(1), repeat=2)
    assert check_equivalence(range_func(2))
    assert check_equivalence(range_func(2), repeat=2)
    assert check_equivalence(range_func(2), range_func(3))
    assert check_equivalence(range_func(2), range_func(1), range_func(3))
    assert check_equivalence(range_func(2), range_func(1), range_func(3), repeat=2)
    assert check_equivalence(range_func(2), range_func(3), repeat=2)
    assert check_equivalence(range_func(2), range_func(3), repeat=2)
    assert check_equivalence(range_func(3), range_func(2, 7), repeat=0)
    assert check_equivalence(range_func(3), range_func(2, 7), repeat=4)
