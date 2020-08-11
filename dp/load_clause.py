from typing import Dict, Sequence, Optional, Any, Mapping, Iterator, Union, Tuple, Callable, TYPE_CHECKING
from collections.abc import Iterable
from decimal import Decimal

from .clause import Clause, AndClause, OrClause, SingleClause
from .constants import Constants
from .data.course_enums import GradeOption, GradeCode
from .op import Operator
from .solve import find_best_solution
from .status import ResultStatus

if TYPE_CHECKING:  # pragma: no cover
    from .context import RequirementContext  # noqa: F401

KEY_LOOKUP = {
    "subjects": "subject",
    "attribute": "attributes",
    "gereq": "gereqs",
}


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
        assert ctx, '$if clauses are not allowed here (no context provided)'

        if '$or' in data['$if']:
            rule_pass = any(check_simple_clause(condition, ctx=ctx) for condition in data['$if']['$or'])

        elif '$all' in data['$if']:
            rule_pass = all(check_simple_clause(condition, ctx=ctx) for condition in data['$if']['$all'])

        else:
            from .rule.query import QueryRule
            rule = QueryRule.load(data['$if'], c=c, path=[], ctx=ctx)

            with ctx.fresh_claims():
                s = find_best_solution(rule=rule, ctx=ctx)

            rule_pass = True
            if not s or s.status() not in (ResultStatus.Done, ResultStatus.Waived, ResultStatus.PendingCurrent, ResultStatus.PendingRegistered):
                rule_pass = False

        when_yes = load_clause(data['$then'], c=c, ctx=ctx, allow_boolean=allow_boolean, forbid=forbid)

        when_no = None
        when_no_clause = data.get('$else', None)
        if when_no_clause:
            when_no = load_clause(when_no_clause, c=c, ctx=ctx, allow_boolean=allow_boolean, forbid=forbid)

        if rule_pass:
            return when_yes
        else:
            return when_no

    assert len(data.keys()) == 1, "only one key allowed in single-clauses"

    clauses = tuple(load_single_clause(key, value, c=c, forbid=forbid, ctx=ctx) for key, value in data.items())

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


def load_single_clause(
    key: str,
    value: Dict,
    *,
    c: Constants,
    ctx: Optional['RequirementContext'] = None,
    forbid: Sequence[Operator] = tuple(),
) -> 'SingleClause':
    assert isinstance(value, Dict), TypeError(f'expected {value!r} to be a dictionary')

    # TODO: replace with attribute whitelist based on input type
    key = KEY_LOOKUP.get(key, key)

    operators = [k for k in value.keys() if k in ('$eq', '$neq', '$in', '$nin', '$gte', '$gt', '$lte', '$lt')]
    assert len(operators) == 1, f"{value}"
    op = operators[0]
    operator = Operator(op)
    assert operator not in forbid, ValueError(f'operator {operator} is forbidden here - {forbid}')

    expected_value, expected_verbatim = load_expected_value(key=key, value=value, op=op, ctx=ctx, c=c)

    expected_value_covid = None
    if '$during_covid' in value:
        expected_value_covid, _ = load_expected_value(key=key, value=value, op='$during_covid', ctx=ctx, c=c)
        assert expected_value_covid is not None

    # forbid all null values in tuples or single-value clauses
    if operator in (Operator.In, Operator.NotIn):
        assert all(v is not None for v in expected_value)
    else:
        assert expected_value is not None

    at_most = value.get('at_most', False)
    assert type(at_most) is bool

    return SingleClause(
        key=key,
        expected=expected_value,
        operator=operator,
        expected_verbatim=expected_verbatim,
        at_most=at_most,
        label=value.get('label', None),
        treat_in_progress_as_pass=value.get('treat_in_progress_as_pass', False),
        state=ResultStatus.Empty,
        during_covid=expected_value_covid,
    )


def load_expected_value(*, key: str, value: Dict, op: str, ctx: Optional['RequirementContext'], c: Constants) -> Tuple[Any, Any]:
    expected_value = value[op]
    if isinstance(expected_value, list):
        expected_value = tuple(expected_value)
    elif isinstance(expected_value, float):
        expected_value = Decimal(str(expected_value))

    expected_value_diff = compute_single_clause_diff(value.get('$ifs', {}), ctx=ctx)
    if expected_value_diff:
        expected_value += expected_value_diff

    expected_verbatim = expected_value

    allowed_types = (bool, str, tuple, int, Decimal)
    assert type(expected_value) in allowed_types, ValueError(f"expected_value should be one of {allowed_types!r}, not {type(expected_value)}")

    if type(expected_value) == str:
        expected_value = c.get_by_name(expected_value)
    elif isinstance(expected_value, tuple):
        expected_value = tuple(c.get_by_name(v) for v in expected_value)
        expected_value = tuple(flatten(expected_value))
    elif isinstance(expected_value, Iterable):
        raise TypeError(f'unexpected type {type(expected_value)} for {expected_value!r}')

    expected_value = process_clause_value(expected_value, key=key)

    return expected_value, expected_verbatim


def compute_single_clause_diff(conditionals: Mapping[str, str], *, ctx: Optional['RequirementContext']) -> Decimal:
    diff_value = Decimal(0)

    for cond, cond_action in conditionals.items():
        conditions = cond.split(' + ')

        if not all(check_simple_clause(condition, ctx=ctx) for condition in conditions):
            continue

        cond_action_mode, cond_action_inc = cond_action.split(' ', maxsplit=1)

        if cond_action_mode == '+':
            diff_value += Decimal(cond_action_inc)
        else:
            raise TypeError(f'unsupported single_clause_diff mode {cond_action_mode}')

    return diff_value


def check_simple_clause(condition: str, *, ctx: Optional['RequirementContext']) -> bool:
    '''
    > has-area-code(716) + has-area-code(711)
    > has-area-code(711) + passed-proficiency-exam(Keyboard Level IV)
    '''
    key = condition.split('(')[0]

    if key == 'has-area-code':
        assert ctx

        area_code = condition.split('(')[1].rstrip(')').strip()
        return ctx.has_area_code(area_code)

    elif key == 'has-course':
        assert ctx

        course_ident = condition.split('(')[1].rstrip(')').strip()
        return ctx.has_course(course_ident)

    elif key == 'has-ip-course':
        assert ctx

        course_ident = condition.split('(')[1].rstrip(')').strip()
        return ctx.has_ip_course(course_ident)

    elif key == 'has-completed-course':
        assert ctx

        course_ident = condition.split('(')[1].rstrip(')').strip()
        return ctx.has_completed_course(course_ident)

    elif key == 'passed-proficiency-exam':
        # note: this was prototyped for BM Performance, but they
        # actually want to check for proficiency _exams_ and make you
        # take extra credits if you tested out of the courses, so this
        # check needs to be extended to check for proficiency exams -
        # we don't currently store exam status in MusicProficiencies,
        # just whether you have the proficiency or not.
        assert ctx

        proficiency = condition.split('(')[1].rstrip(')').strip()

        return ctx.music_proficiencies.status(of=proficiency) is ResultStatus.Done

    else:
        raise TypeError(f"unknown $ifs key {key}")


def flatten(lst: Iterable) -> Iterator:
    for el in lst:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def process_clause__grade(expected_value: Any) -> Union[GradeCode, Tuple[GradeCode, ...]]:
    if not type(expected_value) is str and isinstance(expected_value, Iterable):
        return tuple(GradeCode(v) for v in expected_value)
    else:
        return GradeCode(expected_value)


def process_clause__grade_option(expected_value: Any) -> GradeOption:
    return GradeOption(expected_value)


def process_clause__credits(expected_value: Any) -> Decimal:
    return Decimal(expected_value)


def process_clause__gpa(expected_value: Any) -> Decimal:
    return Decimal(expected_value)


clause_value_process: Mapping[str, Callable[[Sequence[Any]], Union[GradeOption, GradeCode, Tuple[GradeCode, ...], Decimal, Tuple[Decimal, ...]]]] = {
    'grade': process_clause__grade,
    'grade_option': process_clause__grade_option,
    'credits': process_clause__credits,
    'gpa': process_clause__gpa,
}


def process_clause_value(expected_value: Any, *, key: str) -> Union[Any, GradeOption, GradeCode, Tuple[GradeCode, ...], Decimal, Tuple[Decimal, ...]]:
    if key in clause_value_process:
        return clause_value_process[key](expected_value)

    return expected_value
