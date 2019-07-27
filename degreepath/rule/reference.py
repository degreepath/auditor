from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ..constants import Constants
from ..solution import CourseSolution

logger = logging.getLogger(__name__)


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
            raise AssertionError(f"expected a requirement named '{self.name}', but did not find one [options: {reqs}]")

        ctx.requirements[self.name].validate(ctx=ctx)

    def solutions(self, *, ctx, path: List[str]):
        logger.debug('%s reference-rule name=%s', path, self.name)
        requirement = ctx.requirements[self.name]

        yield from requirement.solutions(ctx=ctx, path=path)
