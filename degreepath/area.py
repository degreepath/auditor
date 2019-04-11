from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging

from .rule import Rule, load_rule
from .data import CourseInstance
from .requirement import RequirementContext


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""

    name: str
    kind: str
    degree: Optional[str]
    catalog: str

    result: Rule

    attributes: Dict

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.kind,
            "degree": self.degree,
            "catalog": self.catalog,
            "result": self.result.to_dict(),
            "attributes": self.attributes,
        }

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        result = load_rule(data["result"])

        return AreaOfStudy(
            name=data["name"],
            catalog=data["catalog"],
            degree=data.get("degree", None),
            kind=data["type"],
            result=result,
            attributes=data.get("attributes", {}),
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

        ctx = RequirementContext(transcript=[])

        self.result.validate(ctx=ctx)

    def solutions(self, *, transcript: List[CourseInstance]):
        path = ["$root"]
        logging.debug(f"{path}\n\tevaluating area.result")

        ctx = RequirementContext(transcript=transcript)

        new_path = [*path, ".result"]
        for sol in self.result.solutions(ctx=ctx, path=new_path):
            yield AreaSolution(solution=sol, area=self)

        logging.debug(f"{path}\n\tall solutions generated")


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
        logging.debug(f"{path}\n\tauditing area.result")

        ctx = RequirementContext(transcript=transcript)

        new_path = [*path, ".result"]

        return self.solution.audit(ctx=ctx)


# @dataclass(frozen=True)
# class AreaOfStudy:
#     """The overall class for working with an area"""

#     name: str
#     kind: str
#     degree: Optional[str]
#     catalog: str

#     result: Rule
#     requirements: Dict[str, Requirement]

#     attributes: Dict

#     def to_dict(self):
#         return {
#             "name": self.name,
#             "type": self.kind,
#             "degree": self.degree,
#             "catalog": self.catalog,
#             "result": self.result.to_dict(),
#             "requirements": {
#                 name: r.to_dict() for name, r in self.requirements.items()
#             },
#             "attributes": self.attributes,
#         }

#     @staticmethod
#     def load(data: Dict) -> AreaOfStudy:
#         requirements = {
#             name: Requirement.load(name, r)
#             for name, r in data.get("requirements", {}).items()
#         }
#         result = load_rule(data["result"])

#         return AreaOfStudy(
#             name=data["name"],
#             catalog=data["catalog"],
#             degree=data.get("degree", None),
#             kind=data["type"],
#             requirements=requirements,
#             result=result,
#             attributes=data.get("attributes", {}),
#         )

#     def validate(self):
#         assert isinstance(self.name, str)
#         assert self.name.strip() != ""

#         assert isinstance(self.kind, str)
#         assert self.kind in ["degree", "major", "concentration"]

#         assert isinstance(self.catalog, str)
#         assert self.catalog.strip() != ""

#         if self.kind != "degree":
#             assert isinstance(self.degree, str)
#             assert self.degree.strip() != ""
#             assert self.degree in ["Bachelor of Arts", "Bachelor of Music"]

#         ctx = RequirementContext(
#             transcript=[], save_rules={}, requirements=self.requirements
#         )

#         self.result.validate(ctx=ctx)

#     def solutions(self, *, transcript: List[CourseInstance]):
#         path = ["$root"]
#         logging.debug(f"{path}\n\tevaluating area.result")

#         ctx = RequirementContext(
#             transcript=transcript,
#             save_rules={},
#             requirements={name: r for name, r in self.requirements.items()},
#         )

#         new_path = [*path, ".result"]
#         for sol in self.result.solutions(ctx=ctx, path=new_path):
#             yield AreaSolution(solution=sol, area=self)

#         logging.debug(f"{path}\n\tall solutions generated")


# @dataclass(frozen=True)
# class AreaSolution:
#     solution: Any
#     area: AreaOfStudy

#     def to_dict(self):
#         return {
#             **self.area.to_dict(),
#             "type": "area",
#             "result": self.solution.to_dict(),
#         }

#     def audit(self, *, transcript: List[CourseInstance]):
#         path = ["$root"]
#         logging.debug(f"{path}\n\tauditing area.result")

#         ctx = RequirementContext(
#             transcript=transcript,
#             save_rules={},
#             requirements={name: r for name, r in self.area.requirements.items()},
#         )

#         new_path = [*path, ".result"]
