from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import enum

from .bases import Base


@enum.unique
class AuditedBy(enum.Enum):
    Department = "department"
    Registrar = "registrar"


@dataclass(frozen=True)
class BaseRequirementRule(Base):
    __slots__ = ('name', 'message', 'result', 'audited_by', 'is_contract')
    name: str
    message: Optional[str]
    result: Optional[Base]
    audited_by: Optional[AuditedBy]
    is_contract: bool
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "message": self.message,
            "result": self.result.to_dict() if self.result is not None else None,
            "audited_by": self.audited_by.value if self.audited_by else None,
            "contract": self.is_contract,
        }

    def type(self) -> str:
        return "requirement"

    def rank(self) -> int:
        boost = 1 if self.ok() else 0
        return self.result.rank() + boost if self.result else 0

    def max_rank(self) -> int:
        return self.result.max_rank() + 1 if self.result else 0
