import abc
from typing import Dict, Tuple, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:  # pragma: no cover
    from ..clause import SingleClause

logger = logging.getLogger(__name__)


class Clausable(abc.ABC):
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        ...

    @abc.abstractmethod
    def apply_single_clause(self, clause: 'SingleClause') -> bool:
        ...

    @abc.abstractmethod
    def sort_order(self) -> Tuple:
        ...
