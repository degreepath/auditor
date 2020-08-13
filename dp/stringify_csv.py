from typing import Iterator, Any, Dict, Tuple, Callable
# from io import StringIO
# import csv
# import json
# import textwrap

from .stringify import str_predicate
from .data.course import CourseInstance
from .status import PassingStatusValues, ResultStatus


# def to_csv(result: Dict[str, Any], *, transcript: Sequence[CourseInstance]) -> str:
#     with StringIO() as f:
#         writer = csv.writer(f)
#
#         csvifier = Csvify(stnum='000000', transcript={c.clbid: c for c in transcript})
#
#         # header = csvifier.header_rows(result) | translate_newlines | merge
#
#         # IDEA: DictWriter and have the thing produce (key,value) for each item?
#         # Probably would error, but would also probably better identify mismatched items than a (keys...) pass and then N (values...) passes
#
#         # data = csvifier.process(result)
#         # print(list(data))
#         header = dict(csvifier.process(result))
#         print(json.dumps(header))
#         # for col in header:
#         #     print(col)
#
#         # writer.writerow(header)
#         # for key, val in Csvify(transcript={c.clbid: c for c in transcript}).csvify(result):
#         #     writer.writerow([' > '.join(k for k in key if k), val])
#
#         return f.getvalue()


class Csvify:
    stnum: str
    transcript: Dict[str, CourseInstance]

    def __init__(self, *, stnum: str, transcript: Dict[str, CourseInstance]) -> None:
        self.transcript = transcript
        self.stnum = stnum

        self.lookup: Dict[str, Callable[[Dict[str, Any], bool], Iterator[Tuple[str, str]]]] = {
            "area": self.area,
            "course": self.course,
            "proficiency": self.proficiency,
            "count": self.count,
            "query": self.query,
            "requirement": self.requirement,
        }

    def process(self, root: Dict[str, Any]) -> Iterator[Tuple[str, str]]:
        yield ('Student', self.stnum)
        yield ('GPA', root['gpa'])
        yield ('Status', root['status'])
        yield ('Classification', '???')
        yield ('Ant. Grad. Date', 'May 2000')
        yield from self.dispatch(root, waived=False)

    def dispatch(self, rule: Dict[str, Any], *, waived: bool) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        # print(' > '.join(rule['path']))
        yield from self.lookup[rule["type"]](rule, waived)

    def area(self, rule: Dict[str, Any], waived: bool) -> Iterator[Tuple[str, str]]:
        yield from self.dispatch(rule['result'], waived=waived)

    def requirement(self, rule: Dict[str, Any], waived: bool) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        name = rule['name']

        if '→' in name:
            name = "\n↳ ".join(p.strip() for p in name.split('→'))

        if rule['result']['type'] == 'course':
            yield (name, rule['result']['course'])
            return

        for child_key, child_val in self.dispatch(rule['result'], waived=waived):
            # if child_key.startswith('where '):
            #     child_key = textwrap.fill(child_key, width=40, subsequent_indent=' ' * 8)

            yield (f"{name}\n↳ {child_key}", child_val)

    def course(self, rule: Dict[str, Any], waived: bool) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        if rule['status'] in PassingStatusValues:
            yield (f"{rule['course']}", rule['course'])
        else:
            (f"{rule['course']}", '')

    def proficiency(self, rule: Dict[str, Any], waived: bool) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        yield (f"{rule['proficiency']}", rule['course']['course'] if rule['course'] else 'done' if rule['status'] in PassingStatusValues else '')

    def query(self, rule: Dict[str, Any], waived: bool) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        if rule['where']:
            where = f"where {str_predicate(rule['where'], raw_only=True)}"
        else:
            where = ""

        assertions = rule['assertions']
        # if len(assertions) == 1:
        for assertion in assertions:
            for assertion_key, assertion_val in self.assertion(assertion, waived=waived, source=rule['source']):
                if where:
                    yield (f"{where}\n↳ {assertion_key}", assertion_val)
                else:
                    yield (f"{assertion_key}", assertion_val)

    def assertion(self, rule: Dict[str, Any], *, waived: bool, source: str) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        assertion = rule['assertion']
        where = rule.get('where', None)

        expected = assertion['expected']

        leader = "need"
        if assertion['operator'] in ('LessThan', 'LessThanOrEqualTo'):
            leader = "at most"
        elif assertion['operator'] in ('EqualTo'):
            leader = "exactly"
        elif assertion['operator'] in ('NotEqualTo'):
            leader = "not"

        key = f"{leader} {expected} {assertion['key']}"

        resolved_clbids = assertion.get('resolved_clbids', [])
        resolved_courses = sorted(self.transcript[clbid].course() for clbid in resolved_clbids)

        resolved_courses_str = ', '.join(resolved_courses)

        # if where:
        #     yield (f"{key} where {str_clause(where, raw_only=True)}\n↳ … ok?", assertion['status'])
        #     yield (f"{key} where {str_clause(where, raw_only=True)}\n↳ … courses", resolved_courses_str)
        # else:
        #     yield (f"{key}\n↳ … ok?", assertion['status'])
        #     yield (f"{key}\n↳ … courses", resolved_courses_str)
        if where:
            yield (f"{key} where {str_predicate(where, raw_only=True)}", f"{assertion['status']}: {resolved_courses_str}")
        else:
            yield (key, f"{assertion['status']}: {resolved_courses_str}")

    def count(self, rule: Dict[str, Any], waived: bool) -> Iterator[Tuple[str, str]]:
        waived = waived or rule['status'] == ResultStatus.Waived.value or False

        if rule["count"] == 1 and len(rule["items"]) >= 1:
            key = 'need 1 course'

            for r in rule['items']:
                # if r['status'] not in ('empty', 'pending-approval'):
                # if r['type'] == 'course':
                #     yield (key, r['course'])
                # elif r['type'] == 'count':
                #     yield from self.count(r, waived=waived)
                # # elif r['type'] == 'count':
                # #     yield from self.count(r, waived=waived)
                # else:
                #     # assert None, KeyError(r['type'], r)
                yield from self.dispatch(r, waived=waived)
                return

            if waived:
                yield (key, '<waived>')
                return

            assert None, (self.stnum, rule['path'])
            # if not None:
            #     print()

        for child in rule["items"]:
            yield from self.dispatch(child, waived=waived)
