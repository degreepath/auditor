from typing import Dict, Any, Optional
import attr
import logging
import decimal

from ..clause import Clause, SingleClause, AndClause, OrClause
from .area_enums import AreaStatus, AreaType
from .clausable import Clausable

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaPointer(Clausable):
    code: str
    status: AreaStatus
    kind: AreaType
    name: str
    degree: str
    dept: Optional[str]
    gpa: Optional[decimal.Decimal]

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
        return AreaPointer(
            code=data['code'],
            status=AreaStatus(data['status']),
            kind=AreaType(data['kind']),
            name=data['name'],
            degree=data['degree'],
            gpa=decimal.Decimal(data['gpa']) if 'gpa' in data else None,
            dept=data.get('dept', None),
        )

    def apply_clause(self, clause: Clause) -> bool:
        if isinstance(clause, AndClause):
            logger.debug("clause/and/compare %s", clause)
            return all(self.apply_clause(subclause) for subclause in clause.children)

        elif isinstance(clause, OrClause):
            logger.debug("clause/or/compare %s", clause)
            return any(self.apply_clause(subclause) for subclause in clause.children)

        elif isinstance(clause, SingleClause):
            if clause.key == 'code':
                return clause.compare(self.code)
            elif clause.key == 'status':
                return clause.compare(self.status.name)
            elif clause.key in ('kind', 'type'):
                return clause.compare(self.kind.name)
            elif clause.key == 'name':
                return clause.compare(self.name)
            elif clause.key == 'degree':
                return clause.compare(self.degree)
            elif clause.key == 'gpa':
                if self.gpa is not None:
                    return clause.compare(self.gpa)
                else:
                    return False

            raise TypeError(f"expected to get one of {list(self.__dict__.keys())}; got {clause.key}")

        raise TypeError(f"areapointer: expected a clause; found {type(clause)}")
