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
    hidden: bool
    grade: Optional[Decimal]
    allow_claimed: bool
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "course": self.course,
            "hidden": self.hidden,
            "grade": str(self.grade) if self.grade is not None else None,
            "allow_claimed": self.allow_claimed,
            "claims": [c.to_dict() for c in self.claims()],
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

    def rank(self) -> int:
        return 1 if self.ok() else 0

    def max_rank(self) -> int:
        return 1
