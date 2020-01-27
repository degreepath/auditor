# adapted from https://gist.github.com/jeffdonahue/12ff1b8e90bed6ed22221cbd9ba49578

from typing import Iterable, Iterator, Callable


def lazy_product(*iter_funcs: Callable[[], Iterable], repeat: int = 1) -> Iterator:
    """
    If f1, f2, ..., are functions which have no (required) arguments and
    return iterables, then

        lazy_product(f1, f2, ..., repeat=k)

    is equivalent to

        itertools.product(f1(), f2(), ..., repeat=k)

    but much faster in certain cases.
    For example, let f have the following definition:

        def f(n):
            def func():
                return xrange(n)
            return func

    Then, this code:

        p = itertools.product(*[f(N)() for _ in xrange(M)], repeat=K)
        first_element = next(p)

    takes O(NMK) time and memory to execute, whereas

        p = lazy_product(*[f(N) for _ in xrange(M)], repeat=K)
        first_element = next(p)

    is equivalent, and takes just O(MK) time and memory.
    (Of course, iterating over either result is exactly N^(MK) steps, and each
    step takes O(1) time; the only difference between itertools.product and
    lazy_product is at the time of initialization of the iterable p
    (including the call to next(p) to get the first element, as shown above).

    itertools.product's O(N) speed/memory overhead results from its saving the
    full result of range(N) as a list (or similar data structure) in memory.
    This is necessary as itertools.product takes iterables as input, and it is
    not generally possible to "reset" an iterator, so all of its values
    instead need to be stored. So, the input to lazy_product is an iterable
    of *functions* returning iterables, rather than the iterables themselves,
    allowing for repeated iteration over each iterable (by calling iter_func
    again when we reach the end of the iterable that iter_func created on
    the previous call).

    Inputs:
      - iter_funcs: functions with no (required) arguments that create and
        return an iterable. Each function is assumed to be be deterministic --
        i.e., return an identical iterable on each call.  (Otherwise, the
        behavior of lazy_product is undefined.)
      - repeat: an integer value.

    Returns:
        an iterator over the Cartesian product of the iterables returned
        by the elements of iter_funcs -- equivalent to:
            return itertools.product(*(f() for f in iter_funcs), **kwargs)
    """
    iterables = [iter(f()) for _ in range(repeat) for f in iter_funcs]
    values = [next(i) for i in iterables]

    while True:
        yield tuple(values)
        for index in reversed(range(len(iterables))):
            try:
                values[index] = next(iterables[index])
                break
            except StopIteration:
                iterables[index] = iter(iter_funcs[index % len(iter_funcs)]())
                values[index] = next(iterables[index])
        else:
            return
