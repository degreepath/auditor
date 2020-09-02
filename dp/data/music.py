from typing import Dict, Union, Any, Tuple, Optional, TYPE_CHECKING
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
    'E': MusicPerformanceStatus.Entrance,
    'C': MusicPerformanceStatus.Continuance,
    '': None,
}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, eq=False, order=False, hash=True)
class MusicPerformance(MusicSlip):
    role: Optional[str]
    status: Optional[MusicPerformanceStatus]

    @staticmethod
    def from_dict(data: Dict) -> 'MusicPerformance':
        return MusicPerformance(
            name=data['name'],
            id=data['id'],
            year=int(data['year']),
            term=int(data['term']),
            role=data.get('role', None),
            status=muspf_status_lookup[data.get('status', '')],
        )

    def apply_single_clause(self, clause: 'SingleClause') -> bool:
        if clause.key == 'status':
            if not self.status:
                return False
            return clause.compare(self.status.value)

        if clause.key == 'role':
            if not self.role:
                return False
            return clause.compare(self.role)

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


class MusicProficiencyStatus(enum.Enum):
    No = "N"
    Yes = "Y"
    Exam = "E"
    Class = "C"

    @staticmethod
    def parse(data: Union[str, bool]) -> 'MusicProficiencyStatus':
        if data is True:
            return MusicProficiencyStatus.Yes
        elif data is False:
            return MusicProficiencyStatus.No
        else:
            return MusicProficiencyStatus(data)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class MusicProficiencies:
    guitar: MusicProficiencyStatus = MusicProficiencyStatus.No
    keyboard_1: MusicProficiencyStatus = MusicProficiencyStatus.No
    keyboard_2: MusicProficiencyStatus = MusicProficiencyStatus.No
    keyboard_3: MusicProficiencyStatus = MusicProficiencyStatus.No
    keyboard_4: MusicProficiencyStatus = MusicProficiencyStatus.No

    @staticmethod
    def from_dict(data: Dict) -> 'MusicProficiencies':
        return MusicProficiencies(
            guitar=MusicProficiencyStatus.parse(data.get('guitar', 'N')),
            keyboard_1=MusicProficiencyStatus.parse(data.get('keyboard_1', 'N')),
            keyboard_2=MusicProficiencyStatus.parse(data.get('keyboard_2', 'N')),
            keyboard_3=MusicProficiencyStatus.parse(data.get('keyboard_3', 'N')),
            keyboard_4=MusicProficiencyStatus.parse(data.get('keyboard_4', 'N')),
        )

    def status(self, *, of: str, exam_only: bool) -> ResultStatus:
        compare_against: Tuple[MusicProficiencyStatus, ...]
        if exam_only:
            compare_against = (MusicProficiencyStatus.Exam,)
        else:
            compare_against = (MusicProficiencyStatus.Yes, MusicProficiencyStatus.Exam, MusicProficiencyStatus.Class)

        if of == 'Keyboard Level I':
            result = ResultStatus.Done if self.keyboard_1 in compare_against else ResultStatus.Empty
        elif of == 'Keyboard Level II':
            result = ResultStatus.Done if self.keyboard_2 in compare_against else ResultStatus.Empty
        elif of == 'Keyboard Level III':
            result = ResultStatus.Done if self.keyboard_3 in compare_against else ResultStatus.Empty
        elif of == 'Keyboard Level IV':
            result = ResultStatus.Done if self.keyboard_4 in compare_against else ResultStatus.Empty
        elif of == 'Guitar':
            result = ResultStatus.Done if self.guitar in compare_against else ResultStatus.Empty
        else:
            raise KeyError(f'unknown proficiency status key {of!r}')

        print(f'comparing {of!r} to {compare_against}: {result} (exam-only: {exam_only}) {self!r}')

        return result


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class MusicMediums:
    ppm: Union[str, Tuple[str, ...]] = 'Unknown'
    ppm2: Union[str, Tuple[str, ...]] = 'Unknown'
    spm: Union[str, Tuple[str, ...]] = 'Unknown'
    spm2: Union[str, Tuple[str, ...]] = 'Unknown'

    @staticmethod
    def parse_medium(medium: str) -> Union[str, Tuple[str, ...]]:
        if ',' in medium:
            return tuple(m.strip() for m in medium.split(', '))
        else:
            return medium

    @staticmethod
    def from_dict(data: Dict) -> 'MusicMediums':
        ppm = MusicMediums.parse_medium(data.get('ppm', 'Unknown'))
        ppm2 = MusicMediums.parse_medium(data.get('ppm2', 'Unknown'))
        spm = MusicMediums.parse_medium(data.get('spm', 'Unknown'))
        spm2 = MusicMediums.parse_medium(data.get('spm2', 'Unknown'))

        return MusicMediums(ppm=ppm, ppm2=ppm2, spm=spm, spm2=spm2)
