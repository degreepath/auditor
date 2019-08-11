import abc
from typing import Iterator, Dict, Any, Sequence, List, Tuple, TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..claim import ClaimAttempt  # noqa: F401
    from ..data import CourseInstance  # noqa: F401


@enum.unique
class ResultStatus(enum.Enum):
    Pass = "pass"
    Problem = "problem"
    Skip = "skip"
    Pending = "pending"


class Base(abc.ABC):
    path: Sequence[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": list(self.path),
            "type": self.type(),
            "status": self.status().value,
            "state": self.state(),
            "ok": self.ok(),
            "rank": self.rank(),
            "max_rank": self.max_rank(),
            "claims": [c.to_dict() for c in self.claims()],
            "overridden": self.was_overridden(),
        }

    @abc.abstractmethod
    def type(self) -> str:
        raise NotImplementedError(f'must define a type() method')

    def state(self) -> str:
        return "rule"

    def status(self) -> ResultStatus:
        return ResultStatus.Pass if self.ok() else ResultStatus.Skip

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return False

    def rank(self) -> int:
        return 0

    def max_rank(self) -> int:
        return 0

    def claims(self) -> List['ClaimAttempt']:
        return []

    def matched(self, *, ctx: 'RequirementContext') -> Tuple['CourseInstance', ...]:
        claimed_courses = (claim.get_course(ctx=ctx) for claim in self.claims())
        return tuple(c for c in claimed_courses if c)

    def was_overridden(self) -> bool:
        return False


class Result(Base):
    def state(self) -> str:
        return "result"


class Solution(Base):
    def state(self) -> str:
        return "solution"

    @abc.abstractmethod
    def audit(self, *, ctx: 'RequirementContext') -> Result:
        raise NotImplementedError(f'must define an audit() method')


class Rule(Base):
    def state(self) -> str:
        return "rule"

    @abc.abstractmethod
    def validate(self, *, ctx: 'RequirementContext') -> None:
        raise NotImplementedError(f'must define a validate() method')

    @abc.abstractmethod
    def solutions(self, *, ctx: 'RequirementContext') -> Iterator[Solution]:
        raise NotImplementedError(f'must define a solutions() method')

    @abc.abstractmethod
    def estimate(self, *, ctx: 'RequirementContext') -> int:
        raise NotImplementedError(f'must define an estimate() method')
