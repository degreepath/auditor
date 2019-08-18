import attr
from typing import Dict, List, Tuple, Optional, Sequence, Iterable, Any, TYPE_CHECKING
import logging
import decimal

from .base import Solution, Result, Base, Rule
from .clause import SingleClause
from .constants import Constants
from .context import RequirementContext
from .data import CourseInstance, AreaPointer, AreaType
from .exception import RuleException
from .limit import LimitSet
from .load_rule import load_rule
from .result.count import CountResult
from .result.requirement import RequirementResult
from .lib import grade_point_average

if TYPE_CHECKING:
    from .claim import ClaimAttempt  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaOfStudy(Base):
    """The overall class for working with an area"""
    name: str
    kind: str
    catalog: str
    major: Optional[str]
    degree: Optional[str]

    limit: LimitSet
    result: Any  # Rule
    attributes: Dict[str, Dict[str, List[str]]]
    multicountable: List[List[SingleClause]]
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "kind": self.kind,
            "catalog": self.catalog,
            "major": self.major,
            "degree": self.degree,
            "result": self.result.to_dict(),
            "gpa": str(self.gpa()),
        }

    def type(self) -> str:
        return "area"

    def gpa(self) -> decimal.Decimal:
        return decimal.Decimal('0.00')

    @staticmethod
    def load(*, specification: Dict, c: Constants, other_areas: Sequence[AreaPointer] = tuple()) -> 'AreaOfStudy':
        emphases = specification.get('emphases', {})
        declared_emphases = set(str(a.code) for a in other_areas if a.kind is AreaType.Emphasis)

        result = load_rule(
            data=specification["result"],
            c=c,
            children=specification.get("requirements", {}),
            emphases=[v for k, v in emphases.items() if str(k) in declared_emphases],
            path=["$"],
        )
        limit = LimitSet.load(data=specification.get("limit", None), c=c)

        attributes = specification.get("attributes", dict())
        multicountable: List[List[SingleClause]] = []
        for ruleset in attributes.get("multicountable", []):
            clauses = []
            for clause in ruleset:
                if "course" in clause:
                    item = SingleClause.load('course', clause['course'], c)
                elif "attributes" in clause:
                    item = SingleClause.load("attributes", clause["attributes"], c)
                else:
                    raise Exception(f"invalid multicountable {clause}")
                clauses.append(item)
            multicountable.append(clauses)

        return AreaOfStudy(
            name=specification.get('name', 'Test'),
            kind=specification.get('type', 'test'),
            catalog=specification.get('catalog', '2000-01'),
            major=specification.get('major', None),
            degree=specification.get('degree', None),
            result=result,
            attributes=attributes,
            multicountable=multicountable,
            limit=limit,
            path=('$',)
        )

    def validate(self) -> None:
        ctx = RequirementContext()

        self.result.validate(ctx=ctx)

    def solutions(
        self, *,
        transcript: Sequence[CourseInstance],
        areas: Sequence[AreaPointer],
        exceptions: Sequence[RuleException],
    ) -> Iterable['AreaSolution']:
        logger.debug("evaluating area.result")

        mapped_exceptions = map_exceptions(exceptions)

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            limited_transcript = tuple(sorted(limited_transcript))

            logger.debug("%s evaluating area.result with limited transcript", limited_transcript)

            ctx = RequirementContext(
                areas=tuple(areas),
                exceptions=mapped_exceptions,
                multicountable=self.multicountable,
            ).with_transcript(limited_transcript)

            for sol in self.result.solutions(ctx=ctx, depth=1):
                ctx.reset_claims()
                yield AreaSolution.from_area(solution=sol, area=self, ctx=ctx)

        logger.debug("all solutions generated")

    def estimate(self, *, transcript: Tuple[CourseInstance, ...], areas: Tuple[AreaPointer, ...]) -> int:
        iterations = 0

        for limited_transcript in self.limit.limited_transcripts(courses=transcript):
            ctx = RequirementContext(
                areas=areas,
                multicountable=self.multicountable,
            ).with_transcript(limited_transcript)

            iterations += self.result.estimate(ctx=ctx)

        return iterations


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaSolution(AreaOfStudy):
    solution: Solution
    context: RequirementContext

    @staticmethod
    def from_area(*, area: AreaOfStudy, solution: Solution, ctx: RequirementContext) -> 'AreaSolution':
        return AreaSolution(
            name=area.name,
            kind=area.kind,
            catalog=area.catalog,
            major=area.major,
            degree=area.degree,
            limit=area.limit,
            result=area.result,
            attributes=area.attributes,
            multicountable=area.multicountable,
            path=area.path,
            solution=solution,
            context=ctx,
        )

    def audit(self, other_areas: Sequence[AreaPointer] = tuple()) -> 'AreaResult':
        result = self.solution.audit(ctx=self.context)

        # Append the "common" major requirements, if we've audited a major.
        common_req_results = None
        if self.kind == 'major':
            common_req_results = self.audit_common_major_requirements(result=result, other_areas=other_areas)

            if not isinstance(result, CountResult):
                raise TypeError()

            result = attr.evolve(result, items=tuple([*result.items, common_req_results]))

        return AreaResult.from_solution(area=self, result=result, ctx=self.context)

    def audit_common_major_requirements(self, result: Result, other_areas: Sequence[AreaPointer] = tuple()) -> RequirementResult:
        """
        Of the credits counting toward the minimum requirements for a major, a
        total of six (6.00) must be completed with a grade of C or higher.

        Only one full-course equivalent (1.00-credit course) taken S/U may
        count toward the minimum requirements for a major. Some departments
        have more stringent regulations.

        While the maximum course credits counting toward a major in any one
        department may vary, 21 total credits must be completed outside of the
        SIS "department" code of the major. The 21 total credits include
        Education Department courses attending the major. In order for a
        student to be certified in a second or third major, 21 credits also
        must be taken outside of the SIS "department" code of each of those
        majors as well. If a student has a double major, courses taken in one
        major count toward the 21 credits outside of the other major. Credits
        outside the major department or program include full- (1.00) credit
        courses plus partial- (.25, .50, .75) credit courses. Students who
        double-major in studio art and art history are required to complete at
        least 18 full-course credits outside the SIS "ART" department
        designation.

        """

        other_area_codes = set(p.code for p in other_areas)
        if '140' in other_area_codes and '135' in other_area_codes:
            credits_message = " Students who double-major in studio art and art history are required to complete at least 18 full-course credits outside the SIS 'ART' subject code."
            credits_outside_major = 18
        else:
            credits_message = ""
            credits_outside_major = 21

        claimed = set(result.matched(ctx=self.context))
        unclaimed = list(set(self.context.transcript()) - claimed)
        unclaimed_context = RequirementContext().with_transcript(unclaimed)
        claimed_context = RequirementContext().with_transcript(claimed)
        c = Constants(matriculation_year=0)

        c_or_better = load_rule(
            data={"requirement": "Credits at a C or higher"},
            children={
                "Credits at a C or higher": {
                    "audited_by": "registrar",
                    "message": "Of the credits counting toward the minimum requirements for a major, a total of six (6.00) must be completed with a grade of C or higher.",
                    "result": {
                        "from": {"student": "courses"},
                        "allow_claimed": True,
                        "claim": False,
                        "where": {"grade": {"$gte": "C"}},
                        "assert": {"count(courses)": {"$gte": 6}},
                    },
                },
            },
            path=['$', '%Common Requirements', '.count', '[0]'],
            c=c,
        )

        s_u_credits = load_rule(
            data={"requirement": "Credits taken S/U"},
            children={
                "Credits taken S/U": {
                    "audited_by": "registrar",
                    "message": "Only one full-course equivalent (1.00-credit course) taken S/U may count toward the minimum requirements for a major.",
                    "result": {
                        "from": {"student": "courses"},
                        "allow_claimed": True,
                        "claim": False,
                        "where": {
                            "$and": [
                                {"s/u": {"$eq": True}},
                                {"credits": {"$eq": 1.00}},
                            ],
                        },
                        "assert": {"count(courses)": {"$lte": 1}},
                    },
                },
            },
            path=['$', '%Common Requirements', '.count', '[1]'],
            c=c,
        )

        outside_the_major = load_rule(
            data={"requirement": "Credits outside the major"},
            children={
                "Credits outside the major": {
                    "audited_by": "registrar",
                    "message": f"21 total credits must be completed outside of the SIS 'subject' code of the major.{credits_message}",
                    "result": {
                        "from": {"student": "courses"},
                        "allow_claimed": True,
                        "claim": False,
                        "assert": {"sum(credits)": {"$gte": credits_outside_major}},
                    },
                },
            },
            path=['$', '%Common Requirements', '.count', '[2]'],
            c=c,
        )

        c_or_better__result = find_best_solution(rule=c_or_better, ctx=claimed_context)
        if c_or_better__result is None:
            raise TypeError('no solutions found for c_or_better rule')
        claimed_context.reset_claims()

        s_u_credits__result = find_best_solution(rule=s_u_credits, ctx=claimed_context)
        if s_u_credits__result is None:
            raise TypeError('no solutions found for s_u_credits__result rule')
        claimed_context.reset_claims()

        outside_the_major__result = find_best_solution(rule=outside_the_major, ctx=unclaimed_context)
        if outside_the_major__result is None:
            raise TypeError('no solutions found for outside_the_major__result rule')
        unclaimed_context.reset_claims()

        return RequirementResult(
            name="Common Requirements",
            message="The following requirements are common to all majors offered at St. Olaf College.",
            path=('$', '%Common Requirements'),
            audited_by=None,
            is_contract=False,
            overridden=False,
            result=CountResult(
                path=('$', '%Common Requirements', '.count'),
                count=3,
                at_most=False,
                audit_clauses=tuple(),
                audit_results=tuple(),
                overridden=False,
                items=tuple([
                    c_or_better__result,
                    s_u_credits__result,
                    outside_the_major__result,
                ]),
            ),
        )


def find_best_solution(*, rule: Rule, ctx: RequirementContext) -> Optional[Result]:
    result = None

    for s in rule.solutions(ctx=ctx):
        tmp_result = s.audit(ctx=ctx)

        if result is None:
            result = tmp_result

        if result.rank() < tmp_result.rank():
            result = tmp_result

        if tmp_result.ok():
            result = tmp_result

    return result


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaResult(AreaOfStudy, Result):
    result: Result
    context: RequirementContext

    @staticmethod
    def from_solution(*, area: AreaOfStudy, result: Result, ctx: RequirementContext) -> 'AreaResult':
        return AreaResult(
            name=area.name,
            kind=area.kind,
            catalog=area.catalog,
            major=area.major,
            degree=area.degree,
            limit=area.limit,
            attributes=area.attributes,
            multicountable=area.multicountable,
            path=area.path,
            context=ctx,
            result=result,
        )

    def gpa(self) -> decimal.Decimal:
        if not self.result:
            return decimal.Decimal('0.00')

        transcript_map = {c.clbid: c for c in self.context.transcript()}

        if self.kind == 'degree':
            courses = list(transcript_map.values())
        else:
            courses = [transcript_map[c.claim.clbid] for c in self.claims() if c.failed() is False]

        return grade_point_average(courses)

    def ok(self) -> bool:
        if self.was_overridden():
            return True

        return self.result.ok()

    def rank(self) -> int:
        return self.result.rank()

    def max_rank(self) -> int:
        return self.result.max_rank()

    def claims(self) -> List['ClaimAttempt']:
        return self.result.claims()

    def was_overridden(self) -> bool:
        return self.result.was_overridden()


def map_exceptions(exceptions: Sequence[RuleException]) -> Dict[Tuple[str, ...], RuleException]:
    mapped_exceptions: Dict[Tuple[str, ...], RuleException] = dict()

    for e in exceptions:
        path = tuple(e.path)
        if path in mapped_exceptions:
            raise ValueError(f'expected only one exception per path: {e}')
        else:
            mapped_exceptions[path] = e

    return mapped_exceptions
