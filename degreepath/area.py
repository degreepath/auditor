import attr
from typing import Dict, List, Tuple, Optional, Sequence, Iterable, Any, TYPE_CHECKING
import logging
import decimal

from .base import Solution, Result, Base, Summable
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
from .solve import find_best_solution

if TYPE_CHECKING:
    from .claim import ClaimAttempt  # noqa: F401

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaOfStudy(Base):
    """The overall class for working with an area"""
    name: str
    kind: str
    major: Optional[str]
    degree: Optional[str]

    limit: LimitSet
    result: Any  # Rule
    multicountable: List[List[SingleClause]]
    path: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "kind": self.kind,
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
    def load(*, specification: Dict, c: Constants, areas: Sequence[AreaPointer] = tuple()) -> 'AreaOfStudy':
        emphases = specification.get('emphases', {})

        for e in emphases.values():
            r = AreaOfStudy.load(specification=e, c=c, areas=[])
            r.validate()

        declared_emphasis_codes = set(str(a.code) for a in areas if a.kind is AreaType.Emphasis)

        ctx = RequirementContext(areas=tuple(areas))

        result = load_rule(
            data=specification["result"],
            c=c,
            children=specification.get("requirements", {}),
            emphases=[v for k, v in emphases.items() if str(k) in declared_emphasis_codes],
            path=["$"],
            ctx=ctx,
        )
        if result is None:
            raise TypeError(f'expected load_rule to process {specification["result"]}')

        all_child_names = set(r for r, k in specification.get("requirements", {}).items() if 'if' not in k)
        used_child_names = set(result.get_requirement_names())
        unused_child_names = all_child_names.difference(used_child_names)
        assert unused_child_names == set(), f"expected {unused_child_names} to be empty"

        limit = LimitSet.load(data=specification.get("limit", None), c=c)

        multicountable_rules = specification.get("attributes", {}).get("multicountable", [])
        multicountable_clauses: List[List[SingleClause]] = []
        for ruleset in multicountable_rules:
            clauses = []
            for clause in ruleset:
                if "course" in clause:
                    item = SingleClause.load('course', clause['course'], c)
                elif "attributes" in clause:
                    item = SingleClause.load("attributes", clause["attributes"], c)
                else:
                    raise Exception(f"invalid multicountable {clause}")
                clauses.append(item)
            multicountable_clauses.append(clauses)

        extra_keys = set(specification.keys()).difference(['name', 'type', 'major', 'degree', 'emphases', 'result', 'requirements', 'limit', 'attributes'])
        if extra_keys:
            raise TypeError(f'expected no extra keys; got {extra_keys}')

        return AreaOfStudy(
            name=specification.get('name', 'Test'),
            kind=specification.get('type', 'test'),
            major=specification.get('major', None),
            degree=specification.get('degree', None),
            result=result,
            multicountable=multicountable_clauses,
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
            major=area.major,
            degree=area.degree,
            limit=area.limit,
            result=area.result,
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

            result = attr.evolve(result, items=tuple([*result.items, common_req_results]), count=result.count + 1)

        return AreaResult.from_solution(area=self, result=result, ctx=self.context)

    def audit_common_major_requirements(self, result: Result, other_areas: Sequence[AreaPointer] = tuple()) -> RequirementResult:
        other_area_codes = set(p.code for p in other_areas)
        if '140' in other_area_codes and '135' in other_area_codes:
            credits_message = " Students who double-major in studio art and art history are required to complete at least 18 full-course credits outside the SIS 'ART' subject code."
            credits_outside_major = 18
        else:
            credits_message = ""
            credits_outside_major = 21

        if self.degree == 'B.M.':
            is_bm_major = True
            su_message = "No courses in a B.M Music major may be taken S/U."
            allowed_su_credits = 0
        else:
            is_bm_major = False
            su_message = "Only one full-course equivalent (1.00-credit course) taken S/U may count toward the minimum requirements for a major."
            allowed_su_credits = 1

        claimed = set(result.matched(ctx=self.context))
        unclaimed = list(set(self.context.transcript()) - claimed)
        unclaimed_context = RequirementContext().with_transcript(unclaimed)
        claimed_context = RequirementContext().with_transcript(claimed)
        c = Constants(matriculation_year=0)

        c_or_better = load_rule(
            data={"requirement": "Credits at a C or higher"},
            children={
                "Credits at a C or higher": {
                    "message": "Of the credits counting toward the minimum requirements for a major, a total of six (6.00) must be completed with a grade of C or higher.",
                    "result": {
                        "from": {"student": "courses"},
                        "allow_claimed": True,
                        "claim": False,
                        "where": {
                            "$and": [
                                {"grade": {"$gte": "C"}},
                                {"credits": {"$gt": 0}},
                            ],
                        },
                        "assert": {"count(courses)": {"$gte": 6}},
                    },
                },
            },
            path=['$', '%Common Requirements', '.count', '[0]'],
            c=c,
        )
        if c_or_better is None:
            raise TypeError('expected c_or_better to not be None')

        s_u_credits = load_rule(
            data={"requirement": "Credits taken S/U"},
            children={
                "Credits taken S/U": {
                    "message": su_message,
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
                        "assert": {"count(courses)": {"$lte": allowed_su_credits}},
                    },
                },
            },
            path=['$', '%Common Requirements', '.count', '[1]'],
            c=c,
        )
        if s_u_credits is None:
            raise TypeError('expected s_u_credits to not be None')

        if not is_bm_major:
            outside_the_major = load_rule(
                data={"requirement": "Credits outside the major"},
                children={
                    "Credits outside the major": {
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
            if outside_the_major is None:
                raise TypeError('expected outside_the_major to not be None')

            outside_the_major__result = find_best_solution(rule=outside_the_major, ctx=unclaimed_context)
            if outside_the_major__result is None:
                raise TypeError('no solutions found for outside_the_major__result rule')
            unclaimed_context.reset_claims()
        else:
            outside_the_major__result = None

        c_or_better__result = find_best_solution(rule=c_or_better, ctx=claimed_context)
        if c_or_better__result is None:
            raise TypeError('no solutions found for c_or_better rule')
        claimed_context.reset_claims()

        s_u_credits__result = find_best_solution(rule=s_u_credits, ctx=claimed_context)
        if s_u_credits__result is None:
            raise TypeError('no solutions found for s_u_credits__result rule')
        claimed_context.reset_claims()

        items = [r for r in [c_or_better__result, s_u_credits__result, outside_the_major__result] if r is not None]

        return RequirementResult(
            name=f"Common {self.degree} Major Requirements",
            message=None,
            path=('$', '%Common Requirements'),
            audited_by=None,
            is_contract=False,
            overridden=False,
            result=CountResult(
                path=('$', '%Common Requirements', '.count'),
                count=len(items),
                at_most=False,
                audit_clauses=tuple(),
                audit_results=tuple(),
                overridden=False,
                items=tuple(items),
            ),
        )


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaResult(AreaOfStudy, Result):
    result: Result
    context: RequirementContext

    @staticmethod
    def from_solution(*, area: AreaOfStudy, result: Result, ctx: RequirementContext) -> 'AreaResult':
        return AreaResult(
            name=area.name,
            kind=area.kind,
            major=area.major,
            degree=area.degree,
            limit=area.limit,
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

    def rank(self) -> Summable:
        return self.result.rank()

    def max_rank(self) -> Summable:
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
