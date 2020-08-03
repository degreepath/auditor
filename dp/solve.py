from typing import Optional, Dict, List, TYPE_CHECKING
from decimal import Decimal
import logging

from .status import WAIVED_AND_DONE

if TYPE_CHECKING:  # pragma: no cover
    from .claim import Claim  # noqa: F401
    from .base import Result, Rule  # noqa: F401
    from .context import RequirementContext

logger = logging.getLogger(__name__)


def find_best_solution(*, rule: 'Rule', ctx: 'RequirementContext', merge_claims: bool = False) -> Optional['Result']:
    logger.debug('solving rule: start; at %s', rule.path)

    best_result: Optional['Result'] = None
    best_result_index: Optional[int] = None
    best_rank: Decimal = Decimal(0)

    claims: Dict[str, List['Claim']] = dict()
    if merge_claims:
        claims = ctx.claims

    with ctx.fresh_claims():
        for this_index, s in enumerate(rule.solutions(ctx=ctx)):
            inner_ctx = ctx.with_empty_claims()

            this_result = s.audit(ctx=inner_ctx)
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

    if merge_claims and inner_ctx:
        ctx.set_claims({**claims, **inner_ctx.claims})

    logger.debug('solving rule: done; at %s solved: rank %s, iteration %s', rule.path, best_rank, best_result_index)

    return best_result
