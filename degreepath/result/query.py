from dataclasses import dataclass
from typing import Tuple
from .assertion import AssertionResult

from ..base import Result, BaseQueryRule
from ..data import CourseInstance


@dataclass(frozen=True)
class QueryResult(Result, BaseQueryRule):
    successful_claims: Tuple[CourseInstance, ...]
    failed_claims: Tuple[CourseInstance, ...]
    resolved_assertions: Tuple[AssertionResult, ...]
    success: bool
    overridden: bool = False

    @staticmethod
    def from_solution(
        *,
        solution,
        resolved_assertions=Tuple[AssertionResult, ...],
        successful_claims=Tuple[CourseInstance, ...],
        failed_claims=Tuple[CourseInstance, ...],
        success: bool,
        overridden: bool = False,
    ):
        return QueryResult(
            source=solution.source,
            source_type=solution.source_type,
            source_repeats=solution.source_repeats,
            assertions=solution.assertions,
            limit=solution.limit,
            where=solution.where,
            allow_claimed=solution.allow_claimed,
            attempt_claims=solution.attempt_claims,
            resolved_assertions=resolved_assertions,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=success,
            path=solution.path,
            overridden=overridden,
        )

    def to_dict(self):
        return {
            **super().to_dict(),
            "failures": [c.to_dict() for c in self.failed_claims],
            "assertions": [a.to_dict() for a in self.resolved_assertions],
        }

    def claims(self):
        return self.successful_claims

    def was_overridden(self):
        return self.overridden

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.success is True

    def rank(self):
        return len(self.successful_claims) + int(len(self.failed_claims) * 0.5)

    def max_rank(self):
        return len(self.successful_claims) + len(self.failed_claims)
