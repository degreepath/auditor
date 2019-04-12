from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Iterator, TYPE_CHECKING
import logging

from .rule import FromRule

if TYPE_CHECKING:
    from .requirement import RequirementContext
    from .solution import FromSolution


@dataclass(frozen=True)
class SaveRule:
    innards: FromRule
    name: str

    def to_dict(self):
        return {**self.innards.to_dict(), "type": "save", "name": self.name}

    @staticmethod
    def load(name: str, data: Dict) -> SaveRule:
        return SaveRule(innards=FromRule.load(data), name=name)

    def validate(self, *, ctx: RequirementContext):
        assert self.name.strip() != ""

        self.innards.validate(ctx=ctx)

    def solutions(
        self, *, ctx: RequirementContext, path: List[str]
    ) -> Iterator[FromSolution]:
        path = [*path, f'.save["{self.name}"]']
        logging.debug(f"{path} inside a saverule")
        yield from self.innards.solutions(ctx=ctx, path=path)
