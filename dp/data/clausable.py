import abc
from typing import Tuple, Dict, Any, TYPE_CHECKING
import logging
import attr

if TYPE_CHECKING:  # pragma: no cover
    from ..predicate_clause import Predicate

logger = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ClausableIdentifier:
    type: str
    key: str
    value: str

    def to_dict(self) -> Dict[str, str]:
        return attr.asdict(self)


class Clausable(abc.ABC):
    @abc.abstractmethod
    def apply_predicate(self, clause: 'Predicate') -> bool:
        ...

    # TODO investigate removing this abstract method requirement
    @abc.abstractmethod
    def sort_order(self) -> Tuple:
        ...

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        ...

    @abc.abstractmethod
    def to_identifier(self) -> ClausableIdentifier:
        ...
