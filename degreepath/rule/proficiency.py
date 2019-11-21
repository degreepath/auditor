import attr
from typing import Dict, List, Iterator, Collection, Optional, TYPE_CHECKING
import logging

from ..base import Rule, BaseProficiencyRule
from ..constants import Constants
from ..solution.proficiency import ProficiencySolution
from .course import CourseRule

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ProficiencyRule(Rule, BaseProficiencyRule):
    course: CourseRule

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "proficiency" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: List[str]) -> 'ProficiencyRule':
        proficiency = data['proficiency']

        path = [*path, f"proficiency={proficiency}"]

        allowed_keys = {'proficiency', 'course'}
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        return ProficiencyRule(
            proficiency=proficiency,
            course=CourseRule.load(data['course'], c=c, path=path),
            path=tuple(path),
        )

    def validate(self, *, ctx: 'RequirementContext') -> None:
        pass

    def get_requirement_names(self) -> List[str]:
        return []

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[ProficiencySolution]:
        if ctx.get_waive_exception(self.path):
            logger.debug("forced override on %s", self.path)
            yield ProficiencySolution.overridden_from_rule(rule=self)
            return

        logger.debug('%s reference to proficiency "%s"', self.path, self.proficiency)
        course_solution = next(self.course.solutions(ctx=ctx))

        yield ProficiencySolution.from_rule(rule=self, course_solution=course_solution)

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        return True

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        return self.course.all_matches(ctx=ctx)
