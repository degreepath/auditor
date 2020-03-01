from typing import Tuple, Dict, Any

import attr

from .data.course import CourseInstance


@attr.s(cache_hash=True, auto_attribs=True, slots=True, eq=False, order=False, hash=True)
class Claim:
    course: CourseInstance
    claimed_by: Tuple[str, ...]
    failed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crsid": self.course.crsid,
            "clbid": self.course.clbid,
            "claimed_by": self.claimed_by,
        }

    def get_course(self) -> CourseInstance:
        return self.course
