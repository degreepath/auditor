from typing import Optional, Dict, Set, TYPE_CHECKING


if TYPE_CHECKING:
    from .claim import Claim  # noqa: F401
    from .base import Result, Rule  # noqa: F401
    from .context import RequirementContext


def find_best_solution(*, rule: 'Rule', ctx: 'RequirementContext', reset_claims: bool = False) -> Optional['Result']:
    result = None

    claims: Dict[str, Set['Claim']] = dict()
    if reset_claims:
        claims = ctx.claims
        ctx.reset_claims()

    for s in rule.solutions(ctx=ctx):
        tmp_result = s.audit(ctx=ctx)

        if result is None:
            result = tmp_result

        if tmp_result.ok():
            result = tmp_result
            break

        if result.rank() < tmp_result.rank():
            result = tmp_result

        if reset_claims:
            ctx.reset_claims()

    if reset_claims:
        ctx.set_claims(claims)

    return result
