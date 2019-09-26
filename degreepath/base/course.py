import attr
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from .bases import Base
from ..operator import Operator

if TYPE_CHECKING:
    from ..clause import SingleClause


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class BaseCourseRule(Base):
    course: str
    ap: Optional[str]
    hidden: bool
    grade: Optional[Decimal]
    allow_claimed: bool
    path: Tuple[str, ...]
    inserted: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "course": self.course,
            "hidden": self.hidden,
            "grade": str(self.grade) if self.grade is not None else None,
            "claims": [c.to_dict() for c in self.claims()],
            "ap": self.ap,
        }

    def type(self) -> str:
        return "course"

    def is_equivalent_to_clause(self, clause: 'SingleClause') -> bool:
        if clause.key != 'course':
            return False

        if not hasattr(clause, 'operator'):
            return False

        if clause.operator is Operator.EqualTo:
            if not isinstance(clause.expected, str):
                return False
            return self.course == clause.expected
        elif clause.operator is Operator.In:
            return self.course in clause.expected
        else:
            return False

    def rank(self) -> Decimal:
        if self.in_progress():
            return Decimal('0.5')

        if self.ok():
            return Decimal('1')

        return Decimal('0')

    def in_progress(self) -> bool:
        return any(c.is_in_progress for c in self.matched())

    def max_rank(self) -> int:
        return 1
