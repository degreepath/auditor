from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, List, Optional, TYPE_CHECKING
import re
import itertools
import logging

from ...requirement import RequirementContext
from .source import FromInput
from .assertion import Assertion
from ...limit import Limit
from ...clause import Clause, SingleClause
from ...solution import FromSolution


@dataclass(frozen=True)
class FromRule:
    source: FromInput
    action: Optional[Assertion]
    limit: Optional[Limit]
    where: Optional[Clause]
    store: Optional[str]

    def to_dict(self):
        return {
            "type": "from",
            "source": self.source.to_dict(),
            "action": self.action.to_dict() if self.action else None,
            "where": self.where.to_dict() if self.where else None,
            "store": self.store,
        }

    @staticmethod
    def can_load(data: Dict) -> bool:
        if "from" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict) -> FromRule:
        where = data.get("where", None)
        if where is not None:
            where = SingleClause.load(where)

        limit = data.get("limit", None)
        if limit is not None:
            limit = [Limit.load(l) for l in limit]

        action = None
        if "assert" in data:
            action = Assertion.load(data=data["assert"])

        return FromRule(
            source=FromInput.load(data["from"]),
            action=action,
            limit=limit,
            where=where,
            store=data.get("store", None),
        )

    def validate(self, *, ctx: RequirementContext):
        self.source.validate(ctx=ctx)
        if self.action:
            self.action.validate(ctx=ctx)
        if self.store is not None:
            assert self.store in ("courses",)

    def solutions_when_student(self, *, ctx: RequirementContext, path):
        if self.source.itemtype == "courses":
            data = ctx.transcript
        else:
            raise KeyError(f"{self.source.itemtype} not yet implemented")

        yield data

    def solutions_when_saves(self, *, ctx: RequirementContext, path):
        saves = [
            ctx.save_rules[s].solutions(ctx=ctx, path=path) for s in self.source.saves
        ]

        for p in itertools.product(*saves):
            data = [item for save_result in p for item in save_result.stored()]
            yield data

    def solutions_when_reqs(self, *, ctx: RequirementContext, path):
        reqs = [
            ctx.requirements[s].solutions(ctx=ctx, path=path)
            for s in self.source.requirements
        ]

        for p in itertools.product(*reqs):
            data = [item for req_result in p for item in req_result.matched()]
            yield data

    def solutions(self, *, ctx: RequirementContext, path: List[str]):
        path = [*path, f".from"]
        logging.debug(f"{path}")

        if self.source.mode == "student":
            iterable = self.solutions_when_student(ctx=ctx, path=path)
        elif self.source.mode == "saves":
            iterable = self.solutions_when_saves(ctx=ctx, path=path)
        elif self.source.mode == "requirements":
            iterable = self.solutions_when_reqs(ctx=ctx, path=path)
        else:
            raise KeyError(f'unknown "from" type "{self.source.mode}"')

        did_iter = False
        for data in iterable:
            if self.where is not None:
                logging.debug(f"fromrule/filter/clause: {self.where}")
                logging.debug(f"fromrule/filter/before: {data}")
                data = [c for c in data if c.apply_clause(self.where)]
                logging.debug(f"fromrule/filter/after: {data}")

            if self.store == "courses":
                logging.debug("storing courses")
                yield FromSolution(output=data, rule=self)
                return
            elif self.store:
                raise Exception("not implemented yet")

            assert self.action is not None

            for n in self.action.range(items=data):
                did_iter = True
                for combo in itertools.combinations(data, n):
                    yield FromSolution(output=combo, rule=self)

        if not did_iter:
            # be sure we always yield something
            logging.info("did not yield anything; yielding empty collection")
            yield FromSolution(output=[], rule=self)
