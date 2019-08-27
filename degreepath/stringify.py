from typing import List, Iterator, Any, Dict, Sequence
from .clause import str_clause, get_resolved_items, get_resolved_clbids
from .data import CourseInstance
from .ms import pretty_ms
import json


def summarize(
    *,
    transcript: Sequence[CourseInstance],
    result: Dict[str, Any],
    count: int,
    elapsed: str,
    iterations: List[float],
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    endl = "\n"

    word = "attempt" if count == 1 else "attempts"
    yield f"{count:,} {word} in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl
    yield endl

    yield endl.join(print_result(result, list(transcript), show_paths=show_paths, show_ranks=show_ranks))

    yield endl


def print_result(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if rule["type"] == "area":
        yield from print_area(rule, transcript, indent, show_paths, show_ranks)

    elif rule["type"] == "course":
        yield from print_course(rule, transcript, indent, show_paths, show_ranks)

    elif rule["type"] == "count":
        yield from print_count(rule, transcript, indent, show_paths, show_ranks)

    elif rule["type"] == "query":
        yield from print_query(rule, transcript, indent, show_paths, show_ranks)

    elif rule["type"] == "requirement":
        yield from print_requirement(rule, transcript, indent, show_paths, show_ranks)

    elif rule["type"] == "assertion":
        yield from print_assertion(rule, transcript, indent, show_paths, show_ranks)

    else:
        yield json.dumps(rule, indent=2)


def print_path(rule: Dict[str, Any], indent: int) -> Iterator[str]:
    prefix = " " * indent

    yield f"{prefix}{json.dumps(rule['path'])}"


def calculate_emoji(rule: Dict[str, Any]) -> str:
    if rule["overridden"]:
        return "💜"
    elif rule["status"] == "pass":
        return "💚"
    elif rule["status"] == "skip":
        return "🌀"
    else:
        return "🚫️"


def print_area(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    if rule['ok']:
        title = f"{rule['name']!r} audit was successful."
    else:
        title = f"{rule['name']!r} audit failed."

    yield f"{title} (rank {rule['rank']} of {rule['max_rank']}; gpa: {rule['gpa']})"

    yield ""

    yield from print_result(rule['result'], transcript, show_ranks=show_ranks, show_paths=show_paths)


def print_course(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

    status = "🌀      "
    if rule["ok"]:
        if not rule["overridden"]:
            claim = rule["claims"][0]["claim"]
            mapped_trns = {c.clbid: c for c in transcript}
            course = mapped_trns.get(claim["clbid"], None)

            if not course:
                status = "!!!!!!! "
            elif course.is_incomplete:
                status = "⛔️ [dnf]"
            elif course.is_in_progress:
                status = "💙 [ ip]"
            elif course.is_repeat:
                status = "💕 [rep]"
            else:
                status = "💚 [ ok]"
        else:
            status = "💜 [ovr]"

    yield f"{prefix}{status} {rule['course']}"


def print_count(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

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

    ok_count = len([r for r in rule["items"] if r["ok"]])
    descr += f" (ok: {ok_count}; need: {rule['count']})"

    yield f"{prefix}{emoji} {descr}"

    if rule['audit']:
        yield f'{prefix} This requirement has a post-audit:'

        yield f"{prefix} There must be:"
        for a in rule['audit']:
            yield from print_result(a, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths)

        yield ''

    for i, r in enumerate(rule["items"]):
        yield from print_result(r, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths)

        if i < len(rule['items']) - 1:
            yield ''


def print_query(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

    emoji = calculate_emoji(rule)

    if rule['where'] is not None:
        yield f"{prefix}{emoji} Given courses matching {str_clause(rule['where'])}"

    if rule['limit'] is not None:
        yield f"{prefix} Subject to these limits:"
        for limit in rule['limit']:
            yield f"{prefix} - at most {limit['at_most']} where {str_clause(limit['where'])}"

    if rule["status"] in ("pending"):
        yield f'{prefix}[skipped]'
        return

    mapped_trns = {c.clbid: c for c in transcript}

    if rule["claims"]:
        yield f"{prefix} Matching courses:"
        for clm in rule["claims"]:
            course = mapped_trns.get(clm['claim']["clbid"], None)
            if course:
                yield f"{prefix}    {course.course_shorthand()} \"{course.name}\" ({course.clbid})"
            else:
                yield f"{prefix}    !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

    if rule["failures"]:
        yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
        for clm in rule["failures"]:
            course = mapped_trns.get(clm['claim']["clbid"], None)
            if course:
                conflicts = [x['claimant_path'] for x in clm['conflict_with']]
                yield f"{prefix}    {course.course_shorthand()} \"{course.name}\" ({course.clbid}) [{conflicts}]"
            else:
                yield f"{prefix}    !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

    yield f"{prefix} There must be:"
    for a in rule['assertions']:
        yield from print_result(a, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths)


def print_requirement(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

    emoji = calculate_emoji(rule)

    yield f"{prefix}{emoji} Requirement({rule['name']})"
    if rule["audited_by"] is not None:
        yield f"{prefix}    Audited by: {rule['audited_by']}"
        return
    if rule["result"]:
        yield from print_result(rule["result"], transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths)


def print_assertion(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

    emoji = calculate_emoji(rule)

    yield f"{prefix} - {emoji} {str_clause(rule['assertion'])}"

    prefix += " " * 6

    if rule['where']:
        yield f"{prefix}where {str_clause(rule['where'])}"

    resolved_items = get_resolved_items(rule['assertion'])
    if resolved_items:
        yield f"{prefix}resolved items: {resolved_items}"

    resolved_clbids = get_resolved_clbids(rule['assertion'])
    if resolved_clbids:
        def key(c: CourseInstance) -> str:
            return ''
        if rule['assertion']['key'] == 'sum(credits)':
            def key(c: CourseInstance) -> str:  # noqa F811
                return f'credits={c.credits}'
        elif rule['assertion']['key'] == 'average(grades)':
            def key(c: CourseInstance) -> str:  # noqa F811
                return f'grade={c.grade_points}'

        mapped_trns = {c.clbid: c for c in transcript}

        yield f"{prefix}resolved courses:"

        for clbid in resolved_clbids:
            course = mapped_trns[clbid]
            chunks = [x for x in [f'"{course.course()}"', f'name="{course.name}"', f'clbid={course.clbid}', key(course)] if x]
            yield f'{prefix}  - Course({", ".join(chunks)})'
