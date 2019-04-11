from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..requirement import RequirementContext
from ..solution import CourseSolution


@dataclass(frozen=True)
class ReferenceRule:
    requirement: str

    def to_dict(self):
        return {"type": "reference", "name": self.requirement}

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "requirement" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> ReferenceRule:
        return ReferenceRule(requirement=data["requirement"])

    def validate(self, *, ctx: RequirementContext):
        if self.requirement not in ctx.requirements:
            reqs = ", ".join(ctx.requirements.keys())
            raise AssertionError(
                f"expected a requirement named '{self.requirement}', but did not find one [options: {reqs}]"
            )

        ctx.requirements[self.requirement].validate(ctx=ctx)

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        logging.debug(f'{path}\n\treference to requirement "{self.requirement}"')

        requirement = ctx.requirements[self.requirement]

        logging.debug(f'{path}\n\tfound requirement "{self.requirement}"')

        yield from requirement.solutions(
            ctx=ctx, path=[*path, f"$ref->{self.requirement}"]
        )
