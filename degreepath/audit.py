import dataclasses
from typing import List, Any
from datetime import datetime
import time
import decimal

from .area import AreaOfStudy
from .ms import pretty_ms
from .lib import grade_point_average


@dataclasses.dataclass
class Arguments:
    area_files: List[str]
    student_files: List[str]
    print_all: bool = False


@dataclasses.dataclass
class NoStudentsMsg:
    pass


@dataclasses.dataclass
class AuditStartMsg:
    stnum: str
    area_code: str
    area_catalog: str


@dataclasses.dataclass
class ResultMsg:
    result: Any
    transcript: List
    count: int
    elapsed: str
    iterations: List[int]
    startup_time: int
    gpa: decimal.Decimal


@dataclasses.dataclass
class ExceptionMsg:
    ex: Exception
    tb: str


@dataclasses.dataclass
class NoAuditsCompletedMsg:
    pass


@dataclasses.dataclass
class ProgressMsg:
    count: int
    recent_iters: List[int]
    start_time: datetime


def audit(*, spec, transcript, constants, area_pointers, print_all):
    area = AreaOfStudy.load(specification=spec, c=constants)
    area.validate()

    this_transcript = []
    attributes_to_attach = area.attributes.get("courses", {})
    for c in transcript:
        attrs_by_course = set(attributes_to_attach.get(c.course(), []))
        attrs_by_shorthand = set(attributes_to_attach.get(c.course_shorthand(), []))
        attrs_by_term = set(attributes_to_attach.get(c.course_with_term(), []))

        c = c.attach_attrs(attributes=attrs_by_course | attrs_by_shorthand | attrs_by_term)
        this_transcript.append(c)

    this_transcript = tuple(this_transcript)

    best_sol = None
    total_count = 0
    iterations = []
    start_time = datetime.now()
    start = time.perf_counter()
    iter_start = time.perf_counter()
    startup_time = 0

    for sol in area.solutions(transcript=this_transcript, areas=area_pointers):
        if total_count == 0:
            startup_time = time.perf_counter() - iter_start
            iter_start = time.perf_counter()

        total_count += 1

        if total_count % 1_000 == 0:
            yield ProgressMsg(count=total_count, recent_iters=iterations[-1_000:], start_time=start_time)

        result = sol.audit(transcript=this_transcript, areas=area_pointers)

        if print_all:
            gpa = gpa_from_solution(result=result, transcript=this_transcript)
            yield ResultMsg(result=result, gpa=gpa, transcript=this_transcript, count=total_count, elapsed='∞', iterations=[], startup_time=startup_time)

        if best_sol is None:
            best_sol = result

        if result.rank() > best_sol.rank():
            best_sol = result

        if result.ok():
            best_sol = result
            iter_end = time.perf_counter()
            iterations.append(iter_end - iter_start)
            break

        iter_end = time.perf_counter()
        iterations.append(iter_end - iter_start)
        iter_start = time.perf_counter()

    if not iterations:
        yield NoAuditsCompletedMsg()

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    gpa = gpa_from_solution(result=best_sol, transcript=this_transcript)

    yield ResultMsg(result=best_sol, gpa=gpa, transcript=this_transcript, count=total_count, elapsed=elapsed, iterations=iterations, startup_time=startup_time)
    return


def gpa_from_solution(*, result, transcript):
    transcript_map = {c.clbid: c for c in transcript}
    claimed_courses = [transcript_map[c.claim.clbid] for c in result.claims() if c.failed() is False]

    return round(grade_point_average(claimed_courses), 2)
