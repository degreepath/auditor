import attr
from typing import Dict, List, Iterator, Collection, Optional, TYPE_CHECKING
import re
import logging

from ..base import Rule, BaseCourseRule
from ..constants import Constants
from ..lib import str_to_grade_points
from ..solution.course import CourseSolution
from ..exception import InsertionException

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseRule(Rule, BaseCourseRule):
    ap: Optional[str] = None
    ib: Optional[str] = None
    cal: Optional[str] = None

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: List[str]) -> 'CourseRule':
        course = data['course']
        min_grade = data.get('grade', None)

        path = [*path, f"*{course}" + (f"(grade >= {min_grade})" if min_grade is not None else "")]

        return CourseRule(
            course=course,
            hidden=data.get("hidden", False),
            grade=str_to_grade_points(min_grade) if min_grade is not None else None,
            allow_claimed=data.get("including claimed", False),
            path=tuple(path),
            ap=data.get('ap', None),
            ib=data.get('ib', None),
            cal=data.get('cal', None),
        )

    def validate(self, *, ctx: 'RequirementContext') -> None:
        method_a = re.match(r"[A-Z]{3,5} [0-9]{3}", self.course)
        method_b = re.match(r"[A-Z]{2}/[A-Z]{2} [0-9]{3}", self.course)
        method_c = re.match(r"(IS|ID) [0-9]{3}", self.course)

        assert (method_a or method_b or method_c) is not None, f"{self.course}, {method_a}, {method_b}, {method_c}"

    def get_requirement_names(self) -> List[str]:
        return []

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[CourseSolution]:
        exception = ctx.get_exception(self.path)
        if exception and exception.is_pass_override():
            logger.debug("forced override on %s", self.path)
            yield CourseSolution.from_rule(rule=self, overridden=True)
            return

        logger.debug('%s reference to course "%s"', self.path, self.course)

        yield CourseSolution.from_rule(rule=self)

    def estimate(self, *, ctx: 'RequirementContext') -> int:
        logger.debug('CourseRule.estimate: 1')
        return 1

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if self._has_potential(ctx=ctx):
            logger.debug('%s has potential: yes', self.path)
            return True
        else:
            logger.debug('%s has potential: no', self.path)
            return False

    def _has_potential(self, *, ctx: 'RequirementContext') -> bool:
        if ctx.get_exception(self.path) is not None:
            return True

        try:
            next(ctx.find_other_courses(ap=self.ap, ib=self.ib, cal=self.cal))
            return True
        except StopIteration:
            pass

        if ctx.find_course(self.course) is not None:
            return True

        return False

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        exception = ctx.get_exception(self.path)
        if exception and isinstance(exception, InsertionException):
            match = ctx.find_course_by_clbid(exception.clbid)
        else:
            match = ctx.find_course(self.course)

        return [match] if match else []
