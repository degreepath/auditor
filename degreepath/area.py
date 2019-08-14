from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Sequence, Iterable, Any, TYPE_CHECKING
import logging
import decimal

from .base import Rule, Solution, Result, Base
from .clause import SingleClause
from .constants import Constants
from .context import RequirementContext
from .data import CourseInstance, AreaPointer, AreaType
from .exception import RuleException
from .limit import LimitSet
from .load_rule import load_rule
from .lib import grade_point_average

if TYPE_CHECKING:
    from .claim import ClaimAttempt  # noqa: F401

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AreaOfStudy(Base):
    """The overall class for working with an area"""
    __slots__ = ('name', 'kind', 'catalog', 'major', 'degree', 'limit', 'result', 'attributes', 'multicountable', 'path')
    name: str
    kind: str
    catalog: str
    major: Optional[str]
    degree: Optional[str]

    limit: LimitSet
    result: Rule
    attributes: Dict[str, Dict[str, List[str]]]
    multicountable: List[List[SingleClause]]
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "kind": self.kind,
            "catalog": self.catalog,
            "major": self.major,
            "degree": self.degree,
            "result": self.result.to_dict() if self.result is not None else None,
            "gpa": str(self.gpa()),
        }

    def type(self) -> str:
        return "area"

    def gpa(self) -> decimal.Decimal:
        return decimal.Decimal('0.00')

    @staticmethod
    def load(*, specification: Dict, c: Constants, other_areas: Sequence[AreaPointer] = tuple()) -> 'AreaOfStudy':
        emphases = specification.get('emphases', {})
        declared_emphases = set(str(a.code) for a in other_areas if a.kind is AreaType.Emphasis)

        result = load_rule(
            data=specification["result"],
            c=c,
            children=specification.get("requirements", {}),
            emphases=[v for k, v in emphases.items() if str(k) in declared_emphases],
            path=["$"],
        )
        limit = LimitSet.load(data=specification.get("limit", None), c=c)

        attributes = specification.get("attributes", dict())
        multicountable: List[List[SingleClause]] = []
        for ruleset in attributes.get("multicountable", []):
            clauses = []
            for clause in ruleset:
                if "course" in clause:
                    item = SingleClause.load('course', clause['course'], c)
                elif "attributes" in clause:
                    item = SingleClause.load("attributes", clause["attributes"], c)
                else:
                    raise Exception(f"invalid multicountable {clause}")
                clauses.append(item)
            multicountable.append(clauses)

        return AreaOfStudy(
            name=specification.get('name', 'Test'),
            kind=specification.get('type', 'test'),
            catalog=specification.get('catalog', '2000-01'),
            major=specification.get('major', None),
            degree=specification.get('degree', None),
            result=result,
            attributes=attributes,
            multicountable=multicountable,
            limit=limit,
            path=('$',)
        )

    def validate(self) -> None:
        ctx = RequirementContext()

        self.result.validate(ctx=ctx)

    def solutions(
        self, *,
        transcript: Sequence[CourseInstance],
        areas: Sequence[AreaPointer],
        exceptions: Sequence[RuleException],
    ) -> Iterable['AreaSolution']:
        logger.debug("evaluating area.result")

        mapped_exceptions = map_exceptions(exceptions)

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            limited_transcript = tuple(sorted(limited_transcript))

            logger.debug("%s evaluating area.result with limited transcript", limited_transcript)

            ctx = RequirementContext(
                areas=tuple(areas),
                exceptions=mapped_exceptions,
                multicountable=self.multicountable,
            ).with_transcript(limited_transcript)

            for sol in self.result.solutions(ctx=ctx):
                ctx.reset_claims()
                yield AreaSolution.from_area(solution=sol, area=self, ctx=ctx)

        logger.debug("all solutions generated")

    def estimate(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]) -> int:
        iterations = 0

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            ctx = RequirementContext(
                areas=areas,
                multicountable=self.multicountable,
            ).with_transcript(limited_transcript)

            iterations += self.result.estimate(ctx=ctx)

        return iterations


@dataclass(frozen=True)
class AreaSolution(AreaOfStudy):
    __slots__ = ('solution', 'context')
    solution: Solution
    context: RequirementContext

    @staticmethod
    def from_area(*, area: AreaOfStudy, solution: Solution, ctx: RequirementContext) -> 'AreaSolution':
        return AreaSolution(
            name=area.name,
            kind=area.kind,
            catalog=area.catalog,
            major=area.major,
            degree=area.degree,
            limit=area.limit,
            result=area.result,
            attributes=area.attributes,
            multicountable=area.multicountable,
            path=area.path,
            solution=solution,
            context=ctx,
        )

    def audit(self) -> 'AreaResult':
        return AreaResult.from_solution(area=self, result=self.solution.audit(ctx=self.context), ctx=self.context)


@dataclass(frozen=True)
class AreaResult(AreaOfStudy, Result):
    __slots__ = ('result', 'context')
    result: Result
    context: RequirementContext

    @staticmethod
    def from_solution(*, area: AreaOfStudy, result: Result, ctx: RequirementContext) -> 'AreaResult':
        return AreaResult(
            name=area.name,
            kind=area.kind,
            catalog=area.catalog,
            major=area.major,
            degree=area.degree,
            limit=area.limit,
            attributes=area.attributes,
            multicountable=area.multicountable,
            path=area.path,
            context=ctx,
            result=result,
        )

    def gpa(self) -> decimal.Decimal:
        if not self.result:
            return decimal.Decimal('0.00')

        transcript_map = {c.clbid: c for c in self.context.transcript()}

        if self.kind == 'degree':
            courses = list(transcript_map.values())
        else:
            courses = [transcript_map[c.claim.clbid] for c in self.claims() if c.failed() is False]

        return grade_point_average(courses)

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.result.ok()

    def rank(self) -> int:
        return self.result.rank()

    def max_rank(self) -> int:
        return self.result.max_rank()

    def claims(self) -> List['ClaimAttempt']:
        return self.result.claims()

    def was_overridden(self) -> bool:
        return self.result.was_overridden()


def map_exceptions(exceptions: Sequence[RuleException]) -> Dict[Tuple[str, ...], RuleException]:
    mapped_exceptions: Dict[Tuple[str, ...], RuleException] = dict()

    for e in exceptions:
        path = tuple(e.path)
        if path in mapped_exceptions:
            raise ValueError(f'expected only one exception per path: {e}')
        else:
            mapped_exceptions[path] = e

    return mapped_exceptions
