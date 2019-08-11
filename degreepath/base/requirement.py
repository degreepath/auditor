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
            "audited_by": self.audited_by,
            "contract": self.is_contract,
        }

    def type(self):
        return "requirement"
