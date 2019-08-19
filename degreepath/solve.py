from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from .base import Result, Rule  # noqa: F401
    from .context import RequirementContext


def find_best_solution(*, rule: 'Rule', ctx: 'RequirementContext') -> Optional['Result']:
    result = None

    for s in rule.solutions(ctx=ctx):
        tmp_result = s.audit(ctx=ctx)

        if result is None:
            result = tmp_result

        if result.rank() < tmp_result.rank():
            result = tmp_result

        if tmp_result.ok():
            result = tmp_result

    return result
