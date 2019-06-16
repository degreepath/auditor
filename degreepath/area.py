from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import logging

from .rule import Rule, load_rule
from .data import CourseInstance
from .limit import Limit
from .requirement import RequirementContext, Requirement

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""

    name: str
    kind: str
    degree: Optional[str]
    catalog: str

    limit: Tuple[Limit, ...]
    result: Rule
    requirements: Dict[str, Requirement]

    attributes: Dict

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.kind,
            "degree": self.degree,
            "catalog": self.catalog,
            "limit": [l.to_dict() for l in self.limit],
            "result": self.result.to_dict(),
            "requirements": {
                name: r.to_dict() for name, r in self.requirements.items()
            },
            "attributes": self.attributes,
        }

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        requirements = {
            name: Requirement.load(name, r)
            for name, r in data.get("requirements", {}).items()
        }
        result = load_rule(data["result"])
        limit = tuple(Limit.load(l) for l in data.get('limit', []))

        return AreaOfStudy(
            name=data["name"],
            catalog=data["catalog"],
            degree=data.get("degree", None),
            kind=data["type"],
            requirements=requirements,
            result=result,
            attributes=data.get("attributes", {}),
            limit=limit,
        )

    def validate(self):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        assert isinstance(self.kind, str)
        assert self.kind in ["degree", "major", "concentration"]

        assert isinstance(self.catalog, str)
        assert self.catalog.strip() != ""

        if self.kind != "degree":
            assert isinstance(self.degree, str)
            assert self.degree.strip() != ""
            assert self.degree in ["Bachelor of Arts", "Bachelor of Music"]

        ctx = RequirementContext(requirements=self.requirements)

        self.result.validate(ctx=ctx)

    # def limited_transcripts(self, transcript: List[CourseInstance]):

    def solutions(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logger.debug(f"{path} evaluating area.result")

        # TODO: generate alternate sizes of solution based on the courses subject to the limits
        # for limited_transcript in

        ctx = RequirementContext(
            transcript=transcript,
            requirements={name: r for name, r in self.requirements.items()},
        )

        new_path = [*path, ".result"]
        for sol in self.result.solutions(ctx=ctx, path=new_path):
            logger.info(f"generated new area solution: {sol}")
            yield AreaSolution(solution=sol, area=self)

        logger.debug(f"{path} all solutions generated")

    def estimate(self, *, transcript: List[CourseInstance]):
        ctx = RequirementContext(
            transcript=transcript,
            requirements={name: r for name, r in self.requirements.items()},
        )

        return self.result.estimate(ctx=ctx)


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

    def audit(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logger.debug(f"{path} auditing area.result")

        ctx = RequirementContext(
            transcript=transcript,
            requirements={name: r for name, r in self.area.requirements.items()},
        )

        new_path = [*path, ".result"]

        return self.solution.audit(ctx=ctx, path=new_path)
