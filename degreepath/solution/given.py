from dataclasses import dataclass
from typing import Union, List, TYPE_CHECKING, Sequence, Any
import logging
import decimal

from ..result import FromResult
from ..data import CourseInstance, Term
from ..clause import Clause, AndClause, OrClause, SingleClause, str_clause, Operator

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

    def audit_when_student(self, ctx, path: List):
        successful_claims = []
        failed_claims = []

        for course in self.output:
            claim = ctx.make_claim(
                course=course,
                path=path,
                clause=
                    self.rule.where
                    or SingleClause(key='crsid', operator=Operator.NotEqualTo, expected='', expected_verbatim=''),
                transcript=ctx.transcript,
                allow_claimed=self.rule.allow_claimed,
            )

            if claim.failed():
                logger.debug(f'{path}\n\tcourse "{course}" exists, but has already been claimed by {claim.conflict_with}')
                failed_claims.append(claim)
            else:
                logger.debug(f'{path}\n\tcourse "{course}" exists, and is available')
                successful_claims.append(claim)

        may_possibly_succeed = self.apply_clause(self.rule.action, self.output)

        if may_possibly_succeed:
            logger.debug(f"{path} from-rule '{self.rule}' might possibly succeed")
        else:
            logger.debug(f"{path} from-rule '{self.rule}' did not succeed")

        return FromResult(
            rule=self.rule,
            successful_claims=successful_claims,
            failed_claims=failed_claims,
            success=may_possibly_succeed and len(failed_claims) == 0,
        )


    def apply_clause(self, clause: Clause, output: Sequence) -> bool:
        if isinstance(clause, AndClause):
            logging.debug(f"clause/and/compare {str_clause(clause)}")
            return all(self.apply_clause(subclause, output) for subclause in clause)

        elif isinstance(clause, OrClause):
            logging.debug(f"clause/or/compare {str_clause(clause)}")
            return any(self.apply_clause(subclause, output) for subclause in clause)

        elif isinstance(clause, SingleClause):
            if clause.key == 'count(courses)':
                assert all(isinstance(x, CourseInstance) for x in output)
                count = len(output)
                return clause.compare(count)

            elif clause.key == 'count(subjects)':
                assert all(isinstance(x, CourseInstance) for x in output)
                count = len(set(s for c in output for s in c.subject))
                return clause.compare(count)

            elif clause.key == 'count(terms)':
                assert all(isinstance(x, CourseInstance) for x in output)
                count = len(set(c.term for c in output))
                return clause.compare(count)

            elif clause.key == 'count(years)':
                assert all(isinstance(x, CourseInstance) for x in output)
                count = len(set(c.year for c in output))
                return clause.compare(count)

            elif clause.key == 'count(semesters)':
                # TODO: what is the point of counting semesters as opposed to terms?
                raise Exception
                # assert all(isinstance(x, CourseInstance) for x in output)
                # count = len(set(c.semester for c in output))
                # return clause.compare(count)

            elif clause.key == 'count(distinct_courses)':
                assert all(isinstance(x, CourseInstance) for x in output)
                count = len(set(c.crsid for c in output))
                return clause.compare(count)

            elif clause.key == 'count(areas)':
                # TODO
                pass

            elif clause.key == 'count(performances)':
                # TODO
                pass

            elif clause.key == 'sum(grades)':
                assert all(isinstance(x, CourseInstance) for x in output)
                total = sum(c.grade for c in output)
                return clause.compare(total)

            elif clause.key == 'sum(credits)':
                assert all(isinstance(x, CourseInstance) for x in output)
                total = sum(c.credits for c in output)
                return clause.compare(total)

            elif clause.key == 'average(grades)':
                assert all(isinstance(x, CourseInstance) for x in output)
                total = avg_or_0([c.grade for c in output])
                return clause.compare(total)

            elif clause.key == 'average(credits)':
                assert all(isinstance(x, CourseInstance) for x in output)
                total = avg_or_0([c.credits for c in output])
                return clause.compare(total)

            elif clause.key.startswith('min(') or clause.key.startswith('max('):
                assert all(isinstance(x, CourseInstance) for x in output)
                func = min if clause.key.startswith('min(') else max
                if clause.key == 'min(terms)' or clause.key == 'max(terms)':
                    total = func(c.term for c in output)
                elif clause.key == 'min(semesters)' or clause.key == 'max(semesters)':
                    # TODO: what is the point of using semesters instead of terms here?
                    raise Exception
                    # total = func(c.semester for c in output)
                elif clause.key == 'min(grades)' or clause.key == 'max(grades)':
                    total = func(c.grade for c in output)
                elif clause.key == 'min(credits)' or clause.key == 'max(credits)':
                    total = func(c.credits for c in output)
                return clause.compare(total)

        raise TypeError(f"expected a clause; found {type(clause)}")


def avg_or_0(items: Sequence):
    return sum(items) / len(items) if items else 0
