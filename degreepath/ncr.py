import operator as op
from functools import reduce
from typing import Iterable


def ncr(n: int, r: int) -> int:
    r = min(r, n - r)
    numer = reduce(op.mul, range(n, n - r, -1), 1)
    denom = reduce(op.mul, range(1, r + 1), 1)
    return numer // denom


def mult(it: Iterable[int]) -> int:
    return reduce(op.mul, it, 0)
