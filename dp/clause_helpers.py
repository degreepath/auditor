from .data.course_enums import GradeOption, GradeCode
from typing import Any, Iterable, Iterator
from decimal import Decimal


def stringify_expected(expected: Any) -> Any:
    if isinstance(expected, tuple):
        return tuple(stringify_expected(e) for e in expected)

    if isinstance(expected, (GradeOption, GradeCode)):
        return expected.value

    elif isinstance(expected, Decimal):
        return str(expected)

    return expected


def flatten(lst: Iterable) -> Iterator:
    for el in lst:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el
