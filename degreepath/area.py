from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict
from .rule import Rule
from .requirement import Requirement


@dataclass(frozen=True)
class AreaOfStudy:
    """The overall class for working with an area"""

    name: str
    kind: str
    degree: Optional[str]
    catalog: str

    result: Rule
    requirements: List[Requirement]

    @staticmethod
    def load(data: Dict) -> AreaOfStudy:
        requirements = [Requirement.load(r) for r in data["requirements"]]
        result = Rule.load(data["result"])

        return AreaOfStudy(
            name=data["name"],
            catalog=data["catalog"],
            degree=data["degree"],
            kind=data["type"],
            requirements=requirements,
            result=result,
        )

    def validate(self):
        assert isinstance(self.name, str)
        assert self.name.strip() != ""

        assert isinstance(self.kind, str)
        assert self.kind in ["degree", "major", "concentration"]

        assert isinstance(self.catalog, str)
        assert self.catalog.strip() != ""

        if self.kind == "degree":
            assert isinstance(self.degree, str)
            assert self.degree.strip() != ""
            assert self.degree in ["Bachelor of Arts", "Bachelor of Music"]

        self.result.validate(requirements=self.requirements)

        for req in self.requirements:
            req.validate()
