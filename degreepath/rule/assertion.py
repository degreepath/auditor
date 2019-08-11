from dataclasses import dataclass
from typing import Dict, Sequence, TYPE_CHECKING
import logging

from ..clause import load_clause
from ..constants import Constants
from ..base.bases import Rule
from ..base.assertion import BaseAssertionRule

if TYPE_CHECKING:
    from ..context import RequirementContext

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssertionRule(Rule, BaseAssertionRule):
    @staticmethod
    def can_load(data: Dict) -> bool:
        if "assert" in data:
            return True
        return False

    @staticmethod
    def load(data: Dict, *, c: Constants, path: Sequence[str]) -> 'AssertionRule':
        path = [*path, ".assert"]

        where = data.get("where", None)
        if where is not None:
            where = load_clause(where, c)

        assertion = load_clause(data["assert"], c)

        return AssertionRule(assertion=assertion, where=where, path=tuple(path))

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def estimate(self, *, ctx: 'RequirementContext') -> int:
        logger.debug('AssertionRule.estimate: 0')
        return 0

    def solutions(self):
        raise Exception('this method should not be called')
