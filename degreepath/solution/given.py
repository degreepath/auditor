from dataclasses import dataclass
from typing import Union, List, TYPE_CHECKING, Sequence, Any, Tuple, FrozenSet
import logging
import decimal

from ..result import FromResult
from ..data import CourseInstance, Term
from ..clause import Clause, AndClause, OrClause, SingleClause, str_clause, Operator, ResolvedClause

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FromSolution:
    output: Sequence[Union[CourseInstance, Term, decimal.Decimal, int]]
    rule: Any

    def to_dict(self):
        return {
            "type": "from",
            "source": self.rule.source,
            "action": self.rule.action,
            "where": self.rule.where,
            "output": [x.to_dict() for x in self.output],
            "allow_claimed": self.allow_claimed,
            "state": self.state(),
            "status": "pending",
            "ok": self.ok(),
            "rank": self.rank(),
            "claims": [item for item in self.claims()],
        }

    def state(self):
        return "solution"

    def claims(self):
        return []

    def rank(self):
        return 0

    def ok(self):
        return False

    def stored(self):
        return self.output

    def audit(self, *, ctx, path: List):
        path = [*path, f".of"]

        if self.rule.source.mode == "student":
            return self.audit_when_student(ctx=ctx, path=path)
        if self.rule.source.mode == "saves":
            return self.audit_when_saves(ctx=ctx, path=path)
        if self.rule.source.mode == "requirements":
            return self.audit_when_reqs(ctx=ctx, path=path)

        raise KeyError(f'unknown "from" type "{self.rule.source.mode}"')

    def audit_when_saves(self, *, ctx, path: List):
        successful_claims: List = []
        failed_claims: List = []

        resolved_assertion = self.apply_clause(self.rule.action, self.output)

        if resolved_assertion.result is True:
            logger.debug("%s from-rule '%s' might possibly succeed", path, self.rule)
        else:
            logger.debug("%s from-rule '%s' did not succeed", path, self.rule)

        return FromResult(
            rule=self.rule,
            resolved_assertion=resolved_assertion,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=resolved_assertion.result is True,# and len(failed_claims) == 0,
        )

    def audit_when_reqs(self, *, ctx, path: List):
        successful_claims: List = []
        failed_claims: List = []

        resolved_assertion = self.apply_clause(self.rule.action, self.output)

        if resolved_assertion.result is True:
            logger.debug("%s from-rule '%s' might possibly succeed", path, self.rule)
        else:
            logger.debug("%s from-rule '%s' did not succeed", path, self.rule)

        return FromResult(
            rule=self.rule,
            resolved_assertion=resolved_assertion,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=resolved_assertion.result is True,# and len(failed_claims) == 0,
        )

    def audit_when_student(self, *, ctx, path: List):
        successful_claims = []
        claimed_items = []
        failed_claims = []

        for item in self.output:
            if isinstance(item, CourseInstance):
                claim = ctx.make_claim(
                    course=item,
                    path=path,
                    clause=
                        self.rule.where
                        or SingleClause(key='crsid', operator=Operator.NotEqualTo, expected='', expected_verbatim=''),
                    transcript=ctx.transcript,
                    allow_claimed=self.rule.allow_claimed,
                )

                if claim.failed():
                    logger.debug('%s course "%s" exists, but has already been claimed by %', path, item.clbid, claim.conflict_with)
                    failed_claims.append(claim)
                else:
                    logger.debug('%s course "%s" exists, and is available', path, item.clbid)
                    successful_claims.append(claim)
                    claimed_items.append(item)
            # else:
            #     logger.debug('%s item "%s" exists, and is available', path, item)
            #     successful_claims.append(claim)

        resolved_assertion = self.apply_clause(self.rule.action, claimed_items)

        if resolved_assertion.result is True:
            logger.debug("%s from-rule '%s' might possibly succeed", path, self.rule)
        else:
            logger.debug("%s from-rule '%s' did not succeed", path, self.rule)

        return FromResult(
            rule=self.rule,
            resolved_assertion=resolved_assertion,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=resolved_assertion.result is True,# and len(failed_claims) == 0,
        )

    def apply_clause(self, clause: Clause, output: Sequence) -> ResolvedClause:
        if not isinstance(clause, (AndClause, OrClause, SingleClause)):
            raise TypeError(f"expected a clause; found {clause} ({type(clause)})")

        return clause.compare_and_resolve_with(value=output, map=apply_clause_to_given)


def avg_or_0(items: Sequence):
    return sum(items) / len(items) if items else 0


def apply_clause_to_given(*, value: Any, clause: SingleClause) -> Tuple[Any, FrozenSet[Any]]:
    if clause.key == 'count(courses)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = frozenset(c.clbid for c in value)
        return (len(items), items)

    elif clause.key == 'count(subjects)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = frozenset(s for c in value for s in c.subject)
        return (len(items), items)

    elif clause.key == 'count(terms)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = frozenset(c.term for c in value)
        return (len(items), items)

    elif clause.key == 'count(years)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = frozenset(c.year for c in value)
        return (len(items), items)

    elif clause.key == 'count(distinct_courses)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = frozenset(c.crsid for c in value)
        return (len(items), items)

    elif clause.key == 'count(areas)':
        # TODO
        pass

    elif clause.key == 'count(performances)':
        # TODO
        pass

    elif clause.key == 'count(seminars)':
        # TODO
        pass

    elif clause.key == 'sum(grades)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = tuple(c.grade for c in value)
        return (sum(items), items)

    elif clause.key == 'sum(credits)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = tuple(c.credits for c in value)
        return (sum(items), items)

    elif clause.key == 'average(grades)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = tuple(c.grade for c in value)
        return (avg_or_0(items), items)

    elif clause.key == 'average(credits)':
        assert all(isinstance(x, CourseInstance) for x in value)
        items = tuple(c.credits for c in value)
        return (avg_or_0(items), items)

    elif clause.key.startswith('min(') or clause.key.startswith('max('):
        assert all(isinstance(x, CourseInstance) for x in value)
        func = min if clause.key.startswith('min(') else max

        if clause.key == 'min(terms)' or clause.key == 'max(terms)':
            item = func(c.term for c in value)
        elif clause.key == 'min(grades)' or clause.key == 'max(grades)':
            item = func(c.grade for c in value)
        elif clause.key == 'min(credits)' or clause.key == 'max(credits)':
            item = func(c.credits for c in value)
        else:
            raise Exception(f'expected a valid clause key; got {clause.key}')

        return (item, tuple([item]))

    else:
        raise Exception(f'expected a valid clause key; got {clause.key}')
