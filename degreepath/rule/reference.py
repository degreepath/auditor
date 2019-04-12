from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..requirement import RequirementState
from ..solution import CourseSolution

if TYPE_CHECKING:
    from ..requirement import RequirementContext


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
        requirement = ctx.requirements[self.requirement]
        # print(requirement)

        state = ctx.requirement_cache.setdefault(
            requirement,
            RequirementState(iterable=requirement.solutions(ctx=ctx, path=path)),
        )

        # print(state.vals)

        for x in state:
            # logging.warning(f"{path} {x}")
            yield x
