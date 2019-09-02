import attr
from typing import Optional, Tuple, Dict, Any
import enum

from .bases import Base, Summable


@enum.unique
class AuditedBy(enum.Enum):
    Department = "department"
    Registrar = "registrar"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
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
            "audited_by": self.audited_by.value if self.audited_by else None,
            "contract": self.is_contract,
        }

    def type(self) -> str:
        return "requirement"

    def rank(self) -> Summable:
        if self.result is None:
            return 0
        boost = 1 if self.ok() else 0
        return self.result.rank() + boost

    def max_rank(self) -> Summable:
        if self.result is None:
            return 1
        return self.result.max_rank() + 1
