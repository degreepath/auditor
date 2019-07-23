from dataclasses import dataclass
from typing import Dict, List, Iterator
import logging

from .rule import FromRule
from .constants import Constants


@dataclass(frozen=True)
class SaveRule:
    innards: FromRule
    name: str

    def to_dict(self):
        return {
            **self.innards.to_dict(),
            "type": "save",
            "name": self.name,
        }

    @staticmethod
    def load(name: str, data: Dict, c: Constants):
        return SaveRule(innards=FromRule.load(data, c, in_save=True), name=name)

    def validate(self, *, ctx):
        assert self.name.strip() != ""

        self.innards.validate(ctx=ctx)

    def solutions(self, *, ctx, path: List[str]) -> Iterator:
        path = [*path, f'.save["{self.name}"]']
        logging.debug("{} inside a saverule", path)
        yield from self.innards.solutions(ctx=ctx, path=path)
