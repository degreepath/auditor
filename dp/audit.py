import attr
from typing import List, Optional, Tuple, Iterator, Union, Dict
from decimal import Decimal
import time

from .constants import Constants
from .exception import RuleException
from .area import AreaOfStudy, AreaResult
from .data import CourseInstance, Student
from .status import WAIVED_AND_DONE


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class Arguments:
    transcript_only: bool = False
    estimate_only: bool = False
    gpa_only: bool = False

    print_all: bool = False
    stop_after: Optional[int] = None
    progress_every: int = 1_000
    audit_each: int = 1


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ResultMsg:
    result: AreaResult
    best_i: Optional[int]
    transcript: Tuple[CourseInstance, ...]
    iters: int
    total_iters: int
    avg_iter_ms: float
    elapsed_ms: float


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class NoAuditsCompletedMsg:
    pass


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class EstimateMsg:
    estimate: int


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ProgressMsg:
    best_rank: Decimal
    best_i: Optional[int]
    iters: int
    total_iters: int
    avg_iter_ms: float
    elapsed_ms: float


Message = Union[
    EstimateMsg,
    NoAuditsCompletedMsg,
    ProgressMsg,
    ResultMsg,
]


def audit(*, area: AreaOfStudy, student: Student, args: Optional[Arguments] = None, exceptions: Optional[List[RuleException]] = None) -> Iterator[Message]:
    if not args:
        args = Arguments()

    start = time.perf_counter()
    total_count = 0
    audit_count = 0

    best_sol: Optional[AreaResult] = None
    best_rank: Decimal = Decimal(0)
    best_i: Optional[int] = None

    estimate = area.estimate(student=student, exceptions=exceptions or [])
    yield EstimateMsg(estimate=estimate)

    if args.estimate_only:
        return

    for sol in area.solutions(student=student, exceptions=exceptions or []):
        if total_count == 0:
            # ignore startup time
            start = time.perf_counter()

        total_count += 1

        if total_count % args.audit_each != 0:
            continue

        audit_count += 1

        result = sol.audit()
        result_rank, _result_max = result.rank()
        status = result.status()

        # if this is the first solution, store it, because it's the best so far
        if best_sol is None:
            best_sol, best_rank, best_i = result, result_rank, total_count

        # if the current solution is better, then store it
        if result_rank > best_rank:
            best_sol, best_rank, best_i = result, result_rank, total_count

        # if the current solution is OK, then store it, and end the loop
        if status in WAIVED_AND_DONE:
            best_sol, best_rank, best_i = result, result_rank, total_count
            break

        if audit_count % args.progress_every == 0:
            elapsed_ms = ms_since(start)
            yield ProgressMsg(
                best_rank=best_rank,
                best_i=best_i,
                iters=audit_count,
                total_iters=total_count,
                avg_iter_ms=elapsed_ms / audit_count,
                elapsed_ms=elapsed_ms,
            )

        if args.print_all:
            elapsed_ms = ms_since(start)
            yield ResultMsg(
                result=result,
                best_i=best_i,
                transcript=student.courses,
                iters=audit_count,
                total_iters=total_count,
                avg_iter_ms=elapsed_ms / audit_count,
                elapsed_ms=elapsed_ms,
            )

        if args.stop_after is not None and audit_count >= args.stop_after:
            break

    if not best_sol:
        yield NoAuditsCompletedMsg()
        return

    elapsed_ms = ms_since(start)
    yield ResultMsg(
        result=best_sol,
        best_i=best_i,
        transcript=student.courses,
        iters=audit_count,
        total_iters=total_count,
        avg_iter_ms=elapsed_ms / audit_count,
        elapsed_ms=elapsed_ms,
    )


def ms_since(start: float, *, now: Optional[float] = None) -> float:
    if now is None:
        now = time.perf_counter()
    return (now - start) * 1000


def find_potentials(area: AreaOfStudy, constants: Constants) -> Dict[int, List[str]]:
    return {}

    # if not os.getenv('POTENTIALS_URL', None):
    #     return {}
    #
    # from .discover_potentials import discover_clause_potential
    # return discover_clause_potential(area, c=constants)
