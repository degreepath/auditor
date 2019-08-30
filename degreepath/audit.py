import attr
from typing import List, Optional, Tuple, Sequence, Iterator, Union, Dict, Any, cast
from datetime import datetime
from decimal import Decimal
import time

from .constants import Constants
from .exception import RuleException
from .area import AreaOfStudy, AreaResult
from .ms import pretty_ms
from .data import CourseInstance, AreaPointer
from .discover_potentials import discover_clause_potential


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class Arguments:
    area_files: List[str]
    student_files: List[str]
    print_all: bool = False
    estimate_only: bool = False


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class NoStudentsMsg:
    pass


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AuditStartMsg:
    stnum: str
    area_code: str
    area_catalog: str


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ResultMsg:
    result: AreaResult
    transcript: Tuple[CourseInstance, ...]
    count: int
    elapsed: str
    iterations: List[float]
    startup_time: float
    potentials_for_all_clauses: Dict[int, List[str]]


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ExceptionMsg:
    ex: Exception
    tb: str


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class NoAuditsCompletedMsg:
    pass


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ProgressMsg:
    count: int
    recent_iters: List[float]
    start_time: datetime
    best_rank: Union[int, Decimal]


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class EstimateMsg:
    estimate: int


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AreaFileNotFoundMsg:
    area_file: str
    stnum: str


Message = Union[EstimateMsg, ProgressMsg, NoAuditsCompletedMsg, ExceptionMsg, ResultMsg, AuditStartMsg, NoStudentsMsg, AreaFileNotFoundMsg]


def audit(
    *,
    area: AreaOfStudy,
    transcript: Tuple[CourseInstance, ...],
    constants: Constants,
    exceptions: Sequence[RuleException],
    area_pointers: Sequence[AreaPointer],
    print_all: bool,
    estimate_only: bool,
) -> Iterator[Message]:  # noqa: C901
    best_sol: Optional[AreaResult] = None
    total_count = 0
    iterations: List[float] = []
    start_time = datetime.now()
    start = time.perf_counter()
    iter_start = time.perf_counter()
    startup_time = 0.00

    potentials_for_all_clauses = discover_clause_potential(area, c=constants)

    # estimate = area.estimate(transcript=this_transcript, areas=tuple(area_pointers))
    # yield EstimateMsg(estimate=estimate)

    if estimate_only:
        return

    for sol in area.solutions(transcript=transcript, areas=tuple(area_pointers), exceptions=tuple(exceptions)):
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
                transcript=transcript,
                count=total_count,
                elapsed='∞',
                iterations=[],
                startup_time=startup_time,
                potentials_for_all_clauses=potentials_for_all_clauses,
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
        transcript=transcript,
        count=total_count,
        elapsed=elapsed,
        iterations=iterations,
        startup_time=startup_time,
        potentials_for_all_clauses=potentials_for_all_clauses,
    )
