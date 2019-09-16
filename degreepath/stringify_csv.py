from typing import List, Iterator, Any, Dict, Sequence, Tuple
from io import StringIO
import csv

from .clause import str_clause, get_resolved_clbids, get_in_progress_clbids
from .data import CourseInstance


def to_csv(result: Dict[str, Any], *, transcript: Sequence[CourseInstance]) -> str:
    with StringIO() as f:
        data = {' > '.join(k for k in key if k): val for key, val in csvify_result(result, list(transcript), [])}
        keys = list(data.keys())

        writer = csv.DictWriter(f, fieldnames=keys)

        writer.writeheader()
        writer.writerow(data)

        return f.getvalue()


def csvify_result(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    if rule["type"] == "area":
        yield from csvify_area(rule, transcript, path)

    elif rule["type"] == "course":
        yield from csvify_course(rule, transcript, path)

    elif rule["type"] == "count":
        yield from csvify_count(rule, transcript, path)

    elif rule["type"] == "query":
        yield from csvify_query(rule, transcript, path)

    elif rule["type"] == "requirement":
        yield from csvify_requirement(rule, transcript, path)

    elif rule["type"] == "assertion":
        yield from csvify_assertion(rule, transcript, path)

    else:
        raise Exception(f'unknown type {rule["type"]}')


def csvify_area(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    yield (['progress'], f"{round(float(rule['rank']) / float(rule['max_rank'])):.2%}")
    yield (['gpa'], rule['gpa'])
    yield from csvify_result(rule['result'], transcript, path)


def csvify_course(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    if rule["status"] == "in-progress":
        yield (path, 'in-progress')

    elif rule["status"] == "pass":
        mapped_trns = {c.clbid: c for c in transcript}
        if len(rule["claims"]):
            claim = rule["claims"][0]["claim"]
            course = mapped_trns.get(claim["clbid"], None)
        else:
            course = None

        yield (path, f"{course.course_with_term()}" if course else '???')
    else:
        yield (path, '-')


def csvify_count(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    for i, r in enumerate(rule["items"]):
        if len(rule['path']) == 2:
            index = ""
        elif rule['count'] == len(rule['items']):
            index = f"{i + 1}/{len(rule['items'])}"
        elif rule['count'] == 1:
            index = ""
        else:
            index = f"{i + 1}/{len(rule['items'])}"

        for k, v in csvify_result(r, transcript, [*path, index]):
            if rule['count'] == 1 and v == '-':
                continue
            yield (k, v)


def csvify_query(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    for a in rule['assertions']:
        if a['assertion']['operator'] not in ('LessThan', 'LessThanOrEqualTo'):
            yield from csvify_assertion(a, transcript, path)


def csvify_requirement(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    if rule["name"].startswith('Common ') and rule["name"].endswith(' Major Requirements'):
        return

    if rule["audited_by"] == 'department':
        yield (rule['name'], 'Requires departmental signature')

    if rule["result"]:
        yield from csvify_result(rule["result"], transcript, [*path, rule["name"]])


def csvify_assertion(
    rule: Dict[str, Any],
    transcript: List[CourseInstance],
    path: List[str],
) -> Iterator[Tuple[List[str], str]]:
    where = f"{str_clause(rule['where'])}, " if rule['where'] else ''

    kind_lookup = {
        'count(courses)': 'courses',
        'count(terms_from_most_common_course)': 'terms from the most common course',
        'count(subjects)': 'subjects',
        'count(terms)': 'terms',
        'count(years)': 'years',
        'count(distinct_courses)': 'distinct courses',
        'sum(credits)': 'credits',
        'sum(credits_from_single_subject)': 'credits from a single subject code',
        'average(grades)': 'gpa',
        'average(credits)': 'avg. credits',
        'count(areas)': 'areas',
        'count(items)': 'items',
        'count(performances)': 'performances',
        'count(seminars)': 'seminars',
    }

    kind = kind_lookup.get(rule['assertion']['key'], '???')

    resolved_clbids = get_resolved_clbids(rule['assertion'])
    ip_clbids = get_in_progress_clbids(rule['assertion'])
    all_clbids = [*resolved_clbids, *ip_clbids]

    expected = rule['assertion']['expected']
    for i in range(expected):
        if len(all_clbids) <= i:
            yield ([*path, f"{where}{i + 1}/{expected} {kind}"], '-')
            continue

        clbid = all_clbids[i]
        course = {c.clbid: c for c in transcript}[clbid]
        yield ([*path, f"{where}{i + 1}/{expected} {kind}"], course.course_with_term())
