from typing import List, Iterator, Any, Dict, Sequence
from .clause import str_clause, get_resolved_items, get_resolved_clbids, get_in_progress_clbids
from .data import CourseInstance
from .data.course_enums import CourseType
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
    claims: Dict[str, List[List[str]]],
) -> Iterator[str]:
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True)
    mapped_transcript = {c.clbid: c for c in transcript}
    endl = "\n"

    word = "attempt" if count == 1 else "attempts"
    yield f"{count:,} {word} in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl
    yield endl

    yield endl.join(print_result(result, transcript=mapped_transcript, show_paths=show_paths, show_ranks=show_ranks))

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
        yield from print_assertion(rule, transcript, indent, show_paths, show_ranks, inserted=inserted)

    elif rule["type"] == "conditional-assertion":
        yield from print_conditional_assertion(rule, transcript, indent, show_paths, show_ranks, inserted=inserted)

    elif rule["type"] == "proficiency":
        yield from print_proficiency(rule, transcript, indent, show_paths, show_ranks)

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
    elif rule["status"] == "pending":
        return "🌀"
    elif rule["status"] == "in-progress":
        return "💛"
    else:
        return "🚫️"


def print_area(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
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

    if rule['limit']:
        yield f"Subject to these limits:"
        for limit in rule['limit']:
            yield f"- at most {limit['at_most']} where {str_clause(limit['where'])}"

    yield ""

    yield from print_result(rule['result'], transcript, show_ranks=show_ranks, show_paths=show_paths)


def print_course(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

    display_course = rule['course']
    if not rule['course'] and rule['ap'] != '':
        display_course = rule['ap']

    status = "🌀      "

    if len(rule["claims"]):
        claim = rule["claims"][0]["claim"]
        course = transcript.get(claim["clbid"], None)
    else:
        course = None

    if not rule["overridden"]:
        if course is None:
            status = "🌀      "
        elif course.is_incomplete:
            status = "⛔️ [dnf]"
        elif course.is_in_progress:
            status = "💙 [ ip]"
        elif course.is_repeat:
            status = "💕 [rep]"
        elif course:
            status = "💚 [ ok]"
        else:
            status = "!!!!!!! "

        if course and course.course_type is CourseType.AP:
            display_course = course.name
    elif rule["ok"] and rule["overridden"]:
        if course:
            status = "💜 [ovr]"
            display_course = f"{course.course().strip()} {course.name}"
        else:
            status = "💜 [wvd]"

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
) -> Iterator[str]:
    if show_paths:
        yield from print_path(rule, indent)

    prefix = " " * indent
    if show_ranks:
        prefix += f"({rule['rank']}|{rule['max_rank']}|{'t' if rule['ok'] else 'f'}) "

    status = "🌀      "
    if rule["ok"]:
        if rule["overridden"]:
            status = "💜 [wvd]"
        else:
            status = "💚 [ ok]"

    yield f"{prefix}{status} Proficiency={rule['proficiency']}"

    if rule['course']['ok']:
        yield from print_course(rule['course'], transcript, indent + 4, show_paths, show_ranks)


def print_count(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
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

        if size != 2 and i < len(rule['items']) - 1:
            yield ''


def print_query(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
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

    if rule['where']:
        yield f"{prefix}{emoji} Given courses matching {str_clause(rule['where'])}"

    if rule['limit']:
        yield f"{prefix} Subject to these limits:"
        for limit in rule['limit']:
            yield f"{prefix} - at most {limit['at_most']} where {str_clause(limit['where'])}"

    if rule["claims"]:
        yield f"{prefix} Matching courses:"
        for clm in rule["claims"]:
            course = transcript.get(clm['claim']["clbid"], None)
            if not course:
                yield f"{prefix}    !!!!! \"!!!!!\" ({clm['claim']['clbid']})"
                continue

            inserted_msg = "[ins] " if clm['claim']["clbid"] in rule["inserted"] else ""
            ip_msg = "[ip] " if course.is_in_progress else ""
            yield f"{prefix}    {inserted_msg}{ip_msg}{course.course()} \"{course.name}\" ({course.clbid})"

    if rule["failures"]:
        yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
        for clm in rule["failures"]:
            course = transcript.get(clm['claim']["clbid"], None)
            if course:
                conflicts = [x['claimant_path'] for x in clm['conflict_with']]
                yield f"{prefix}    {course.course()} \"{course.name}\" ({course.clbid}) [{conflicts}]"
            else:
                yield f"{prefix}    !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

    yield f"{prefix} There must be:"
    for a in rule['assertions']:
        yield from print_result(a, transcript, indent=indent + 4, show_ranks=show_ranks, show_paths=show_paths, inserted=rule["inserted"])


def print_requirement(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
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
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    inserted: Sequence[str] = tuple(),
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

        yield f"{prefix}resolved courses:"

        ip_clbids = get_in_progress_clbids(rule['assertion'])

        for clbid in resolved_clbids:
            inserted_msg = " [ins]" if clbid in inserted or clbid in rule['inserted'] else ""
            ip_msg = " [ip]" if clbid in ip_clbids else ""
            if clbid in transcript:
                course = transcript[clbid]
                chunks = [x for x in [f'"{course.course()}"', f'name="{course.name}"', f'clbid={course.clbid}', key(course)] if x]
                yield f'{prefix}  -{ip_msg}{inserted_msg} Course({", ".join(chunks)})'
            else:
                yield f'{prefix}  -{ip_msg}{inserted_msg} Course(clbid={clbid})'


def print_conditional_assertion(
    rule: Dict[str, Any],
    transcript: Dict[str, CourseInstance],
    indent: int = 0,
    show_paths: bool = True,
    show_ranks: bool = True,
    inserted: Sequence[str] = tuple(),
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
