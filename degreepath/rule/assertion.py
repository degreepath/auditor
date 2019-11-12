import attr
from typing import Dict, Sequence, Iterator, List, Collection, Optional, TYPE_CHECKING
import logging
from decimal import Decimal

from ..clause import load_clause, SingleClause
from ..constants import Constants
from ..operator import Operator
from ..base.bases import Rule, Solution
from ..base.assertion import BaseAssertionRule

if TYPE_CHECKING:  # pragma: no cover
    from ..context import RequirementContext
    from ..data import Clausable  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
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
            where = load_clause(where, c=c)

        assertion = load_clause(data["assert"], c=c, allow_boolean=False, forbid=[Operator.LessThan])

        message = data.get("message", None)

        allowed_keys = set(['where', 'assert', 'message'])
        given_keys = set(data.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at {path})"

        assert isinstance(assertion, SingleClause), "assertions may only be single clauses"

        return AssertionRule(assertion=assertion, where=where, path=tuple(path), inserted=tuple(), message=message)

    def validate(self, *, ctx: 'RequirementContext') -> None:
        if self.where:
            self.where.validate(ctx=ctx)
        self.assertion.validate(ctx=ctx)

    def get_requirement_names(self) -> List[str]:
        return []

    def estimate(self, *, ctx: 'RequirementContext') -> int:
        logger.debug('AssertionRule.estimate: 0')
        return 0

    def solutions(self, *, ctx: 'RequirementContext', depth: Optional[int] = None) -> Iterator[Solution]:
        raise Exception('this method should not be called')

    def has_potential(self, *, ctx: 'RequirementContext') -> bool:
        raise Exception('this method should not be called')

    def all_matches(self, *, ctx: 'RequirementContext') -> Collection['Clausable']:
        raise Exception('this method should not be called')

    def override_expected_value(self, value: Decimal) -> 'AssertionRule':
        clause = self.assertion.override_expected(value)

        return attr.evolve(self, assertion=clause)
