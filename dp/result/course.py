import attr
from typing import Optional, List

from ..base import Result, BaseCourseRule
from ..claim import Claim


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseResult(Result, BaseCourseRule):
    claim_attempt: Optional[Claim]
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseCourseRule,
        claim_attempt: Optional[Claim] = None,
        overridden: bool = False,
    ) -> 'CourseResult':
        return CourseResult(
            course=solution.course,
            clbid=solution.clbid,
            hidden=solution.hidden,
            grade=solution.grade,
            grade_option=solution.grade_option,
            allow_claimed=solution.allow_claimed,
            claim_attempt=claim_attempt,
            path=solution.path,
            overridden=overridden,
            ap=solution.ap,
            institution=solution.institution,
            name=solution.name,
            inserted=solution.inserted,
            optional=solution.optional,
        )

    def claims(self) -> List[Claim]:
        if self.claim_attempt and self.claim_attempt.failed is False:
            return [self.claim_attempt]
        else:
            return []

    def waived(self) -> bool:
        return self.inserted or self.overridden
