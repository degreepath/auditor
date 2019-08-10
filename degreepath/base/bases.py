import abc
from typing import List, Iterator


class Base(abc.ABC):
    def to_dict(self):
        return {
            "type": self.type(),
            "status": self.status(),
            "state": self.state(),
            "ok": self.ok(),
            "rank": self.rank(),
            "max_rank": self.max_rank(),
            "claims": [c.to_dict() for c in self.claims()],
        }

    @abc.abstractmethod
    def type(self) -> str:
        raise NotImplementedError(f'must define a type() method')

    def status(self):
        return "pass" if self.ok() else "skip"

    def ok(self):
        return False

    def rank(self):
        return 0

    def max_rank(self):
        return 0

    def claims(self):
        return []

    def matched(self, *, ctx):
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)


class Rule(Base):
    def state(self):
        return "rule"

    @abc.abstractmethod
    def validate(self, *, ctx):
        raise NotImplementedError(f'must define a validate() method')

    @abc.abstractmethod
    def solutions(self, *, ctx, path: List[str]) -> Iterator:
        raise NotImplementedError(f'must define a solutions() method')

    @abc.abstractmethod
    def estimate(self, *, ctx) -> int:
        raise NotImplementedError(f'must define an estimate() method')


class Solution(Base):
    def state(self):
        return "solution"

    @abc.abstractmethod
    def audit(self, *, ctx, path: List):
        raise NotImplementedError(f'must define an audit() method')


class Result(Base):
    def state(self):
        return "result"
