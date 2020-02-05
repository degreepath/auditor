import attr
from typing import Tuple, Sequence, List, Union, TYPE_CHECKING

from .assertion import AssertionResult
from ..base import Result, BaseQueryRule
from ..claim import ClaimAttempt

if TYPE_CHECKING:  # pragma: no cover
    from ..rule.assertion import AssertionRule  # noqa: F401
    from ..rule.conditional_assertion import ConditionalAssertionRule  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QueryResult(Result, BaseQueryRule):
    successful_claims: Tuple[ClaimAttempt, ...]
    failed_claims: Tuple[ClaimAttempt, ...]
    resolved_assertions: Tuple[AssertionResult, ...]
    overridden: bool

    @staticmethod
    def from_solution(
        *,
        solution: BaseQueryRule,
        resolved_assertions: Tuple[AssertionResult, ...],
        successful_claims: Tuple[ClaimAttempt, ...],
        failed_claims: Tuple[ClaimAttempt, ...],
        overridden: bool = False,
    ) -> 'QueryResult':
        return QueryResult(
            source=solution.source,
            assertions=solution.assertions,
            limit=solution.limit,
            where=solution.where,
            allow_claimed=solution.allow_claimed,
            attempt_claims=solution.attempt_claims,
            record_claims=solution.record_claims,
            resolved_assertions=resolved_assertions,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            path=solution.path,
            overridden=overridden,
            inserted=solution.inserted,
            force_inserted=solution.force_inserted,
        )

    def only_failed_claims(self) -> Sequence[ClaimAttempt]:
        return self.failed_claims

    def all_assertions(self) -> Sequence[Union['AssertionRule', 'ConditionalAssertionRule', AssertionResult]]:
        return self.resolved_assertions

    def claims(self) -> List[ClaimAttempt]:
        return list(self.successful_claims)

    def waived(self) -> bool:
        return self.overridden
