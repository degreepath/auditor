import abc
from typing import Iterator, Sequence
import enum


@enum.unique
class ResultStatus(enum.Enum):
    Pass = "pass"
    Problem = "problem"
    Skip = "skip"
    Pending = "pending"


class Base(abc.ABC):
    path: Sequence[str]

    def to_dict(self):
        return {
            "path": list(self.path),
            "type": self.type(),
            "status": self.foostatus(),
            "state": self.state(),
            "ok": self.ok(),
            "rank": self.rank(),
            "max_rank": self.max_rank(),
            "claims": [c.to_dict() for c in self.claims()],
            "overridden": self.was_overridden(),
        }

    def foostatus(self):
        if not isinstance(self.status(), str):
            return self.status().value
        raise Exception(f"expected {self.status()} to be a ResultStatus (at {self.path})")

    @abc.abstractmethod
    def type(self) -> str:
        raise NotImplementedError(f'must define a type() method')

    def status(self) -> ResultStatus:
        return ResultStatus.Pass if self.ok() else ResultStatus.Skip

    def ok(self):
        if self.was_overridden():
            return True

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

    def was_overridden(self) -> bool:
        return False


class Rule(Base):
    def state(self):
        return "rule"

    @abc.abstractmethod
    def validate(self, *, ctx):
        raise NotImplementedError(f'must define a validate() method')

    @abc.abstractmethod
    def solutions(self, *, ctx) -> Iterator:
        raise NotImplementedError(f'must define a solutions() method')

    @abc.abstractmethod
    def estimate(self, *, ctx) -> int:
        raise NotImplementedError(f'must define an estimate() method')


class Solution(Base):
    def state(self):
        return "solution"

    @abc.abstractmethod
    def audit(self, *, ctx):
        raise NotImplementedError(f'must define an audit() method')


class Result(Base):
    def state(self):
        return "result"
