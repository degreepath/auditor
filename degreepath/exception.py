import attr
from typing import Tuple, Dict, Any
import logging
import enum
from .base import ResultStatus

logger = logging.getLogger(__name__)


@enum.unique
class ExceptionAction(enum.Enum):
    Insert = "insert"
    ForceInsert = "force-insert"
    Override = "override"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RuleException:
    path: Tuple[str, ...]
    type: ExceptionAction

    def to_dict(self) -> Dict[str, Any]:
        return {"path": list(self.path), "type": self.type.value}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class InsertionException(RuleException):
    clbid: str
    forced: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "clbid": self.clbid, "forced": self.forced}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class OverrideException(RuleException):
    status: ResultStatus

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "status": self.status.value}


def load_exception(data: Dict[str, Any]) -> RuleException:
    type = ExceptionAction(data['type'])

    if type is ExceptionAction.Insert:
        return InsertionException(clbid=data['clbid'], path=tuple(data['path']), type=type, forced=False)
    elif type is ExceptionAction.ForceInsert:
        return InsertionException(clbid=data['clbid'], path=tuple(data['path']), type=type, forced=True)
    elif type is ExceptionAction.Override:
        return OverrideException(status=ResultStatus(data['status']), path=tuple(data['path']), type=type)

    raise TypeError(f'expected "type" to be "insert" or "override"; got {data["type"]}')
