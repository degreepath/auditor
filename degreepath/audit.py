import attr
from typing import List, Optional, Tuple, Sequence, Iterator, Union, Dict, Any
from datetime import datetime
from decimal import Decimal
import time

from .constants import Constants
from .exception import RuleException
from .area import AreaOfStudy, AreaResult
from .ms import pretty_ms
from .data import CourseInstance, AreaPointer, MusicAttendance, MusicPerformance, MusicProficiencies
from .discover_potentials import discover_clause_potential


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class Arguments:
    area_files: List[str]
    student_files: List[str]
    archive_file: Optional[str]
    print_all: bool = False


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class NoStudentsMsg:
    pass


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AuditStartMsg:
    stnum: str
    area_code: str
    area_catalog: str
    student: Dict[str, Any]


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
    stnum: Optional[str]
    area_code: Optional[str]


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
class AreaFileNotFoundMsg:
    area_file: str
    stnum: str


Message = Union[ProgressMsg, NoAuditsCompletedMsg, ExceptionMsg, ResultMsg, AuditStartMsg, NoStudentsMsg, AreaFileNotFoundMsg]


def audit(
    *,
    area: AreaOfStudy,
    area_pointers: Sequence[AreaPointer] = tuple(),
    args: Arguments = Arguments(),
    constants: Constants,
    exceptions: Sequence[RuleException] = tuple(),
    music_attendances: Tuple[MusicAttendance, ...] = tuple(),
    music_performances: Tuple[MusicPerformance, ...] = tuple(),
    music_proficiencies: MusicProficiencies = MusicProficiencies(),
    transcript: Tuple[CourseInstance, ...] = tuple(),
    transcript_with_failed: Tuple[CourseInstance, ...] = tuple(),
    print_all: bool,
) -> Iterator[Message]:  # noqa: C901
    best_sol: Optional[AreaResult] = None
    best_rank: Union[int, Decimal] = 0
    total_count = 0
    iterations: List[float] = []
    start_time = datetime.now()
    start = time.perf_counter()
    iter_start = time.perf_counter()
    startup_time = 0.00

    potentials_for_all_clauses = discover_clause_potential(area, c=constants)

    for sol in area.solutions(
        transcript=transcript,
        areas=tuple(area_pointers),
        music_performances=music_performances,
        music_attendances=music_attendances,
        music_proficiencies=music_proficiencies,
        exceptions=list(exceptions),
        transcript_with_failed=transcript_with_failed,
    ):
        if total_count == 0:
            startup_time = time.perf_counter() - iter_start
            iter_start = time.perf_counter()

        total_count += 1

        if total_count % 1_000 == 0:
            yield ProgressMsg(
                count=total_count,
                recent_iters=iterations[-1_000:],
                start_time=start_time,
                best_rank=best_sol.rank() if best_sol else 0,
            )

        result = sol.audit()
        result_rank = result.rank()

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
            best_sol, best_rank = result, result_rank
        elif result_rank > best_rank:
            best_sol, best_rank = result, result_rank

        if result.ok():
            best_sol, best_rank = result, result_rank
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
