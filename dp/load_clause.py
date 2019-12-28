from typing import Dict, Sequence, Optional, Any, Mapping, Iterator, TYPE_CHECKING
from .constants import Constants

from .clause import Clause, AndClause, OrClause, SingleClause
from .operator import Operator
from .solve import find_best_solution

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext  # noqa: F401


def load_clause(
    data: Dict[str, Any],
    *,
    c: Constants,
    ctx: Optional['RequirementContext'] = None,
    allow_boolean: bool = True,
    forbid: Sequence[Operator] = tuple(),
) -> Optional[Clause]:
    if not isinstance(data, Mapping):
        raise Exception(f'expected {data} to be a dictionary')

    if not allow_boolean and ('$and' in data or '$or' in data):
        raise ValueError('$and / $or clauses are not allowed here')

    if "$and" in data:
        assert len(data.keys()) == 1
        clauses = tuple(load_clauses(data['$and'], c=c, ctx=ctx, allow_boolean=allow_boolean, forbid=forbid))
        assert len(clauses) >= 1
        return AndClause(children=clauses)

    elif "$or" in data:
        assert len(data.keys()) == 1
        clauses = tuple(load_clauses(data['$or'], c=c, ctx=ctx, allow_boolean=allow_boolean, forbid=forbid))
        assert len(clauses) >= 1
        return OrClause(children=clauses)

    elif "$if" in data:
        assert ctx, '$if clauses are not allowed here'

        from .rule.query import QueryRule
        rule = QueryRule.load(data['$if'], c=c, path=[], ctx=ctx)

        with ctx.fresh_claims():
            s = find_best_solution(rule=rule, ctx=ctx)

        when_yes = load_clause(data['$then'], c=c, ctx=ctx, allow_boolean=allow_boolean, forbid=forbid)
        when_no = load_clause(data['$else'], c=c, ctx=ctx, allow_boolean=allow_boolean, forbid=forbid) if '$else' in data else None

        if not s:
            return when_no

        if not s.ok():
            return when_no

        return when_yes

    assert len(data.keys()) == 1, "only one key allowed in single-clauses"

    clauses = tuple(SingleClause.load(key, value, c=c, forbid=forbid, ctx=ctx) for key, value in data.items())

    if len(clauses) == 1:
        return clauses[0]

    return AndClause(children=clauses)


def load_clauses(
    data: Sequence[Any],
    *,
    c: Constants,
    ctx: Optional['RequirementContext'] = None,
    allow_boolean: bool = True,
    forbid: Sequence[Operator] = tuple(),
) -> Iterator[Clause]:
    for clause in data:
        loaded = load_clause(clause, c=c, allow_boolean=allow_boolean, forbid=forbid, ctx=ctx)
        if not loaded:
            continue
        yield loaded
