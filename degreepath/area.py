from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Sequence, Iterable
import logging

from .base import Rule, Solution, Result
from .clause import SingleClause
from .constants import Constants
from .context import RequirementContext
from .data import CourseInstance, AreaPointer, AreaType
from .exception import RuleException
from .limit import LimitSet
from .load_rule import load_rule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""
    name: str
    type: str
    catalog: str
    major: Optional[str]
    degree: Optional[str]

    limit: LimitSet
    result: Rule
    attributes: Dict[str, List[str]]
    multicountable: List[List[SingleClause]]

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
            type=specification.get('type', 'test'),
            catalog=specification.get('catalog', '2000-01'),
            major=specification.get('major', None),
            degree=specification.get('degree', None),
            result=result,
            attributes=attributes,
            multicountable=multicountable,
            limit=limit,
        )

    def validate(self) -> None:
        ctx = RequirementContext()

        self.result.validate(ctx=ctx)

    def solutions(
        self, *,
        transcript: Tuple[CourseInstance, ...],
        areas: Tuple[AreaPointer, ...],
        exceptions: Tuple[RuleException, ...],
    ) -> Iterable['AreaSolution']:
        logger.debug("evaluating area.result")

        mapped_exceptions = map_exceptions(exceptions)

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            limited_transcript = tuple(sorted(limited_transcript))

            logger.debug("%s evaluating area.result with limited transcript", limited_transcript)

            ctx = RequirementContext(areas=areas, exceptions=mapped_exceptions, multicountable=self.multicountable).with_transcript(limited_transcript)

            for sol in self.result.solutions(ctx=ctx):
                ctx.reset_claims()
                yield AreaSolution.from_area(solution=sol, area=self, ctx=ctx)

        logger.debug("all solutions generated")

    def estimate(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]) -> int:
        iterations = 0

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            ctx = RequirementContext(areas=areas, multicountable=self.multicountable).with_transcript(limited_transcript)

            iterations += self.result.estimate(ctx=ctx)

        return iterations


@dataclass(frozen=True)
class AreaSolution(AreaOfStudy):
    solution: Solution
    context: RequirementContext

    def from_area(*, area: AreaOfStudy, solution: Solution, ctx: RequirementContext) -> 'AreaSolution':
        return AreaSolution(
            name=area.name,
            type=area.type,
            catalog=area.catalog,
            major=area.major,
            degree=area.degree,
            limit=area.limit,
            result=area.result,
            attributes=area.attributes,
            multicountable=area.multicountable,
            solution=solution,
            context=ctx,
        )

    def audit(self) -> Result:
        return self.solution.audit(ctx=self.context)


def map_exceptions(exceptions: Sequence[RuleException]) -> Dict[Tuple[str, ...], RuleException]:
    mapped_exceptions: Dict[Tuple[str, ...], RuleException] = dict()

    for e in exceptions:
        path = tuple(e.path)
        if path in mapped_exceptions:
            raise ValueError(f'expected only one exception per path: {e}')
        else:
            mapped_exceptions[path] = e

    return mapped_exceptions
