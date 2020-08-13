import abc
from typing import Tuple, TYPE_CHECKING
import logging

if TYPE_CHECKING:  # pragma: no cover
    from ..predicate_clause import Predicate

logger = logging.getLogger(__name__)


class Clausable(abc.ABC):
    @abc.abstractmethod
    def apply_predicate(self, clause: 'Predicate') -> bool:
        ...

    # TODO investigate removing this abstract method requirement
    @abc.abstractmethod
    def sort_order(self) -> Tuple:
        ...
