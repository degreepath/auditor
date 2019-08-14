from typing import List, Iterator, Any, Dict, Sequence
from .clause import str_clause, get_resolved_items
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
) -> Iterator[str]:
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    endl = "\n"

    word = "attempt" if count == 1 else "attempts"
    yield f"{count:,} {word} in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl
    yield endl

    yield endl.join(print_result(result, list(transcript)))

    yield endl


def print_result(rule: Dict[str, Any], transcript: List[CourseInstance], indent: int = 0) -> Iterator[str]:  # noqa: C901
    prefix = " " * indent

    rule_type = rule["type"]
    rank = rule["rank"]
    path = rule["path"]

    yield f"{prefix}{json.dumps(path)}"

    prefix += f"({rank}|{'t' if rule['ok'] else 'f'}) "

    if rule_type == "area":
        if rule['ok']:
            title = f"{rule['name']!r} audit was successful."
        else:
            title = f"{rule['name']!r} audit failed."

        yield f"{title} (rank {rule['rank']} of {rule['max_rank']}; gpa: {rule['gpa']})"

        yield ""

        yield from print_result(rule['result'], transcript)

    elif rule_type == "course":
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
                    status = "💚 [ ip]"
                elif course.is_repeat:
                    status = "💚 [rep]"
                else:
                    status = "💚 [ ok]"
            else:
                status = "💜 [ovr]"

        yield f"{prefix}{status} {rule['course']}"

    elif rule_type == "count":
        if rule["overridden"]:
            emoji = "💜"
        elif rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

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
                if a["overridden"]:
                    emoji = "💜"
                elif a["status"] == "pass":
                    emoji = "💚"
                elif a["status"] == "skip":
                    emoji = "🌀"
                else:
                    emoji = "🚫️"

                yield f"{prefix} - {emoji} {str_clause(a['assertion'])} {str(a['path'])}"
                if a['where']:
                    yield f"{prefix}      where {str_clause(a['where'])}"
                resolved_items = get_resolved_items(a['assertion'])
                if resolved_items:
                    yield f"{prefix}      resolved items: {resolved_items}"

            yield ''

        for r in rule["items"]:
            yield from print_result(r, transcript, indent=indent + 4)

    elif rule_type == "query":
        if rule["overridden"]:
            emoji = "💜"
        elif rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        if rule['where'] is not None:
            yield f"{prefix}{emoji} Given courses matching {str_clause(rule['where'])}"

        if rule["status"] in ("pending"):
            yield f'{prefix}[skipped]'
            return

        mapped_trns = {c.clbid: c for c in transcript}

        if rule["claims"]:
            yield f"{prefix} Matching courses:"
            for clm in rule["claims"]:
                course = mapped_trns.get(clm['claim']["clbid"], None)
                if course:
                    yield f"{prefix}   {course.course_shorthand()} \"{course.name}\" ({course.clbid})"
                else:
                    yield f"{prefix}   !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

        if rule["failures"]:
            yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
            for clm in rule["failures"]:
                course = mapped_trns.get(clm['claim']["clbid"], None)
                if course:
                    conflicts = [x['claimant_path'] for x in clm['conflict_with']]
                    yield f"{prefix}   {course.course_shorthand()} \"{course.name}\" ({course.clbid}) [{conflicts}]"
                else:
                    yield f"{prefix}   !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

        yield f"{prefix} There must be:"
        for a in rule['assertions']:
            if a["overridden"]:
                emoji = "💜"
            elif a["status"] == "pass":
                emoji = "💚"
            elif a["status"] == "skip":
                emoji = "🌀"
            else:
                emoji = "🚫️"

            yield f"{prefix} - {emoji} {str_clause(a['assertion'])} {str(a['path'])}"
            if a['where']:
                yield f"{prefix}      where {str_clause(a['where'])}"
            resolved_items = get_resolved_items(a['assertion'])
            if resolved_items:
                yield f"{prefix}      resolved items: {resolved_items}"

    elif rule_type == "requirement":
        if rule["overridden"]:
            emoji = "💜"
        elif rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        if rule["audited_by"] is not None:
            yield f"{prefix}    Audited by: {rule['audited_by']}"
            return
        if rule["result"]:
            yield from print_result(rule["result"], transcript, indent=indent + 4)

    else:
        yield json.dumps(rule, indent=2)
