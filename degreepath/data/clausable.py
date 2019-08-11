import abc
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..clause import Clause


class Clausable(abc.ABC):
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        ...

    @abc.abstractmethod
    def apply_clause(self, clause: 'Clause') -> bool:
        ...
