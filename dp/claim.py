from typing import Tuple, Dict, Any, TYPE_CHECKING
import attr

if TYPE_CHECKING:  # pragma: no cover
    from .data import CourseInstance  # noqa: F401


@attr.s(cache_hash=True, auto_attribs=True, slots=True, eq=False, order=False, hash=True)
class Claim:
    course: 'CourseInstance'
    claimed_by: Tuple[str, ...]
    failed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crsid": self.course.crsid,
            "clbid": self.course.clbid,
            "claimed_by": self.claimed_by,
        }

    def get_course(self) -> 'CourseInstance':
        return self.course
