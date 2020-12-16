import attr
from typing import Optional
import logging

from ..base import Base, Result, BaseRequirementRule

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RequirementResult(Result, BaseRequirementRule):
    @staticmethod
    def from_solution(
        *,
        solution: BaseRequirementRule,
        result: Optional[Base],
        overridden: bool = False,
    ) -> 'RequirementResult':
        return RequirementResult(
            name=solution.name,
            message=solution.message,
            is_audited=solution.is_audited,
            is_contract=solution.is_contract,
            path=solution.path,
            disjoint=solution.disjoint,
            in_gpa=solution.in_gpa,
            result=result,
            overridden=overridden,
        )
