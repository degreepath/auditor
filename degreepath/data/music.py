from typing import Dict, Any, Tuple, Optional, TYPE_CHECKING
import attr
import logging
import enum
import abc

from .clausable import Clausable
from ..status import ResultStatus

if TYPE_CHECKING:  # pragma: no cover
    from ..clause import SingleClause

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, eq=False, order=False, hash=True)
class MusicSlip(Clausable):
    year: int
    id: str
    term: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type(),
            "year": self.year,
            "term": self.term,
            "name": self.name,
        }

    @abc.abstractmethod
    def type(self) -> str:
        raise NotImplementedError('not implemented')

    def apply_single_clause(self, clause: 'SingleClause') -> bool:
        if clause.key == 'name':
            return clause.compare(self.name)

        if clause.key == 'year':
            return clause.compare(self.year)

        if clause.key == 'term':
            return clause.compare(self.term)

        raise TypeError(f"got unknown key {clause.key}")

    def __eq__(self, other: Any) -> bool:
        if other.__class__ is self.__class__:
            return hash(self) == hash(other)

        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if other.__class__ is self.__class__:
            return hash(self) != hash(other)

        return NotImplemented

    def sort_order(self) -> Tuple[int, int, str, str]:
        return (self.year, self.term, self.name, self.id)


class MusicPerformanceStatus(enum.Enum):
    Entrance = 'entrance'
    Continuance = 'continuance'


muspf_status_lookup = {
    'e': MusicPerformanceStatus.Entrance,
    'c': MusicPerformanceStatus.Continuance,
    '': None,
}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, eq=False, order=False, hash=True)
class MusicPerformance(MusicSlip):
    # TODO: make this be non-optional and look up the proper field to pull this data from
    status: Optional[MusicPerformanceStatus]

    @staticmethod
    def from_dict(data: Dict) -> 'MusicPerformance':
        return MusicPerformance(
            name=data['name'],
            id=data['id'],
            year=int(data['year']),
            term=int(data['term']),
            status=muspf_status_lookup[data.get('status', '')],
        )

    def apply_single_clause(self, clause: 'SingleClause') -> bool:
        if clause.key == 'status':
            if not self.status:
                return False
            return clause.compare(self.status.value)

        return super().apply_single_clause(clause)

    def type(self) -> str:
        return 'music performance'


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, eq=False, order=False, hash=True)
class MusicAttendance(MusicSlip):
    @staticmethod
    def from_dict(data: Dict) -> 'MusicAttendance':
        return MusicAttendance(
            name=data['name'],
            id=data['id'],
            year=int(data['year']),
            term=int(data['term']),
        )

    def type(self) -> str:
        return 'music attendance'


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, hash=True)
class MusicProficiencies:
    guitar: bool = False
    keyboard_1: bool = False
    keyboard_2: bool = False
    keyboard_3: bool = False
    keyboard_4: bool = False

    @staticmethod
    def from_dict(data: Dict) -> 'MusicProficiencies':
        return MusicProficiencies(
            guitar=data['guitar'],
            keyboard_1=data['keyboard_1'],
            keyboard_2=data['keyboard_2'],
            keyboard_3=data['keyboard_3'],
            keyboard_4=data['keyboard_4'],
        )

    def status(self, *, of: str) -> ResultStatus:
        matcher = {
            'Keyboard Level I': self.keyboard_1,
            'Keyboard Level II': self.keyboard_2,
            'Keyboard Level III': self.keyboard_3,
            'Keyboard Level IV': self.keyboard_4,
            'Guitar': self.guitar,
        }

        return ResultStatus.Pass if matcher[of] else ResultStatus.Pending
