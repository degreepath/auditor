from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional
import logging

from .clause import SingleClause
from .constants import Constants
from .context import RequirementContext
from .data import CourseInstance, AreaPointer, AreaType
from .limit import LimitSet
from .load_rule import Rule, load_rule

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

    def to_dict(self):
        return {
            "type": "area",
            "limit": [l.to_dict() for l in self.limit],
            "result": self.result.to_dict(),
            "attributes": self.attributes,
        }

    @staticmethod
    def load(*, specification: Dict, c: Constants, other_areas: Tuple[AreaPointer, ...]):
        emphases = specification.get('emphases', {})
        taken_emphases = set(str(a.code) for a in other_areas if a.kind is AreaType.Emphasis)

        result = load_rule(
            data=specification["result"],
            c=c,
            children=specification.get("requirements", {}),
            emphases=[v for k, v in emphases.items() if str(k) in taken_emphases],
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

            new_path = [*path, ".result"]
            for sol in self.result.solutions(ctx=ctx, path=new_path):
                ctx.reset_claims()
                yield AreaSolution(solution=sol, area=self)

        logger.debug("%s all solutions generated", path)


@dataclass(frozen=True)
class AreaSolution:
    solution: Any
    area: AreaOfStudy

    def to_dict(self):
        return {
            **self.area.to_dict(),
            "type": "area",
            "result": self.solution.to_dict(),
        }

    def audit(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]):
        path = ["$root"]

        ctx = RequirementContext(transcript=transcript, areas=areas, multicountable=self.area.multicountable)

        return self.solution.audit(ctx=ctx, path=path)
