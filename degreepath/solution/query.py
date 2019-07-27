from dataclasses import dataclass
from typing import Union, List, Sequence, Any, Tuple, Collection
import logging
import decimal

from ..result.query import QueryResult
from ..rule.assertion import AssertionRule
from ..data import CourseInstance, Term, AreaPointer
from ..clause import SingleClause, Operator, ResolvedClause

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QuerySolution:
    output: Sequence[Union[CourseInstance, Term, decimal.Decimal, int]]
    rule: Any

    def to_dict(self):
        return {
            "type": "from",
            "source": self.rule.source,
            "source_type": self.rule.source_type,
            "source_repeats": self.rule.source_repeats,
            "assertions": [a.to_dict() for a in self.rule.assertions],
            "where": self.rule.where.to_dict() if self.rule.where else None,
            "output": [x.to_dict() for x in self.output],
            "allow_claimed": self.rule.allow_claimed,
            "state": self.state(),
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [item for item in self.claims()],
            "failures": [],
            "resolved_action": None,
        }

    def state(self):
        return "solution"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    def stored(self, *, ctx):
        return self.output

    def audit(self, *, ctx, path: List):
        path = [*path, f".of"]

        if self.rule.source != "student":
            raise KeyError(f'unknown "from" type "{self.rule.source}"')

        successful_claims = []
        claimed_items = []
        failed_claims = []

        for item in self.output:
            if isinstance(item, CourseInstance):
                clause = self.rule.where or SingleClause(key='crsid', operator=Operator.NotEqualTo, expected='', expected_verbatim='')
                claim = ctx.make_claim(course=item, path=path, clause=clause, allow_claimed=self.rule.allow_claimed)

                if claim.failed():
                    logger.debug('%s course "%s" exists, but has already been claimed by %', path, item.clbid, claim.conflict_with)
                    failed_claims.append(claim)
                else:
                    logger.debug('%s course "%s" exists, and is available', path, item.clbid)
                    successful_claims.append(claim)
                    claimed_items.append(item)

            elif isinstance(item, AreaPointer):
                logger.debug('%s item "%s" exists, and is available', path, item)
                claimed_items.append(item)

            else:
                raise TypeError(f'expected CourseInstance or AreaPointer; got {type(item)}')

        resolved_assertions = tuple(self.apply_assertion(a, claimed_items) for a in self.rule.assertions)

        resolved_result = all(a.result is True for a in resolved_assertions)

        if resolved_result:
            logger.debug("%s from-rule '%s' might possibly succeed", path, self.rule)
        else:
            logger.debug("%s from-rule '%s' did not succeed", path, self.rule)

        return QueryResult(
            rule=self.rule,
            resolved_assertions=resolved_assertions,
            successful_claims=tuple(successful_claims),
            failed_claims=tuple(failed_claims),
            success=resolved_result,
        )

    def apply_assertion(self, clause: AssertionRule, output: Sequence) -> ResolvedClause:
        if not isinstance(clause, AssertionRule):
            raise TypeError(f"expected a query assertion; found {clause} ({type(clause)})")

        filtered_output = output
        if clause.where is not None:
            filtered_output = [item for item in output if item.apply_clause(clause.where)]

        return clause.assertion.compare_and_resolve_with(value=filtered_output, map_func=apply_clause_to_query_rule)


def apply_clause_to_query_rule(*, value: Any, clause: SingleClause) -> Tuple[Any, Collection[Any]]:
    # remove the trailing ) with [:-1], then split on the opening ( to get the two parts
    action, kind = clause.key[:-1].split('(', maxsplit=1)

    if action == 'count':
        return count_items(kind=kind, data=value)

    elif action == 'sum':
        return sum_items(kind=kind, data=value)

    elif action == 'average':
        return avg_items(kind=kind, data=value)

    raise Exception(f'expected a valid clause key; got {clause.key}')


def count_items(data, kind):
    if kind == 'courses':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = frozenset(c.clbid for c in data)
        return (len(items), items)

    if kind == 'subjects':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = frozenset(s for c in data for s in c.subject)
        return (len(items), items)

    if kind == 'terms':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = frozenset(c.term for c in data)
        return (len(items), items)

    if kind == 'years':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = frozenset(c.year for c in data)
        return (len(items), items)

    if kind == 'distinct_courses':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = frozenset(c.crsid for c in data)
        return (len(items), items)

    if kind == 'areas':
        assert all(isinstance(x, AreaPointer) for x in data)
        items = frozenset(c.code for c in data)
        return (len(items), items)

    if kind == 'performances':
        # TODO
        raise Exception(f'count(performances) is not yet implemented')

    if kind == 'seminars':
        # TODO
        raise Exception(f'count(seminars) is not yet implemented')

    raise Exception(f'expected a valid kind; got {kind}')


def sum_items(data, kind):
    if kind == 'grades':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = tuple(c.grade for c in data)
        return (sum(items), items)

    if kind == 'credits':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = tuple(c.credits for c in data)
        return (sum(items), items)

    raise Exception(f'expected a valid kind; got {kind}')


def avg_items(data, kind):
    if kind == 'grades':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = tuple(c.grade for c in data)
        return (avg_or_0(items), items)

    if kind == 'credits':
        assert all(isinstance(x, CourseInstance) for x in data)
        items = tuple(c.credits for c in data)
        return (avg_or_0(items), items)

    raise Exception(f'expected a valid kind; got {kind}')


def avg_or_0(items: Sequence):
    return sum(items) / len(items) if items else 0
