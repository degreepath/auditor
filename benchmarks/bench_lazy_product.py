import itertools
import pytest

from dp.lazy_product import lazy_product


@pytest.mark.benchmark()
def test_eager_small(benchmark):
    itertools_input = [range(1_000_000) for _ in range(10)]
    p = benchmark(itertools.product, *itertools_input)
    next(p)


@pytest.mark.benchmark()
def test_lazy_small(benchmark):
    lazy_input = [lambda: range(1_000_000) for _ in range(10)]
    p = benchmark(lazy_product, *lazy_input)
    next(p)


@pytest.mark.benchmark()
def test_eager_large(benchmark):
    itertools_input = [range(10_000_000) for _ in range(10)]
    p = benchmark(itertools.product, *itertools_input)
    next(p)


@pytest.mark.benchmark()
def test_lazy_large(benchmark):
    lazy_input = [lambda: range(10_000_000) for _ in range(10)]
    p = benchmark(lazy_product, *lazy_input)
    next(p)
