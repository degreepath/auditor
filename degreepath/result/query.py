import attr
from typing import Tuple, Dict, Any, List
from .assertion import AssertionResult

from ..base import Result, BaseQueryRule
from ..claim import ClaimAttempt


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QueryResult(Result, BaseQueryRule):
    successful_claims: Tuple[ClaimAttempt, ...]
    failed_claims: Tuple[ClaimAttempt, ...]
    resolved_assertions: Tuple[AssertionResult, ...]
    success: bool
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseQueryRule,
        resolved_assertions: Tuple[AssertionResult, ...],
        successful_claims: Tuple[ClaimAttempt, ...],
        failed_claims: Tuple[ClaimAttempt, ...],
        success: bool,
        overridden: bool = False,
    ) -> 'QueryResult':
        return QueryResult(
            source=solution.source,
            source_type=solution.source_type,
            source_repeats=solution.source_repeats,
            assertions=solution.assertions,
            limit=solution.limit,
            where=solution.where,
            allow_claimed=solution.allow_claimed,
            attempt_claims=solution.attempt_claims,
            resolved_assertions=resolved_assertions,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=success,
            path=solution.path,
            overridden=overridden,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "failures": [c.to_dict() for c in self.failed_claims],
            "assertions": [a.to_dict() for a in self.resolved_assertions],
        }

    def claims(self) -> List[ClaimAttempt]:
        return list(self.successful_claims)

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.success is True

    def rank(self) -> int:
        return sum(a.rank() for a in self.resolved_assertions)

    def max_rank(self) -> int:
        return sum(a.max_rank() for a in self.resolved_assertions)
