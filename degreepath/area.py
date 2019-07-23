from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Union
import logging

from .rule import Rule, load_rule, CourseRule
from .data import CourseInstance
from .limit import Limit
from .clause import SingleClause, Clause
from .requirement import RequirementContext, Requirement
from .constants import Constants

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""
    limit: Tuple
    result: Rule
    requirements: Dict
    attributes: Dict
    multicountable: List

    def to_dict(self):
        return {
            "limit": [l.to_dict() for l in self.limit],
            "result": self.result.to_dict(),
            "requirements": {name: r.to_dict() for name, r in self.requirements.items()},
            "attributes": self.attributes,
        }

    @staticmethod
    def load(*, specification: Dict, c: Constants):
        requirements = {
            name: Requirement.load(name, r, c)
            for name, r in specification.get("requirements", {}).items()
        }

        result = load_rule(specification["result"], c)
        limit = tuple(Limit.load(l, c) for l in specification.get("limit", []))

        attributes = specification.get("attributes", dict())
        multicountable = []
        for ruleset in attributes.get("multicountable", []):
            clauses = []
            for clause in ruleset:
                if "course" in clause:
                    item = CourseRule.load(clause, c)
                elif "attributes" in clause:
                    item = SingleClause.load("attributes", clause["attributes"], c)
                else:
                    raise Exception(f"invalid multicountable {clause}")
                clauses.append(item)
            multicountable.append(clauses)

        return AreaOfStudy(
            requirements=requirements,
            result=result,
            attributes=attributes,
            multicountable=multicountable,
            limit=limit,
        )

    def validate(self):
        ctx = RequirementContext(requirements=self.requirements)

        self.result.validate(ctx=ctx)

    # def limited_transcripts(self, transcript: List[CourseInstance]):

    def solutions(self, *, transcript: Tuple[CourseInstance, ...]):
        path = ["$root"]
        logger.debug("{} evaluating area.result", path)

        # TODO: generate alternate sizes of solution based on the courses subject to the limits
        # for limited_transcript in

        ctx = RequirementContext(
            transcript=transcript,
            requirements={name: r for name, r in self.requirements.items()},
            multicountable=self.multicountable,
        )

        new_path = [*path, ".result"]
        for sol in self.result.solutions(ctx=ctx, path=new_path):
            ctx.reset_claims()
            logger.info("generated new area solution: {}", sol)
            yield AreaSolution(solution=sol, area=self)

        logger.debug("{} all solutions generated", path)

    def estimate(self, *, transcript: Tuple[CourseInstance, ...]):
        ctx = RequirementContext(
            transcript=transcript,
            requirements={name: r for name, r in self.requirements.items()},
            multicountable=self.multicountable,
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

    def audit(self, *, transcript: Tuple[CourseInstance, ...]):
        path = ["$root"]
        logger.debug("{} auditing area.result", path)

        ctx = RequirementContext(
            transcript=transcript,
            requirements={name: r for name, r in self.area.requirements.items()},
        )

        new_path = [*path, ".result"]

        return self.solution.audit(ctx=ctx, path=new_path)
