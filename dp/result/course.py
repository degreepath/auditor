import attr
from typing import Optional, List

from ..base import Result, BaseCourseRule
from ..claim import Claim


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseResult(Result, BaseCourseRule):
    # we don't need to include this in the output, because
    # it's returned automatically under the "claims" key
    claim_attempt: Optional[Claim]

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
            year=solution.year,
            term=solution.term,
            section=solution.section,
            sub_type=solution.sub_type,
        )

    def claims(self) -> List[Claim]:
        if self.claim_attempt and self.claim_attempt.failed is False:
            return [self.claim_attempt]
        else:
            return []

    def is_waived(self) -> bool:
        if self.claim_attempt is not None and self.claim_attempt.failed is True:
            return False

        return self.inserted or self.overridden
