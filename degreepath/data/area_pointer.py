import dataclasses
import logging

from ..clause import Clause, SingleClause, AndClause, OrClause
from .area_enums import AreaStatus, AreaType
from .clausable import Clausable

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class AreaPointer(Clausable):
    code: str
    status: AreaStatus
    kind: AreaType
    name: str
    degree: str

    def to_dict(self):
        return {
            "type": "area",
            "code": self.code,
            "status": self.status.name,
            "kind": self.kind.name,
            "degree": self.degree,
            "name": self.name,
        }

    @staticmethod
    def from_dict(*, code, status, kind, name, degree):
        return AreaPointer(
            code=code,
            status=AreaStatus(status),
            kind=AreaType(kind),
            name=name,
            degree=degree,
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

            raise TypeError(f"expected to get one of {list(self.__dict__.keys())}; got {clause.key}")

        raise TypeError(f"areapointer: expected a clause; found {type(clause)}")
