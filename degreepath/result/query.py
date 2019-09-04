import attr
from typing import Tuple, Sequence, List

from .assertion import AssertionResult
from ..base import Result, BaseQueryRule, Summable, BaseAssertionRule
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
        inserted: Tuple[str, ...] = tuple(),
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
            inserted=inserted,
        )

    def only_failed_claims(self) -> Sequence[ClaimAttempt]:
        return self.failed_claims

    def all_assertions(self) -> Sequence[BaseAssertionRule]:
        return self.resolved_assertions

    def claims(self) -> List[ClaimAttempt]:
        return list(self.successful_claims)

    def was_overridden(self) -> bool:
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.success is True

    def rank(self) -> Summable:
        return sum(a.rank() for a in self.resolved_assertions)

    def max_rank(self) -> Summable:
        return sum(a.max_rank() for a in self.resolved_assertions)
