from dataclasses import dataclass, field
from typing import Tuple, Union, FrozenSet, Optional, Dict, Any, TYPE_CHECKING
import logging

from .clause import Clause
from .base.course import BaseCourseRule

if TYPE_CHECKING:
    from .context import RequirementContext
    from .data import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Claim:
    crsid: str
    clbid: str
    claimant_path: Tuple[str, ...]
    value: Union[Clause, BaseCourseRule]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crsid": self.crsid,
            "clbid": self.clbid,
            "claimant_path": self.claimant_path,
            "value": self.value.to_dict(),
        }


@dataclass(frozen=True)
class ClaimAttempt:
    claim: Claim
    conflict_with: FrozenSet[Claim] = field(default_factory=frozenset)

    def failed(self) -> bool:
        return len(self.conflict_with) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "conflict_with": [c.to_dict() for c in self.conflict_with],
        }

    def get_course(self, *, ctx: 'RequirementContext') -> Optional['CourseInstance']:
        return ctx.find_course_by_clbid(self.claim.clbid)

    def hash(self) -> str:
        return str(hash(self))
