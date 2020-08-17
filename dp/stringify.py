from typing import List, Iterator, Any, Dict, Sequence, Set, Optional
from .data.course import CourseInstance
from .data.course_enums import CourseType
from .op import str_operator
from .ms import pretty_ms
from .status import PassingStatusValues, WAIVED_AND_DONE
import json

WAIVED_AND_DONE_VALUES = [v.value for v in WAIVED_AND_DONE]


def summarize(
    *,
    transcript: Sequence[CourseInstance],
    result: Dict[str, Any],
    final_index: Optional[int] = None,
    count: int,
    gen_count: int = 0,
    elapsed: str,
    avg_iter_ms: float,
    show_paths: bool = True,
    show_ranks: bool = True,
    claims: Dict[str, List[List[str]]],
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    avg_iter_time = pretty_ms(avg_iter_ms, format_sub_ms=True)
    mapped_transcript = {c.clbid: c for c in transcript}
    endl = "\n"

    if count == gen_count:
        yield f"{count:,} checked in {elapsed} (audit #{final_index}); avg {avg_iter_time} per check"
    else:
        yield f"{count:,} checked (of {gen_count:,} generated) in {elapsed} (audit #{final_index}); avg {avg_iter_time} per check"

    yield endl
    yield endl

    yield endl.join(print_result(result, transcript=mapped_transcript, show_paths=show_paths, show_ranks=show_ranks, only_path=only_path))

    if only_path:
        return

    yield endl
    yield endl

    yield "Claimed courses:"
    yield endl

    for clbid, claimant_paths in claims.items():
        for path in claimant_paths:
            path = [f"%{result['name']}", *path]
            label = f'{mapped_transcript[clbid].course_with_term()} "{mapped_transcript[clbid].name}"'
            yield f"  - {label} at {claimed_path(path)}"
            yield endl


def claimed_path(path: List[str]) -> str:
    return ' > '.join(chunk[1:] for chunk in path if chunk.startswith('%'))


def print_result(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    inserted: Sequence[str] = tuple(),
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if rule["type"] == "area":
        yield from print_area(rule, transcript, indent, show_paths, show_ranks, only_path=only_path)

    elif rule["type"] == "course":
        yield from print_course(rule, transcript, indent, show_paths, show_ranks, only_path=only_path)

    elif rule["type"] == "count":
        yield from print_count(rule, transcript, indent, show_paths, show_ranks, only_path=only_path)

    elif rule["type"] == "query":
        yield from print_query(rule, transcript, indent, show_paths, show_ranks, only_path=only_path)

    elif rule["type"] == "requirement":
        yield from print_requirement(rule, transcript, indent, show_paths, show_ranks, only_path=only_path)

    elif rule["type"] == "assertion":
        yield from print_assertion(rule, transcript, indent, show_paths, show_ranks, inserted=inserted, only_path=only_path)

    elif rule["type"] == "conditional-assertion":
        yield from print_conditional_assertion(rule, transcript, indent, show_paths, show_ranks, inserted=inserted, only_path=only_path)

    elif rule["type"] == "proficiency":
        yield from print_proficiency(rule, transcript, indent, show_paths, show_ranks, only_path=only_path)

    else:
        yield json.dumps(rule, indent=2)


def print_path(rule: Dict[str, Any], indent: int) -> Iterator[str]:
    prefix = " " * indent

    yield f"{prefix}{json.dumps(rule['path'])}"


def calculate_emoji(rule: Dict[str, Any]) -> str:
    if rule["status"] == "waived":
        return "💜"
    elif rule["status"] == "done":
        return "💚"
    elif rule["status"] == "pending-current":
        return "💖"
    elif rule["status"] == "pending-registered":
        return "🧡"
    elif rule["status"] == "needs-more-items":
        return "💙"
    elif rule["status"] == "pending-approval":
        return "❓"
    elif rule["status"] == "empty":
        return "🌀"
    else:
        return "🚫️"


def print_area(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    title = f"{rule['name']!r} audit status: {rule['status']}."
    rank = f"rank {rule['rank']} of {rule['max_rank']}"
    gpa = f"gpa: {rule['gpa']}"

    yield f"{title} ({rank}; {gpa})"

    if rule['limit']:
        yield "Subject to these limits:"
        for limit in rule['limit']:
            yield str_limit(limit)

    yield ""

    yield from print_result(rule['result'], transcript, show_ranks=show_ranks, show_paths=show_paths, only_path=only_path)


def emojify_course(course: Optional[CourseInstance], status: Optional[str] = None) -> str:
    if status == "waived" and course:
        return "💜 [ovr]"
    elif status == "waived":
        return "💜 [wvd]"
    elif course is None:
        return "🌀      "
    elif course.is_incomplete:
        return "⛔️ [dnf]"
    elif course.is_in_progress_this_term:
        return "💖 [ip!]"
    elif course.is_in_progress_in_future:
        return "🧡 [ip-]"
    elif course.is_in_progress:
        return "💙 [ip?]"
    elif course.is_repeat:
        return "💕 [rep]"
    elif course:
        return "💚 [ ok]"
    else:
        return "!!!!!!! "


def print_course(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({float(rule['rank']):.4g}|{rule['max_rank']}|{'t' if rule['status'] in PassingStatusValues else 'f'}) "

    if len(rule["claims"]):
        claim = rule["claims"][0]
        course = transcript.get(claim["clbid"], None)
    else:
        course = None

    status = emojify_course(course, rule["status"])

    display_course = rule['course']
    if rule["status"] == "waived" and course:
        display_course = f"{course.course().strip()} {course.name}"
    elif rule["status"] != "waived" and course and course.course_type is CourseType.AP:
        display_course = course.name
    elif not rule["course"] and rule["ap"] != "":
        display_course = rule["ap"]

    institution = ""
    if rule['institution']:
        institution = f" [{rule['institution']}]"

    yield f"{prefix}{status} {display_course}{institution}"


def print_proficiency(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({float(rule['rank']):.4g}|{rule['max_rank']}|{'t' if rule['status'] in PassingStatusValues else 'f'}) "

    status = "🌀      "
    if rule["status"] == 'waived':
        status = "💜 [wvd]"
    elif rule["status"] == 'done':
        status = "💚 [ ok]"

    yield f"{prefix}{status} Proficiency={rule['proficiency']}"

    if rule['course']['status'] in WAIVED_AND_DONE_VALUES:
        yield from print_course(rule['course'], transcript, indent + 4, show_paths, show_ranks)


def print_count(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({float(rule['rank']):.4g}|{rule['max_rank']}|{'t' if rule['status'] in PassingStatusValues else 'f'}) "

    emoji = calculate_emoji(rule)

    size = len(rule["items"])
    if rule["count"] == 1 and size == 2:
        descr = f"either of (these {size})"
    elif rule["count"] == 2 and size == 2:
        descr = f"both of (these {size})"
    elif rule["count"] == size:
        descr = f"all of (these {size})"
    elif rule["count"] == 1:
        descr = f"any of (these {size})"
    else:
        descr = f"at least {rule['count']} of {size}"

    ok_count = len([r for r in rule["items"] if r["status"] in WAIVED_AND_DONE_VALUES])
    descr += f" (ok: {ok_count}; need: {rule['count']})"

    yield f"{prefix}{emoji} {descr}"

    if rule['audit']:
        yield f'{prefix} This requirement has a post-audit [status={rule["audit_status"]}]:'

        yield f"{prefix} There must be:"
        for a in rule['audit']:
            yield from print_result(a, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths, only_path=only_path)

        yield ''

    for i, r in enumerate(rule["items"]):
        yield from print_result(r, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths, only_path=only_path)

        if size != 2 and i < len(rule['items']) - 1:
            yield ''


def print_query(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({float(rule['rank']):.4g}|{rule['max_rank']}|{'t' if rule['status'] in PassingStatusValues else 'f'}) "

    emoji = calculate_emoji(rule)

    if rule['where']:
        yield f"{prefix}{emoji} [{rule['status']}] Given courses matching {str_predicate(rule['where'])}"

    if rule['limit']:
        yield f"{prefix} Subject to these limits:"
        for limit in rule['limit']:
            yield prefix + " " + str_limit(limit)

    if rule["claims"]:
        yield f"{prefix} Matching courses:"
        for clm in rule["claims"]:
            course = transcript.get(clm["clbid"], None)
            if not course:
                yield f"{prefix}    !!!!! \"!!!!!\" ({clm['clbid']})"
                continue

            status = emojify_course(course)
            inserted_msg = "[ins] " if clm["clbid"] in rule["inserted"] else ""
            yield f"{prefix}    {inserted_msg}{status} {course.verbose()}"

    if rule["failures"]:
        yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
        for clm in rule["failures"]:
            course = transcript.get(clm["clbid"], None)
            if course:
                # conflicts = [x['claimant_path'] for x in clm['conflict_with']]
                yield f"{prefix}    {course.course()} \"{course.name}\" ({course.clbid})"
            else:
                yield f"{prefix}    !!!!! \"!!!!!\" ({clm['clbid']})"

    yield f"{prefix} There must be:"
    for a in rule['assertions']:
        yield from print_result(a, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths, inserted=rule["inserted"])


def print_requirement(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if only_path and rule['path'][:len(only_path)] != only_path:
        return

    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({float(rule['rank']):.4g}|{rule['max_rank']}|{'t' if rule['status'] in PassingStatusValues else 'f'}) "

    emoji = calculate_emoji(rule)

    yield f"{prefix}{emoji} Requirement({rule['name']}) [{rule['status']}]"
    if rule["is_audited"]:
        yield f"{prefix}    is manually audited"
        return

    if rule["result"]:
        yield from print_result(rule["result"], transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths, only_path=only_path)


def print_assertion(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    inserted: Sequence[str] = tuple(),
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    rank_prefix = ""
    if show_ranks:
        rank_prefix = f"({float(rule['rank']):.4g}|{rule['max_rank']}|{'t' if rule['status'] in PassingStatusValues else 'f'}) "
    rank_prefix_spaces = "             "

    emoji = calculate_emoji(rule)

    yield f"{prefix}{rank_prefix} - {emoji} {str_assertion(rule)} [{rule['status']}]"

    prefix += " " * 6

    if rule['where']:
        yield f"{prefix}{rank_prefix_spaces}where {str_predicate(rule['where'])}"

    resolved_items = get_resolved_items(rule)
    if resolved_items:
        yield f"{prefix}{rank_prefix_spaces}resolved items: {resolved_items}"

    resolved_clbids = get_resolved_clbids(rule)
    if resolved_clbids:
        yield f"{prefix}{rank_prefix_spaces}resolved courses:"

        ip_clbids = get_in_progress_clbids(rule)

        for clbid in resolved_clbids:
            inserted_msg = " [ins]" if clbid in inserted or clbid in rule['inserted_clbids'] else ""

            course = transcript.get(clbid, None)
            if not course:
                ip_msg = " [ip?]" if clbid in ip_clbids else ""
                yield f'{prefix}  -{ip_msg}{inserted_msg} #{int(clbid)}'
                continue

            status = emojify_course(course)
            yield f'{prefix}{rank_prefix_spaces}  -{inserted_msg} {status} {course.verbose()}'


def print_conditional_assertion(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    inserted: Sequence[str] = tuple(),
    only_path: Optional[List[str]] = None,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    yield f"{prefix}If:"
    yield from print_result(rule['condition'], transcript, indent + 4, show_paths, show_ranks, inserted)

    yield f"{prefix}Then:"
    yield from print_result(rule['when_yes'], transcript, indent + 4, show_paths, show_ranks, inserted)

    if rule['when_no']:
        yield f"{prefix}Otherwise:"
        yield from print_result(rule['when_no'], transcript, indent + 4, show_paths, show_ranks, inserted)
    else:
        yield f"{prefix}Otherwise, do nothing"


def str_predicate(clause: Dict[str, Any], *, nested: bool = False, raw_only: bool = False) -> str:
    if clause["type"] == "predicate":
        return str_single_predicate(clause, nested=nested, raw_only=raw_only)

    elif clause["type"] == "pred--or":
        text = " or ".join(str_predicate(c, nested=True, raw_only=raw_only) for c in clause["predicates"])
        if not nested:
            return text
        else:
            return f'({text})'

    elif clause["type"] == "pred--and":
        text = " and ".join(str_predicate(c, nested=True, raw_only=raw_only) for c in clause["predicates"])
        if not nested:
            return text
        else:
            return f'({text})'

    elif clause["type"] == "pred--if":
        cond = str_expression(clause['condition'])
        then = str_predicate(clause['when_true'])
        branch = clause['condition']['result']
        # print(clause)
        true_branch = 't.' if branch is True else ''
        false_branch = 'f!' if branch is False else ''
        if clause['when_false']:
            other = str_predicate(clause['when_false'])
        else:
            other = "do nothing"

        text = f"If: [{cond}] Then ({true_branch}): [{then}] Else ({false_branch}): [{other}]"

        if not nested:
            return text
        else:
            return f'({text})'

    raise Exception(f'not an expression: {clause["type"]}')


def str_single_predicate(clause: Dict[str, Any], *, nested: bool = False, raw_only: bool = False) -> str:
    key = clause["key"]

    if key == 'attributes':
        key = 'bucket'
    elif key == 'is_in_progress':
        key = 'in-progress'
    elif key == 'is_stolaf':
        key = 'from STOLAF'

    resolved_with = clause.get('resolved_with', None)
    if resolved_with is not None:
        resolved = f" [{repr(resolved_with)}]"
    else:
        resolved = ""

    expected = clause['expected']

    if raw_only:
        expected = clause.get('expected_verbatim', clause['expected'])
        postscript = ""

    if 'expected_verbatim' in clause:
        postscript = f" [via {repr(clause['expected_verbatim'])}]"
    else:
        postscript = ""

    label = clause.get('label', None)
    if label:
        postscript += f' [label: "{label}"]'

    op = str_operator(clause['operator'])

    if clause['operator'] == 'EqualTo' and expected is True:
        return f'{key}{resolved}{postscript}'
    elif clause['operator'] == 'EqualTo' and expected is False:
        return f'not "{key}"{resolved}{postscript}'

    return f'{key}{resolved} {op} {expected}{postscript}'


def str_expression(expr: Dict[str, Any], *, nested: bool = False) -> str:
    if expr["type"] == "pred-expr":
        headline = "??"
        if expr['result'] is True:
            headline = 't.'
        elif expr['result'] is False:
            headline = 'f!'
        return f"({headline} {expr['function']} {expr['argument']!r})"

    elif expr["type"] == "pred-expr--or":
        text = " or ".join(str_expression(c, nested=True) for c in expr["expressions"])
        if not nested:
            return text
        else:
            return f'({text})'

    elif expr["type"] == "pred-expr--and":
        text = " and ".join(str_expression(c, nested=True) for c in expr["expressions"])
        if not nested:
            return text
        else:
            return f'({text})'

    raise Exception(f'not a predicate expression: {expr["type"]}')


def str_assertion(clause: Dict[str, Any], *, nested: bool = False, raw_only: bool = False) -> str:
    if clause["type"] == "assertion":
        key = clause["key"]

        resolved_with = clause.get('resolved_with', None)
        if resolved_with is not None:
            resolved = f" [{repr(resolved_with)}]"
        else:
            resolved = ""

        expected = clause['expected']

        if raw_only:
            expected = clause.get('original', clause['expected'])
            postscript = ""

        if 'original' in clause:
            postscript = f" [via {repr(clause['original'])}]"
        else:
            postscript = ""

        label = clause.get('label', None)
        if label:
            postscript += f' [label: "{label}"]'

        op = str_operator(clause['operator'])

        if clause['operator'] == 'EqualTo' and expected is True:
            return f'{key}{resolved}{postscript}'
        elif clause['operator'] == 'EqualTo' and expected is False:
            return f'not "{key}"{resolved}{postscript}'

        return f'{key}{resolved} {op} {expected}{postscript}'

    elif clause["type"] == "assertion--if":
        cond = str_expression(clause['condition'])
        then = str_assertion(clause['when_true'])
        branch = clause['condition']['result']
        # print(clause)
        true_branch = 't.' if branch is True else ''
        false_branch = 'f!' if branch is False else ''
        if clause['when_false']:
            other = str_assertion(clause['when_false'])
        else:
            other = "do nothing"
        text = f"If: [{cond}] Then ({true_branch}): [{then}] Else ({false_branch}): [{other}]"

        if not nested:
            return text
        else:
            return f'({text})'

    raise Exception(f'not an assertion: {clause["type"]}')


def str_limit(limit: Dict[str, Any], *, nested: bool = False) -> str:
    if limit["type"] == "limit":
        return f"at most {limit['at_most']} {limit['at_most_what']} where {str_predicate(limit['where'])}"

    elif limit["type"] == "limit--if":
        cond = str_expression(limit['condition'])
        then = str_limit(limit['when_true'])
        branch = limit['condition']['result']
        # print(limit)
        true_branch = 't.' if branch is True else ''
        false_branch = 'f!' if branch is False else ''
        if limit['when_false']:
            other = str_limit(limit['when_false'])
        else:
            other = "do nothing"
        text = f"If: [{cond}] Then ({true_branch}): [{then}] Else ({false_branch}): [{other}]"

        if not nested:
            return text
        else:
            return f'({text})'

    raise Exception(f'not a limit: {limit["type"]}')


def get_resolved_items(clause: Dict[str, Any]) -> str:
    if clause["type"] == "assertion":
        resolved_with = clause.get('resolved', None)
        if resolved_with is not None:
            return str(sorted(clause.get('resolved_items', [])))
        else:
            return ""
    elif clause["type"] == "assertion--if":
        items = " conditional assertion "
        return f'({items})'

    raise Exception('not a clause')


def get_resolved_clbids(clause: Dict[str, Any]) -> List[str]:
    if clause["type"] == "assertion":
        return sorted(clause.get('resolved_clbids', []))
    # elif clause["type"] == "or-clause":
    #     return [clbid for c in clause["children"] for clbid in get_resolved_clbids(c)]
    # elif clause["type"] == "and-clause":
    #     return [clbid for c in clause["children"] for clbid in get_resolved_clbids(c)]

    raise Exception('not a clause')


def get_in_progress_clbids(clause: Dict[str, Any]) -> Set[str]:
    if clause["type"] == "assertion":
        return set(clause.get('in_progress_clbids', []))
    # elif clause["type"] == "or-clause":
    #     return set(clbid for c in clause["children"] for clbid in get_in_progress_clbids(c))
    # elif clause["type"] == "and-clause":
    #     return set(clbid for c in clause["children"] for clbid in get_in_progress_clbids(c))

    raise Exception('not a clause')
