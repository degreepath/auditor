import abc
from typing import Iterator, Sequence, Dict, Any, List, Tuple, TYPE_CHECKING
import enum

from natsort import natsorted  # type: ignore

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
    path: Tuple[str, ...]

    def __lt__(self, other: Any) -> Any:
        prefixlen = commonprefixlen(self.path, other.path)
        trimmed_self = self.path[prefixlen:]
        trimmed_other = other.path[prefixlen:]

        # natsorted properly sorts the `[index]` items
        lo, hi = natsorted([trimmed_self, trimmed_other])

        if trimmed_self is lo:
            return True

        # lo, hi = natsorted([self.path, other.path])
        # if self.path is lo:
        #     return True

        return False

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

    @abc.abstractmethod
    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        raise NotImplementedError(f'must define a has_potential() method')


def commonprefixlen(a: Sequence[str], b: Sequence[str]) -> int:
    "Return the longest prefix of all list elements."
    a, b = min(a, b), max(a, b)

    for i, c in enumerate(a):
        if c != b[i]:
            return i

    return 0
