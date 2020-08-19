import attr
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from decimal import Decimal

from .bases import Base
from ..status import ResultStatus
from ..claim import Claim
from ..conditional_expression import SomePredicateExpression

if TYPE_CHECKING:
    from ..context import RequirementContext
    from ..data.course import CourseInstance  # noqa: F401


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseConditionalRule(Base):
    condition: SomePredicateExpression
    when_true: Base
    when_false: Optional[Base]
    overridden: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "condition": self.condition.to_dict(),
            "when_true": self.when_true.to_dict(),
            "when_false": self.when_false.to_dict() if self.when_false else None,
        }

    def type(self) -> str:
        return "conditional"

    def status(self) -> ResultStatus:
        if self.condition.result is True:
            return self.when_true.status()
        elif self.condition.result is False and self.when_false:
            return self.when_false.status()
        else:
            return ResultStatus.Empty

    def rank(self) -> Tuple[Decimal, Decimal]:
        if self.condition.result is True:
            return self.when_true.rank()
        elif self.condition.result is False and self.when_false:
            return self.when_false.rank()
        else:
            return Decimal(0), Decimal(1)

    def is_in_gpa(self) -> bool:
        if self.condition.result is True:
            return self.when_true.is_in_gpa()
        elif self.condition.result is False and self.when_false:
            return self.when_false.is_in_gpa()
        else:
            return False

    def claims(self) -> List[Claim]:
        if self.condition.result is True:
            return self.when_true.claims()
        elif self.condition.result is False and self.when_false:
            return self.when_false.claims()
        else:
            return []

    def claims_for_gpa(self) -> List[Claim]:
        if self.condition.result is True:
            return self.when_true.claims_for_gpa()
        elif self.condition.result is False and self.when_false:
            return self.when_false.claims_for_gpa()
        else:
            return []

    def all_courses(self, ctx: 'RequirementContext') -> List['CourseInstance']:
        if self.condition.result is True:
            return self.when_true.all_courses(ctx=ctx)
        elif self.condition.result is False and self.when_false:
            return self.when_false.all_courses(ctx=ctx)
        else:
            return []

    def waived(self) -> bool:
        return self.overridden
