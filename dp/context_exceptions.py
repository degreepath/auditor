import attr
from typing import List, Optional, Tuple, Set, Iterator
import logging

from .exception import RuleException, OverrideException, InsertionException, ValueException

logger = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ContextExceptions:
    exceptions: List[RuleException] = attr.ib(factory=list)
    exception_paths_: Set[Tuple[str, ...]] = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        exception_paths = set(e.path for e in self.exceptions)
        object.__setattr__(self, "exception_paths_", exception_paths)

    def has_exception(self, path: Tuple[str, ...]) -> bool:
        return any(e.path[:len(path)] == path for e in self.exceptions)

    def get_insert_exceptions(self, path: Tuple[str, ...]) -> Iterator[InsertionException]:
        if path not in self.exception_paths_:
            return

        for exception in self.exceptions:
            if isinstance(exception, InsertionException) and exception.path == path:
                yield exception

    def get_insert_exceptions_beneath(self, path: Tuple[str, ...]) -> Iterator[InsertionException]:
        path_len = len(path)

        for exception in self.exceptions:
            if isinstance(exception, InsertionException) and exception.path[:path_len] == path:
                yield exception

    def get_waive_exception(self, path: Tuple[str, ...]) -> Optional[OverrideException]:
        if path not in self.exception_paths_:
            return None

        for e in self.exceptions:
            if isinstance(e, OverrideException) and e.path == path:
                return e

        return None

    def get_value_exception(self, path: Tuple[str, ...]) -> Optional[ValueException]:
        if path not in self.exception_paths_:
            return None

        for e in self.exceptions:
            if isinstance(e, ValueException) and e.path == path:
                return e

        return None
