import dataclasses
from typing import List, Optional, Set, Dict, Tuple, Sequence, Iterator, Any, Union, cast
from datetime import datetime
import time

from .constants import Constants
from .exception import RuleException
from .area import AreaOfStudy, AreaResult
from .ms import pretty_ms
from .data import CourseInstance, AreaPointer


@dataclasses.dataclass
class Arguments:
    area_files: List[str]
    student_files: List[str]
    print_all: bool = False
    estimate_only: bool = False


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
    result: AreaResult
    transcript: Tuple[CourseInstance, ...]
    count: int
    elapsed: str
    iterations: List[float]
    startup_time: float


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
    recent_iters: List[float]
    start_time: datetime
    best_rank: int


@dataclasses.dataclass
class EstimateMsg:
    estimate: int


Message = Union[EstimateMsg, ProgressMsg, NoAuditsCompletedMsg, ExceptionMsg, ResultMsg, AuditStartMsg, NoStudentsMsg]


def audit(
    *,
    spec: Dict[str, Any],
    transcript: Sequence[CourseInstance],
    constants: Constants,
    exceptions: Sequence[RuleException],
    area_pointers: Sequence[AreaPointer],
    print_all: bool,
    other_areas: Sequence[AreaPointer],
    estimate_only: bool,
) -> Iterator[Message]:  # noqa: C901
    area = AreaOfStudy.load(specification=spec, c=constants, other_areas=other_areas)
    area.validate()

    _transcript = []
    attributes_to_attach: Dict[str, List[str]] = area.attributes.get("courses", {})
    for c in transcript:
        # We need to leave repeated courses in the transcript, because some majors (THEAT) require repeated courses
        # for completion.
        attrs_by_course: Set[str] = set(attributes_to_attach.get(c.course(), []))
        attrs_by_shorthand: Set[str] = set(attributes_to_attach.get(c.course_shorthand(), []))
        attrs_by_term: Set[str] = set(attributes_to_attach.get(c.course_with_term(), []))

        c = c.attach_attrs(attributes=attrs_by_course | attrs_by_shorthand | attrs_by_term)
        _transcript.append(c)

    this_transcript = tuple(_transcript)

    best_sol: Optional[AreaResult] = None
    total_count = 0
    iterations: List[float] = []
    start_time = datetime.now()
    start = time.perf_counter()
    iter_start = time.perf_counter()
    startup_time = 0.00

    # estimate = area.estimate(transcript=this_transcript, areas=tuple(area_pointers))
    # yield EstimateMsg(estimate=estimate)

    if estimate_only:
        return

    for sol in area.solutions(transcript=this_transcript, areas=tuple(area_pointers), exceptions=tuple(exceptions)):
        if total_count == 0:
            startup_time = time.perf_counter() - iter_start
            iter_start = time.perf_counter()

        total_count += 1

        if total_count % 1_000 == 0:
            yield ProgressMsg(
                count=total_count,
                recent_iters=iterations[-1_000:],
                start_time=start_time,
                best_rank=cast(AreaResult, best_sol).rank(),
            )

        result = sol.audit()

        if print_all:
            yield ResultMsg(
                result=result,
                transcript=this_transcript,
                count=total_count,
                elapsed='∞',
                iterations=[],
                startup_time=startup_time,
            )

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

    if not best_sol:
        yield NoAuditsCompletedMsg()
        return

    end = time.perf_counter()
    elapsed = pretty_ms((end - start) * 1000)

    yield ResultMsg(
        result=best_sol,
        transcript=this_transcript,
        count=total_count,
        elapsed=elapsed,
        iterations=iterations,
        startup_time=startup_time,
    )
