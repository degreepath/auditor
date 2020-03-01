from typing import Tuple, Optional

import attr

from ..base.assertion import BaseAssertionRule
from ..base.bases import Result
from ..clause import SingleClause


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AssertionResult(Result, BaseAssertionRule):
    overridden: bool

    @staticmethod
    def from_rule(
        rule: BaseAssertionRule,
        *,
        assertion: Optional[SingleClause] = None,
        inserted_clbids: Tuple[str, ...] = tuple(),
        overridden: bool = False,
    ) -> 'AssertionResult':
        return AssertionResult(
            where=rule.where,
            assertion=assertion or rule.assertion,
            path=rule.path,
            message=rule.message,
            overridden=overridden,
            inserted=inserted_clbids,
        )

    def waived(self) -> bool:
        return self.overridden
