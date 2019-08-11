from dataclasses import dataclass
from typing import Optional, Tuple, TYPE_CHECKING
from decimal import Decimal

from .bases import Base
from ..operator import Operator

if TYPE_CHECKING:
    from ..clause import SingleClause


@dataclass(frozen=True)
class BaseCourseRule(Base):
    course: str
    hidden: bool
    grade: Optional[Decimal]
    allow_claimed: bool
    path: Tuple[str, ...]

    def to_dict(self):
        return {
            **super().to_dict(),
            "course": self.course,
            "hidden": self.hidden,
            "grade": str(self.grade) if self.grade is not None else None,
            "allow_claimed": self.allow_claimed,
        }

    def type(self):
        return "course"

    def is_equivalent_to_clause(self, clause: 'SingleClause') -> bool:
        if clause.key != 'course':
            return False

        if not hasattr(clause, 'operator'):
            return False

        if clause.operator is Operator.EqualTo:
            return self.course == clause.expected
        elif clause.operator is Operator.In:
            return self.course in clause.expected
        else:
            return False
