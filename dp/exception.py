import attr
from typing import Tuple, Dict, Any
import logging
import enum
from decimal import Decimal
from .status import ResultStatus

logger = logging.getLogger(__name__)


@enum.unique
class ExceptionAction(enum.Enum):
    Insert = "insert"
    ForceInsert = "force-insert"
    Override = "override"
    Value = "value"
    CourseCredits = "course-credits"
    CourseSubject = "course-subject"


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class RuleException:
    path: Tuple[str, ...]
    type: ExceptionAction

    def to_dict(self) -> Dict[str, Any]:
        return {"path": list(self.path), "type": self.type.value}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseOverrideException(RuleException):
    clbid: str

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "clbid": self.clbid}


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


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class ValueException(RuleException):
    value: Decimal

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": str(self.value)}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseCreditOverride(CourseOverrideException):
    credits: Decimal

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "credits": str(self.credits)}


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class CourseSubjectOverride(CourseOverrideException):
    subject: str

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "subject": self.subject}


def load_exception(data: Dict[str, Any]) -> RuleException:
    ex_type = ExceptionAction(data['type'])
    ex_path = tuple(data['path'])

    if ex_type is ExceptionAction.Insert:
        return InsertionException(clbid=data['clbid'], path=ex_path, type=ex_type, forced=False)
    elif ex_type is ExceptionAction.ForceInsert:
        return InsertionException(clbid=data['clbid'], path=ex_path, type=ex_type, forced=True)
    elif ex_type is ExceptionAction.Override:
        return OverrideException(status=ResultStatus(data['status']), path=ex_path, type=ex_type)
    elif ex_type is ExceptionAction.Value:
        return ValueException(value=Decimal(data['value']), path=ex_path, type=ex_type)
    elif ex_type is ExceptionAction.CourseCredits:
        return CourseCreditOverride(clbid=data['clbid'], credits=Decimal(data['credits']), path=ex_path, type=ex_type)
    elif ex_type is ExceptionAction.CourseSubject:
        return CourseSubjectOverride(clbid=data['clbid'], subject=data['subject'], path=ex_path, type=ex_type)

    raise TypeError(f'expected a known "type"; got {data["type"]}')
