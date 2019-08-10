from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Sequence
import logging

from .base import Rule, Solution
from .clause import SingleClause
from .constants import Constants
from .context import RequirementContext
from .data import CourseInstance, AreaPointer, AreaType
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
    attributes: Dict
    multicountable: List

    @staticmethod
    def load(*, specification: Dict, c: Constants, other_areas: Sequence[AreaPointer] = tuple()):
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
        multicountable = []
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

    def validate(self):
        ctx = RequirementContext()

        self.result.validate(ctx=ctx)

    def solutions(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]):
        path = ["$root"]
        logger.debug("%s evaluating area.result", path)

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            logger.debug("%s evaluating area.result with limited transcript %s", path, limited_transcript)

            ctx = RequirementContext(transcript=limited_transcript, areas=areas, multicountable=self.multicountable)

            for sol in self.result.solutions(ctx=ctx):
                ctx.reset_claims()
                yield AreaSolution(solution=sol, area=self)

        logger.debug("%s all solutions generated", path)

    def estimate(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]):
        iterations = 0

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            ctx = RequirementContext(transcript=limited_transcript, areas=areas, multicountable=self.multicountable)

            iterations += self.result.estimate(ctx=ctx)

        return iterations


@dataclass(frozen=True)
class AreaSolution:
    solution: Solution
    area: AreaOfStudy

    def audit(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]):
        ctx = RequirementContext(transcript=transcript, areas=areas, multicountable=self.area.multicountable)

        return self.solution.audit(ctx=ctx)
