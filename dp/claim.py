from typing import Tuple, Dict, Any, TYPE_CHECKING
import attr

if TYPE_CHECKING:  # pragma: no cover
    from .data.course import CourseInstance  # noqa: F401


@attr.s(cache_hash=True, auto_attribs=True, slots=True, eq=False, order=False, hash=True, repr=False)
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

    def __repr__(self) -> str:
        return f"Claim(status={'fail' if self.failed else 'ok'}, course={self.course!r}, claimed_by={'/'.join(self.claimed_by)!r})"

    def get_course(self) -> 'CourseInstance':
        return self.course
