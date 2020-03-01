from typing import Dict, List, Iterator, Collection, Optional
import logging

import attr

from ..base.bases import Rule
from ..base.course import BaseCourseRule
from ..constants import Constants
from ..context import RequirementContext
from ..data.course import CourseInstance
from ..data.course_enums import GradeOption
from ..grades import str_to_grade_points
from ..solution.course import CourseSolution

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseRule(Rule, BaseCourseRule):
    auto_waived: bool = False

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "course" in data:
            return True
        if "ap" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: List[str]) -> 'CourseRule':
        course = data.get('course', None)
        ap = data.get('ap', None)
        name = data.get('name', None)
        institution = data.get('institution', None)
        min_grade = data.get('grade', None)
        grade_option = data.get('grade_option', None)
        clbid = data.get('clbid', None)
        inserted = data.get('inserted', False)
        auto_waived = data.get('auto_waived', False)

        path_name = f"*{course or ap or name}"
        path_inst = f"(institution={institution})" if institution else ""
        path_grade = f"(grade >= {min_grade})" if min_grade else ""
        path = [*path, f"{path_name}{path_inst}{path_grade}"]

        from_claimed = data.get("from_claimed", False)
        allow_claimed = data.get("allow_claimed", False)

        if from_claimed:
            allow_claimed = True

        allowed_keys = {
            'course', 'grade', 'allow_claimed', 'from_claimed',
            'hidden', 'ap', 'grade_option', 'institution',
            'name', 'clbid', 'inserted', 'waived',
        }
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        return CourseRule(
            course=course,
            hidden=data.get("hidden", False),
            grade=str_to_grade_points(min_grade) if min_grade is not None else None,
            grade_option=GradeOption(grade_option) if grade_option else None,
            allow_claimed=allow_claimed,
            from_claimed=from_claimed,
            path=tuple(path),
            institution=institution,
            name=name,
            ap=ap,
            clbid=clbid,
            inserted=inserted,
            auto_waived=auto_waived,
        )

    def validate(self, *, ctx: RequirementContext) -> None:
        assert self.course or self.ap or (self.institution and self.name)

    def get_requirement_names(self) -> List[str]:
        return []

    def get_required_courses(self, *, ctx: RequirementContext) -> Collection[CourseInstance]:
        if self.from_claimed:
            return tuple()

        matches = self.all_matches(ctx=ctx)

        if len(matches) == 1:
            return tuple(matches)

        return tuple()

    def exclude_required_courses(self, to_exclude: Collection[CourseInstance]) -> 'CourseRule':
        return self

    def solutions(self, *, ctx: RequirementContext, depth: Optional[int] = None) -> Iterator[CourseSolution]:
        if self.auto_waived or ctx.exceptions.get_waive_exception(self.path):
            logger.debug("forced override on %s", self.path)
            yield CourseSolution.from_rule(rule=self, overridden=True)
            return

        logger.debug('%s reference to course "%s"', self.path, self.course)

        yield CourseSolution.from_rule(rule=self)

    def estimate(self, *, ctx: RequirementContext, depth: Optional[int] = None) -> int:
        return 1

    def has_potential(self, *, ctx: RequirementContext) -> bool:
        if self._has_potential(ctx=ctx):
            logger.debug('%s has potential: yes', self.path)
            return True
        else:
            logger.debug('%s has potential: no', self.path)
            return False

    def _has_potential(self, *, ctx: RequirementContext) -> bool:
        if self.auto_waived or ctx.exceptions.has_exception(self.path):
            return True

        try:
            next(ctx.find_courses(rule=self))
            return True
        except StopIteration:
            return False

    def all_matches(self, *, ctx: RequirementContext) -> Collection[CourseInstance]:
        for insert in ctx.exceptions.get_insert_exceptions(self.path):
            match = ctx.find_course_by_clbid(insert.clbid)
            return [match] if match else []

        if self.from_claimed:
            return []

        return list(ctx.find_courses(rule=self))
