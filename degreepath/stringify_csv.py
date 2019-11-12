from typing import List, Iterator, Any, Dict, Sequence, Tuple
from io import StringIO
import attr
import csv

from .clause import str_clause, get_resolved_clbids, get_in_progress_clbids
from .data import CourseInstance


def to_csv(result: Dict[str, Any], *, transcript: Sequence[CourseInstance]) -> str:
    with StringIO() as f:
        writer = csv.writer(f)

        writer.writerow(['key', 'student'])
        for key, val in Csvify(transcript={c.clbid: c for c in transcript}).csvify(result):
            key = ' > '.join(k for k in key if k)
            writer.writerow([key, val])

        return f.getvalue()


@attr.s(slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Csvify:
    transcript: Dict[str, CourseInstance]

    def csvify(self, root: Dict[str, Any]):
        yield from self.result(root, path=[], overridden=False)

    def result(
        self,
        rule: Dict[str, Any],
        *,
        path: Sequence[str],
        overridden: bool,
    ) -> Iterator[Tuple[List[str], str]]:
        if rule["type"] == "area":
            yield from self.area(rule, path=path)
        elif rule["type"] == "course":
            yield from self.course(rule, path=path, overridden=overridden)
        elif rule["type"] == "count":
            yield from self.count(rule, path=path, overridden=overridden)
        elif rule["type"] == "query":
            yield from self.query(rule, path=path, overridden=overridden)
        elif rule["type"] == "requirement":
            yield from self.requirement(rule, path=path, overridden=overridden)
        elif rule["type"] == "assertion":
            yield from self.assertion(rule, path=path, overridden=overridden)
        else:
            raise Exception(f'unknown type {rule["type"]}')

    def area(self, rule: Dict[str, Any], *, path: Sequence[str]) -> Iterator[Tuple[List[str], str]]:
        yield (['progress'], f"{round(float(rule['rank']) / float(rule['max_rank'])):.2%}")
        yield (['gpa'], rule['gpa'])
        yield from self.result(rule['result'], path=path, overridden=rule['overridden'])

    def course(self, rule: Dict[str, Any], *, path: Sequence[str], overridden: bool) -> Iterator[Tuple[List[str], str]]:
        if overridden:
            yield (path, '[overridden]')
            return

        if rule["status"] == "in-progress":
            yield (path, 'in-progress')
            return

        elif rule["status"] == "pass":
            if len(rule["claims"]):
                claim = rule["claims"][0]["claim"]
                course = self.transcript.get(claim["clbid"], None)
            else:
                course = None

            yield (path, f"{course.course_with_term()}" if course else '???')
            return

        yield (path, '-')

    def count(self, rule: Dict[str, Any], *, path: Sequence[str], overridden: bool) -> Iterator[Tuple[List[str], str]]:
        overridden = overridden or rule['overridden']

        for i, r in enumerate(rule["items"]):
            if len(rule['path']) == 2:
                pass
            elif rule['count'] == len(rule['items']):
                index = f"{i + 1}/{len(rule['items'])}"
                path = [*path, index]
            elif rule['count'] == 1:
                pass
            else:
                index = f"{i + 1}/{len(rule['items'])}"
                path = [*path, index]

            for k, v in self.result(r, path=path, overridden=overridden):
                if overridden:
                    yield (k, '[overridden]')
                    continue
                if rule['count'] == 1 and v == '-':
                    continue
                yield (k, v)

    def query(self, rule: Dict[str, Any], *, path: Sequence[str], overridden: bool) -> Iterator[Tuple[List[str], str]]:
        for a in rule['assertions']:
            if a['assertion']['operator'] not in ('LessThan', 'LessThanOrEqualTo'):
                yield from self.assertion(a, path=path, overridden=overridden or rule['overridden'])

    def requirement(self, rule: Dict[str, Any], *, path: Sequence[str], overridden: bool) -> Iterator[Tuple[List[str], str]]:
        if rule["name"].startswith('Common ') and rule["name"].endswith(' Major Requirements'):
            return

        if rule["audited_by"] == 'department':
            yield ([rule['name']], 'Requires departmental signature')
            return

        if rule["result"]:
            yield from self.result(rule["result"], path=[*path, rule["name"]], overridden=overridden or rule['overridden'])

    def assertion(self, rule: Dict[str, Any], *, path: Sequence[str], overridden: bool) -> Iterator[Tuple[List[str], str]]:
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
            key = [*path, f"{where}{i + 1}/{expected} {kind}"]
            if overridden or rule['overridden']:
                yield (key, '[overridden]')
                continue

            if len(all_clbids) <= i:
                yield (key, '-')
                continue

            course = self.transcript[all_clbids[i]]
            yield (key, course.course_with_term())
