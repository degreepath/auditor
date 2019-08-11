from dataclasses import dataclass
from typing import Tuple, Dict
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
    action: ExceptionAction

    def to_dict(self):
        return {"path": list(self.path), "action": self.action.value}

    def is_pass_override(self) -> bool:
        return False


@dataclass(frozen=True)
class InsertionException(RuleException):
    clbid: str

    def to_dict(self):
        return {**super().to_dict(), "clbid": self.clbid}


@dataclass(frozen=True)
class OverrideException(RuleException):
    status: ResultStatus

    def to_dict(self):
        return {**super().to_dict(), "status": self.status.value}

    def is_pass_override(self) -> bool:
        return self.status is ResultStatus.Pass


def load_exception(data: Dict) -> RuleException:
    if data['action'] == 'insert':
        return InsertionException(clbid=data['clbid'], path=data['path'], action=ExceptionAction.Insert)
    elif data['action'] == 'override':
        return OverrideException(status=ResultStatus(data['status']), path=data['path'], action=ExceptionAction.Override)

    raise TypeError(f'expected "action" to be "insert" or "override"; got {data["action"]}')
