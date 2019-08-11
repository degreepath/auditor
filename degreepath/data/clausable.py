import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..clause import Clause


class Clausable(abc.ABC):
    def apply_clause(self, clause: 'Clause') -> bool:
        ...
