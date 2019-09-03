from typing import Tuple, Union, FrozenSet, Dict, Any, TYPE_CHECKING
import logging
import attr

from .clause import Clause
from .base.course import BaseCourseRule

if TYPE_CHECKING:
    from .data import CourseInstance  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class Claim:
    course: 'CourseInstance'
    claimant_path: Tuple[str, ...]
    value: Union[Clause, BaseCourseRule]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crsid": self.course.crsid,
            "clbid": self.course.clbid,
            "claimant_path": self.claimant_path,
            "value": self.value.to_dict(),
        }


@attr.s(frozen=True, cache_hash=True, auto_attribs=True, slots=True)
class ClaimAttempt:
    claim: Claim
    conflict_with: FrozenSet[Claim]
    did_fail: bool

    def failed(self) -> bool:
        return self.did_fail

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "conflict_with": [c.to_dict() for c in self.conflict_with],
            "failed": self.failed(),
        }

    def get_course(self) -> 'CourseInstance':
        return self.claim.course
