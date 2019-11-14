from typing import Iterable, Dict, List, Callable, TypeVar
from collections import defaultdict

T = TypeVar('T')
U = TypeVar('U')


def group_by(it: Iterable[T], key: Callable[[T], U]) -> Dict[U, List[T]]:
    grouped: Dict[U, List[T]] = defaultdict(list)

    for item in it:
        grouped[key(item)].append(item)

    return grouped
