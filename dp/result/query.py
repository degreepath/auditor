import attr
from typing import Tuple, Sequence, List

from ..assertion_clause import AnyAssertion
from ..base import Result, BaseQueryRule
from ..claim import Claim


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class QueryResult(Result, BaseQueryRule):
    @staticmethod
    def from_solution(
        *,
        solution: BaseQueryRule,
        assertions: Tuple[AnyAssertion, ...],
        successful_claims: Tuple[Claim, ...],
        failed_claims: Tuple[Claim, ...],
        overridden: bool = False,
    ) -> 'QueryResult':
        return QueryResult(
            source=solution.source,
            data_type=solution.data_type,
            assertions=assertions,
            limit=solution.limit,
            where=solution.where,
            include_failed=solution.include_failed,
            allow_claimed=solution.allow_claimed,
            attempt_claims=solution.attempt_claims,
            record_claims=solution.record_claims,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            path=solution.path,
            overridden=overridden,
            inserted=solution.inserted,
            force_inserted=solution.force_inserted,
            output=solution.output,
            excluded_clbids=solution.excluded_clbids,
            load_potentials=solution.load_potentials,
        )

    def only_failed_claims(self) -> Sequence[Claim]:
        return self.failed_claims

    def claims(self) -> List[Claim]:
        return list(self.successful_claims)
