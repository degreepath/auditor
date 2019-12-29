from typing import Optional, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .claim import Claim  # noqa: F401
    from .base import Result, Rule  # noqa: F401
    from .context import RequirementContext


def find_best_solution(*, rule: 'Rule', ctx: 'RequirementContext', merge_claims: bool = False) -> Optional['Result']:
    result: Optional['Result'] = None

    claims: Dict[str, List['Claim']] = dict()
    if merge_claims:
        claims = ctx.claims

    with ctx.fresh_claims():
        for s in rule.solutions(ctx=ctx):
            inner_ctx = ctx.with_empty_claims()
            tmp_result = s.audit(ctx=inner_ctx)

            if result is None:
                result = tmp_result

            if tmp_result.rank() > result.rank():
                result = tmp_result

            if tmp_result.ok():
                result = tmp_result
                break

    if merge_claims and inner_ctx:
        ctx.set_claims({**claims, **inner_ctx.claims})

    return result
