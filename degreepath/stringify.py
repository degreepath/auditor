from .clause import Operator, str_clause
from .data import CourseStatus
from .rule import str_assertion
from .ms import pretty_ms


def summarize(*, stnum, transcript, result, count, elapsed, iterations):
    avg_iter_s = sum(iterations) / max(len(iterations), 1)
    avg_iter_time = pretty_ms(avg_iter_s * 1_000, format_sub_ms=True, unit_count=1)

    endl = "\n"

    yield f"#{stnum}'s"

    if result['ok']:
        yield f" audit was successful."
    else:
        yield f" audit failed."

    yield f" (rank {result['rank']})"

    yield endl

    word = "attempt" if count == 1 else "attempts"
    yield f"{count:,} {word} in {elapsed} (avg {avg_iter_time} per attempt)"
    yield endl

    yield endl

    yield "Results"
    yield endl
    yield "======="

    yield endl
    yield endl

    yield endl.join(print_result(result, transcript))

    yield endl


def print_result(rule, transcript, indent=0):
    prefix = " " * indent

    if rule is None:
        yield f"{prefix}???"
        return

    rule_type = rule["type"]

    if rule_type == "course":
        status = "🌀      "
        if "ok" in rule and rule["ok"]:
            claim = rule["claims"][0]["claim"]
            mapped_trns = {c.clbid: c for c in transcript}
            course = mapped_trns.get(claim["clbid"], None)

            if not course:
                status = "!!!!!!! "
            elif course.status == CourseStatus.Ok:
                status = "💚 [ ok]"
            elif course.status == CourseStatus.DidNotComplete:
                status = "⛔️ [dnf]"
            elif course.status == CourseStatus.InProgress:
                status = "💚 [ ip]"
            elif course.status == CourseStatus.Repeated:
                status = "💚 [rep]"
            elif course.status == CourseStatus.NotTaken:
                status = "🌀      "

        yield f"{prefix}{status} {rule['course']}"

    elif rule_type == "count":
        if rule["status"] == "pass":
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
            descr = f"{rule['count']} of {size}"

        ok_count = len([r for r in rule["items"] if r["ok"]])
        descr += f" (ok: {ok_count}; need: {rule['count']})"

        yield f"{prefix}{emoji} {descr}"

        for r in rule["items"]:
            yield from print_result(r, transcript, indent=indent + 4)

    elif rule_type == "from":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        if rule['where'] is not None:
            yield f"{prefix}{emoji} Given courses matching {str_clause(rule['where'])}"

        mapped_trns = {c.clbid: c for c in transcript}

        if rule["claims"]:
            yield f"{prefix} Matching courses:"
            for clm in rule["claims"]:
                course = mapped_trns.get(clm['claim']["clbid"], None)
                if course:
                    yield f"{prefix}   {course.shorthand} \"{course.name}\" ({course.clbid})"
                else:
                    yield f"{prefix}   !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

        if rule["failures"]:
            yield f"{prefix} Pre-claimed courses which cannot be re-claimed:"
            for clm in rule["failures"]:
                course = mapped_trns.get(clm['claim']["clbid"], None)
                if course:
                    yield f"{prefix}   {course.shorthand} \"{course.name}\" ({course.clbid})"
                else:
                    yield f"{prefix}   !!!!! \"!!!!!\" ({clm['claim']['clbid']})"

        yield f"{prefix} There must be {str_clause(rule['action'])} (have: {len(rule['claims'])})"

    elif rule_type == "requirement":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        if rule["audited_by"] is not None:
            yield f"{prefix}    Audited by: {rule['audited_by']}; assuming success"
            return
        yield from print_result(rule["result"], transcript, indent=indent + 4)

    elif rule_type == "reference":
        if rule["status"] == "pass":
            emoji = "💚"
        elif rule["status"] == "skip":
            emoji = "🌀"
        else:
            emoji = "🚫️"

        yield f"{prefix}{emoji} Requirement({rule['name']})"
        yield f"{prefix}   [Skipped]"

    else:
        yield json.dumps(rule, indent=2)
