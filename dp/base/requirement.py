import attr
from typing import Optional, Dict, Any, List, cast, TYPE_CHECKING
from fractions import Fraction

from .bases import Base
from ..status import ResultStatus, PassingStatuses

if TYPE_CHECKING:  # pragma: no cover
    from ..claim import ClaimAttempt  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseRequirementRule(Base):
    name: str
    message: Optional[str]
    result: Optional[Base]
    is_audited: bool
    is_contract: bool
    in_gpa: bool
    disjoint: Optional[bool]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "message": self.message,
            "result": self.result.to_dict() if self.result is not None else None,
            "audited_by": "department" if self.is_audited else None,
            "contract": self.is_contract,
        }

    def type(self) -> str:
        return "requirement"

    def status(self) -> ResultStatus:
        if self.result is None:
            return super().status()

        if self.is_audited:
            return ResultStatus.PendingApproval

        return self.result.status()

    def rank(self) -> Fraction:
        if self.is_audited and self.waived():
            return Fraction(1, 1)

        if self.result is None:
            return Fraction(0, 1)

        status = self.status()
        if status in PassingStatuses:
            boost: Optional[int] = 1
        else:
            boost = None

        child_rank: Fraction = self.result.rank()

        return cast(Fraction, child_rank + boost if boost else child_rank)

    def is_always_disjoint(self) -> bool:
        if self.disjoint is True:
            return True

        if self.result is None:
            return super().is_always_disjoint()

        return self.result.is_always_disjoint()

    def is_never_disjoint(self) -> bool:
        if self.disjoint is False:
            return True

        if self.result is None:
            return super().is_never_disjoint()

        return self.result.is_never_disjoint()

    def is_in_gpa(self) -> bool:
        return self.in_gpa

    def claims(self) -> List['ClaimAttempt']:
        if self.is_audited or self.result is None:
            return []

        return self.result.claims()

    def claims_for_gpa(self) -> List['ClaimAttempt']:
        if self.is_in_gpa() and self.result and not self.is_audited:
            return self.result.claims_for_gpa()

        return []
