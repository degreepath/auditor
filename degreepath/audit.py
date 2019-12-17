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


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class Arguments:
    area_files: Sequence[str] = tuple()
    student_files: Sequence[str] = tuple()
    db_file: Optional[str] = None
    student_data: Sequence[dict] = tuple()
    area_specs: Sequence[Tuple[dict, str]] = tuple()

    transcript_only: bool = False
    estimate_only: bool = False
    gpa_only: bool = False

    print_all: bool = False
    stop_after: Optional[int] = None
    progress_every: int = 1_000


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
    elapsed_ms: float
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
class EstimateMsg:
    estimate: int


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ProgressMsg:
    count: int
    recent_iters: List[float]
    start_time: datetime
    best_rank: Union[int, Decimal]


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class AreaFileNotFoundMsg:
    area_file: str
    stnums: Sequence[str]


Message = Union[
    AreaFileNotFoundMsg,
    AuditStartMsg,
    EstimateMsg,
    ExceptionMsg,
    NoAuditsCompletedMsg,
    NoStudentsMsg,
    ProgressMsg,
    ResultMsg,
]


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
) -> Iterator[Message]:  # noqa: C901
    best_sol: Optional[AreaResult] = None
    best_rank: Union[int, Decimal] = 0
    total_count = 0
    iterations: List[float] = []
    start_time = datetime.now()
    start = time.perf_counter()
    iter_start = time.perf_counter()
    startup_time = 0.00

    estimate = area.estimate(
        transcript=transcript,
        areas=tuple(area_pointers),
        music_performances=music_performances,
        music_attendances=music_attendances,
        music_proficiencies=music_proficiencies,
        exceptions=list(exceptions),
        transcript_with_failed=transcript_with_failed,
    )
    yield EstimateMsg(estimate=estimate)

    if args.estimate_only:
        return

    potentials_for_all_clauses = find_potentials(area, constants)

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
            iter_start = time.perf_counter()
            startup_time = time.perf_counter() - iter_start

        total_count += 1

        if total_count % args.progress_every == 0:
            yield ProgressMsg(
                count=total_count,
                recent_iters=iterations[-args.progress_every:],
                start_time=start_time,
                best_rank=best_sol.rank() if best_sol else 0,
            )

        result = sol.audit()
        result_rank = result.rank()

        if args.print_all:
            yield ResultMsg(
                result=result,
                transcript=transcript,
                count=total_count,
                elapsed='∞',
                elapsed_ms=0,
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

        if args.stop_after is not None and total_count >= args.stop_after:
            break

    if not best_sol:
        yield NoAuditsCompletedMsg()
        return

    end = time.perf_counter()
    elapsed_ms = (end - start) * 1000
    elapsed = pretty_ms(elapsed_ms)

    yield ResultMsg(
        result=best_sol,
        transcript=transcript,
        count=total_count,
        elapsed=elapsed,
        elapsed_ms=elapsed_ms,
        iterations=iterations,
        startup_time=startup_time,
        potentials_for_all_clauses=potentials_for_all_clauses,
    )


def find_potentials(area: AreaOfStudy, constants: Constants) -> Dict[int, List[str]]:
    return {}

    # if not os.getenv('POTENTIALS_URL', None):
    #     return {}
    #
    # from .discover_potentials import discover_clause_potential
    # return discover_clause_potential(area, c=constants)
