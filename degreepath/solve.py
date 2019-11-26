from typing import Optional, Dict, List, TYPE_CHECKING
from .stringify import summarize

if TYPE_CHECKING:  # pragma: no cover
    from .claim import Claim  # noqa: F401
    from .base import Result, Rule  # noqa: F401
    from .context import RequirementContext


# def foo(rule):
#     print(str(rule.__class__))
#     for slot in sorted(set(slot for cls in type(rule).__mro__ for slot in rule.__slots__)):
#         if slot == 'result':
#             foo(rule.result)
#         else:
#             print(str(slot) + ' = ' + str(getattr(rule, slot)))
    # return '\n'.join([str(rule.__class__)] + [str(item) + ' = ' + str(getattr(rule, item)) for item in sorted(rule.__slots__)])


def find_best_solution(*, rule: 'Rule', ctx: 'RequirementContext', reset_claims: bool = False) -> Optional['Result']:
    # if rule.path == ('$', '.count', '[5]', '%Sequence'):
    #     print(' -> '.join(rule.path))
    #     print(rule)
    #     # print(foo(rule))
    #     print()

    result = None

    claims: Dict[str, List['Claim']] = dict()
    if reset_claims:
        claims = ctx.claims
        ctx.reset_claims()

    for s in rule.solutions(ctx=ctx):
        tmp_result = s.audit(ctx=ctx)

        if rule.path == ('$', '.count', '[5]', '%Sequence'):
            print('\n'.join(summarize(
                result=tmp_result.to_dict(),
                transcript=ctx.transcript(),
                count=0,
                elapsed='0',
                iterations=[],
                claims={},
            )))

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
