from dataclasses import dataclass
from typing import Tuple, Dict, Any
import logging
import enum
from .base import ResultStatus

logger = logging.getLogger(__name__)


@enum.unique
class ExceptionAction(enum.Enum):
    Insert = "insert"
    Override = "override"


@dataclass(frozen=True)
class RuleException:
    path: Tuple[str, ...]
    type: ExceptionAction

    def to_dict(self) -> Dict[str, Any]:
        return {"path": list(self.path), "type": self.type.value}

    def is_pass_override(self) -> bool:
        return False


@dataclass(frozen=True)
class InsertionException(RuleException):
    clbid: str

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "clbid": self.clbid}


@dataclass(frozen=True)
class OverrideException(RuleException):
    status: ResultStatus

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "status": self.status.value}

    def is_pass_override(self) -> bool:
        return self.status is ResultStatus.Pass


def load_exception(data: Dict[str, Any]) -> RuleException:
    if data['type'] == 'insert':
        return InsertionException(clbid=data['clbid'], path=data['path'], type=ExceptionAction.Insert)
    elif data['type'] == 'override':
        return OverrideException(status=ResultStatus(data['status']), path=data['path'], type=ExceptionAction.Override)

    raise TypeError(f'expected "type" to be "insert" or "override"; got {data["type"]}')
