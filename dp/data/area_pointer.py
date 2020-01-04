from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
import attr
import logging
import decimal

from .area_enums import AreaStatus, AreaType
from .clausable import Clausable

if TYPE_CHECKING:  # pragma: no cover
    from ..clause import SingleClause

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, eq=False, order=False, hash=True)
class AreaPointer(Clausable):
    code: str
    status: AreaStatus
    kind: AreaType
    name: str
    degree: str
    dept: Optional[str]
    gpa: Optional[decimal.Decimal]

    @staticmethod
    def with_code(code: str) -> 'AreaPointer':
        return AreaPointer(
            code=code,
            status=AreaStatus.WhatIf,
            kind=AreaType.Concentration,
            name='',
            degree='',
            gpa=None,
            dept=None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "area",
            "code": self.code,
            "status": self.status.name,
            "kind": self.kind.name,
            "degree": self.degree,
            "dept": self.dept,
            "name": self.name,
        }

    @staticmethod
    def from_dict(data: Dict) -> 'AreaPointer':
        if isinstance(data, AreaPointer):
            return data  # type: ignore

        return AreaPointer(
            code=data['code'],
            status=AreaStatus(data['status']),
            kind=AreaType(data['kind']),
            name=data['name'],
            degree=data['degree'],
            gpa=decimal.Decimal(data['gpa']) if 'gpa' in data else None,
            dept=data.get('dept', None),
        )

    def apply_single_clause(self, clause: 'SingleClause') -> bool:  # noqa: C901
        if clause.key == 'code':
            return clause.compare(self.code)

        if clause.key == 'status':
            return clause.compare(self.status.name)

        if clause.key in ('kind', 'type'):
            return clause.compare(self.kind.name)

        if clause.key == 'name':
            return clause.compare(self.name)

        if clause.key == 'degree':
            return clause.compare(self.degree)

        if clause.key == 'gpa':
            if self.gpa is not None:
                return clause.compare(self.gpa)
            else:
                return False

        raise TypeError(f"expected got unknown key {clause.key}")

    def __eq__(self, other: Any) -> bool:
        if other.__class__ is self.__class__:
            return hash(self) == hash(other)

        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if other.__class__ is self.__class__:
            return hash(self) != hash(other)

        return NotImplemented

    def sort_order(self) -> Tuple[str, str]:
        return (self.kind.value, self.code)
