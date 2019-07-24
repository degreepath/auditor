from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..constants import Constants
from ..requirement import RequirementState, RequirementSolution
from ..solution import CourseSolution


@dataclass(frozen=True)
class ReferenceRule:
    name: str

    def to_dict(self):
        return {
            "type": "reference",
            "name": self.name,
            "status": "skip",
            "state": self.state(),
            "ok": self.ok(),
            "rank": self.rank(),
        }

    def state(self):
        return "rule"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "requirement" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, c: Constants):
        return ReferenceRule(name=data["requirement"])

    def validate(self, *, ctx):
        if self.name not in ctx.requirements:
            reqs = ", ".join(ctx.requirements.keys())
            raise AssertionError(
                f"expected a requirement named '{self.name}', but did not find one [options: {reqs}]"
            )

        ctx.requirements[self.name].validate(ctx=ctx)

    def _init(self, *, ctx, path):
        requirement = ctx.requirements[self.name]

        state = ctx.requirement_cache.get(requirement, None)

        if state is None:
            state = RequirementState(iterable=requirement.solutions(ctx=ctx, path=path))
            ctx.requirement_cache[requirement] = state

        return state

    def estimate(self, *, ctx):
        return 0

        requirement = ctx.requirements[self.name]

        state = self._init(ctx=ctx, path=[])

        return state.estimate(ctx=ctx)

    def solutions(self, *, ctx, path: List[str]):
        requirement = ctx.requirements[self.name]

        state = self._init(ctx=ctx, path=path)
        # print("hi")
        # ident = hash(requirement.name)
        # ident = requirement.name

        yield from state.iter_solutions()
