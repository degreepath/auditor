from typing import Optional, TYPE_CHECKING
from decimal import Decimal
import logging

from .status import WAIVED_AND_DONE

if TYPE_CHECKING:  # pragma: no cover
    from .claim import Claim  # noqa: F401
    from .base import Result, Rule  # noqa: F401
    from .context import RequirementContext

logger = logging.getLogger(__name__)


def find_best_solution(*, rule: 'Rule', ctx: 'RequirementContext', merge_claims: bool = False) -> Optional['Result']:
    logger.debug('solving rule at %s', rule.path)

    best_result: Optional['Result'] = None
    best_result_index: Optional[int] = None
    best_rank: Decimal = Decimal(0)

    original_claims = ctx.claims

    ctx.claims = original_claims.empty()

    for this_index, s in enumerate(rule.solutions(ctx=ctx)):
        ctx.claims = original_claims.empty()

        this_result = s.audit(ctx=ctx)
        this_rank, _this_max_rank = this_result.rank()
        this_status = this_result.status()

        if best_result is None:
            best_result = this_result
            best_rank = this_rank
            best_result_index = this_index

        if this_rank > best_rank:
            best_result = this_result
            best_rank = this_rank
            best_result_index = this_index

        if this_status in WAIVED_AND_DONE:
            best_result = this_result
            best_rank = this_rank
            best_result_index = this_index
            break

    solved_claims = ctx.claims

    if merge_claims and solved_claims.has_claims():
        ctx.claims = original_claims.merge(solved_claims)

    logger.debug('rule at %s solved: rank %s, iteration %s', rule.path, best_rank, best_result_index)

    return best_result
