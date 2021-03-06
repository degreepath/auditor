import attr
from typing import Dict, List, Set, FrozenSet, Tuple, Optional, Sequence, Iterator, Any
import logging
import decimal
import os
from collections import defaultdict

from .base import Solution, Result, Rule, Base
from .constants import Constants
from .context import RequirementContext, group_exceptions
from .data.course import CourseInstance
from .data.area_pointer import AreaPointer
from .data.area_enums import AreaType
from .data.student import Student
from .exception import RuleException, InsertionException, BlockException
from .limit import LimitSet
from .load_rule import load_rule
from .result.count import CountResult
from .result.requirement import RequirementResult
from .lib import grade_point_average
from .solve import find_best_solution
from .status import ResultStatus, WAIVED_AND_DONE
from .claim import Claim

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaOfStudy(Base):
    """The overall class for working with an area"""
    name: str
    kind: str
    degree: Optional[str]
    dept: Optional[str]
    code: str

    limit: LimitSet
    result: Any  # Rule
    multicountable: Dict[str, List[Tuple[str, ...]]]
    path: Tuple[str, ...]

    common_rules: Tuple[Rule, ...]
    excluded_clbids: FrozenSet[str] = frozenset()

    # the version of this file format
    version: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "kind": self.kind,
            "code": self.code,
            "degree": self.degree,
            "result": self.result.to_dict(),
            "gpa": str(self.gpa()),
            "limit": self.limit.to_dict(),
            "ok": self.status() in WAIVED_AND_DONE,
            "version": self.version,
        }

    def type(self) -> str:
        return "area"

    def gpa(self) -> decimal.Decimal:
        return decimal.Decimal('0.00')

    @staticmethod
    def load(
        *,
        specification: Dict,
        c: Constants,
        student: Student = Student(),
        exceptions: Sequence[RuleException] = tuple(),
        all_emphases: bool = False,
        emphasis_validity_check: bool = False,
    ) -> 'AreaOfStudy':
        this_code = specification.get('code', '<null>')
        pointers = {p.code: p for p in student.areas}
        this_pointer = pointers.get(this_code, None)

        emphases = specification.get('emphases', {})

        # this block just does validity checking on the emphases; we don't
        # actually use the result of loading these here.
        for e in emphases.values():
            AreaOfStudy.load(specification=e, c=c, student=student, emphasis_validity_check=True)

        declared_emphasis_codes = set(str(a.code) for a in student.areas if a.kind is AreaType.Emphasis)

        ctx = RequirementContext(
            areas=student.areas,
            exceptions=group_exceptions(exceptions),
            templates=student.templates_as_dict(),
            music_proficiencies=student.music_proficiencies,
        ).with_transcript(student.courses, including_failed=student.courses_with_failed,)

        result = load_rule(
            data=specification["result"],
            c=c,
            children=specification.get("requirements", {}),
            emphases=[
                v for k, v in emphases.items()
                if str(k) in declared_emphasis_codes or all_emphases
            ],
            path=["$"],
            ctx=ctx,
        )
        assert result, TypeError(f'expected load_rule to process {specification["result"]}')

        # Automatically exclude any "required" courses
        excluded_clbids: FrozenSet[str] = frozenset()
        if not emphasis_validity_check:
            required_courses = result.get_required_courses(ctx=ctx)
            excluded_clbids = frozenset(c.clbid for c in required_courses)
            result = result.exclude_required_courses(required_courses)

            excluded_idents = sorted(set(f"{crs.identity_}:{crs.clbid}" for crs in required_courses))
            logger.debug('excluding %s', excluded_idents)

        # Apply "block" exceptions to prevent courses from going places they shouldn't
        for exception in exceptions:
            if not isinstance(exception, BlockException):
                continue

            result = result.apply_block_exception(exception)

        limit = LimitSet.load(data=specification.get("limit", None), c=c, ctx=ctx)

        multicountable_rules: Dict[str, List[Tuple[str, ...]]] = {
            course: [
                tuple(f"%{segment}" for segment in path)
                for path in paths
            ]
            for course, paths in specification.get("multicountable", {}).items()
        }

        allowed_keys = {'name', 'type', 'major', 'degree', 'code', 'emphases', 'result', 'requirements', 'limit', 'multicountable', 'credit', 'exceptions-migrations'}
        given_keys = set(specification.keys())
        assert given_keys.difference(allowed_keys) == set(), f"expected set {given_keys.difference(allowed_keys)} to be empty (at ['$'])"

        dept = this_pointer.dept if this_pointer else None
        degree = specification.get('degree', None)

        return AreaOfStudy(
            name=specification.get('name', 'Test'),
            kind=specification.get('type', 'test'),
            degree=degree,
            dept=dept,
            result=result,
            multicountable=multicountable_rules,
            limit=limit,
            path=('$',),
            code=this_code,
            excluded_clbids=excluded_clbids,
            overridden=False,
            common_rules=tuple(prepare_common_rules(
                other_areas=student.areas,
                dept_code=dept,
                degree=degree,
                area_code=this_code,
                ctx=ctx,
                c=c,
            )),
        )

    def solutions(self, *, student: Student, exceptions: List[RuleException]) -> Iterator['AreaSolution']:
        logger.debug("evaluating area.result")

        forced_clbids = set(e.clbid for e in exceptions if isinstance(e, InsertionException) and e.forced is True)
        forced_courses = {c.clbid: c for c in student.courses if c.clbid in forced_clbids}

        # has_multicountable = len(self.multicountable) > 0
        # skip_areas = {'250', '220', '350', '455', '420', '570', 'B.A.', 'B.M.'}
        # use_optimization = not has_multicountable and self.code not in (skip_areas)
        use_optimization = f"{student.stnum}::{self.code}" in os.getenv('DP_WIP_MC_OPTIMIZATION', '').split(',')

        ctx = RequirementContext(
            areas=student.areas,
            music_performances=student.music_performances,
            music_attendances=student.music_recital_slips,
            music_proficiencies=student.music_proficiencies,
            exceptions=group_exceptions(exceptions),
            multicountable=self.multicountable,
            templates=student.templates_as_dict(),
        )

        for i, _c in enumerate(student.courses):
            logger.debug("initial transcript [%d]: %r", i, _c)

        for limited_transcript in self.limit.limited_transcripts(courses=student.courses, forced_clbids=tuple(forced_clbids)):
            for i, _c in enumerate(limited_transcript):
                logger.debug("evaluating area.result with limited transcript [%d]: %r", i, _c)

            ctx = ctx.with_transcript(
                limited_transcript,
                full=student.courses,
                forced=forced_courses,
                including_failed=student.courses_with_failed,
            )

            for i, sol in enumerate(self.result.solutions(ctx=ctx, depth=1)):
                logger.debug('beginning solution #%d', i + 1)

                if use_optimization:
                    all_claims = sol.all_courses(ctx=ctx)

                    if len(all_claims) != len(set(all_claims)):
                        continue

                # be sure to start with an empty claims list - without
                # clearing it here, these calls only work if you process the
                # `.audit()` calls in sequence directly from the generator;
                # generating a full list of all solutions and then iterating
                # over that will accidentally share state.

                yield AreaSolution.from_area(solution=sol, area=self, ctx=ctx)

                # We need to clear the list of claims at the end of the loop,
                # or else we accidentally clear the independently-solved claims
                ctx = ctx.with_empty_claims()

                logger.debug('completed solution #%d', i + 1)

        logger.debug("all solutions generated")

    def estimate(self, *, student: Student, exceptions: List[RuleException]) -> int:
        forced_clbids = set(e.clbid for e in exceptions if isinstance(e, InsertionException) and e.forced is True)
        forced_courses = {c.clbid: c for c in student.courses if c.clbid in forced_clbids}

        ctx = RequirementContext(
            areas=student.areas,
            music_performances=student.music_performances,
            music_attendances=student.music_recital_slips,
            music_proficiencies=student.music_proficiencies,
            exceptions=group_exceptions(exceptions),
            multicountable=self.multicountable,
            templates=student.templates_as_dict(),
        )

        acc = 0

        for limited_transcript in self.limit.limited_transcripts(courses=student.courses, forced_clbids=tuple(forced_clbids)):
            ctx = ctx.with_transcript(
                limited_transcript,
                full=student.courses,
                forced=forced_courses,
                including_failed=student.courses_with_failed,
            )

            acc += self.result.estimate(ctx=ctx.with_empty_claims(), depth=1)

        return acc


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class AreaSolution(AreaOfStudy):
    solution: Solution
    context: RequirementContext

    @staticmethod
    def from_area(*, area: AreaOfStudy, solution: Solution, ctx: RequirementContext) -> 'AreaSolution':
        return AreaSolution(
            name=area.name,
            kind=area.kind,
            dept=area.dept,
            code=area.code,
            degree=area.degree,
            limit=area.limit,
            result=area.result,
            multicountable=area.multicountable,
            path=area.path,
            solution=solution,
            context=ctx,
            overridden=area.overridden,
            common_rules=area.common_rules,
            excluded_clbids=area.excluded_clbids,
        )

    def audit(self) -> 'AreaResult':
        logger.debug("auditing area solution")
        result = self.solution.audit(ctx=self.context)

        # Append the "common" major requirements, if we've audited a major.
        if self.kind == 'major':
            common_req_results = self.audit_common_major_requirements(result=result)

            assert isinstance(result, CountResult), TypeError('expected a Count result from common major requirements')

            result = attr.evolve(result, items=tuple([*result.items, common_req_results]), count=result.count + 1)

        logger.debug("audit complete")

        return AreaResult.from_solution(area=self, result=result, ctx=self.context)

    def audit_common_major_requirements(self, result: Result) -> RequirementResult:
        logger.debug("auditing area solution's common major requirements")
        claimed: Set[CourseInstance] = result.matched()

        c_or_better__path = self.common_rules[0].path
        exceptions = {}
        for e in self.context.get_insert_exceptions_beneath(c_or_better__path):
            course = self.context.forced_course_by_clbid(e.clbid, path=c_or_better__path)
            exceptions[course.clbid] = course

        # unclaimed = list(set(self.context.transcript()) - claimed)
        # unclaimed_context = RequirementContext().with_transcript(unclaimed)

        fresh_context = self.context.with_empty_claims()
        whole_context = fresh_context.with_transcript(fresh_context.transcript_with_excluded())
        claimed_context = fresh_context.with_transcript(claimed, forced=exceptions)

        c_or_better = find_best_solution(rule=self.common_rules[0], ctx=claimed_context)
        assert c_or_better is not None, TypeError('no solutions found for c_or_better rule')

        s_u_credits = find_best_solution(rule=self.common_rules[1], ctx=claimed_context)
        assert s_u_credits is not None, TypeError('no solutions found for s_u_credits rule')

        try:
            outside_the_major = find_best_solution(rule=self.common_rules[2], ctx=whole_context)
            assert outside_the_major is not None, TypeError('no solutions found for outside_the_major rule')
        except IndexError:
            outside_the_major = None

        items = [c_or_better, s_u_credits]
        if outside_the_major is not None:
            items.append(outside_the_major)

        return RequirementResult(
            name=f"Common {self.degree} Major Requirements",
            message=None,
            path=('$', '%Common Requirements'),
            is_audited=False,
            in_gpa=False,
            is_contract=False,
            overridden=False,
            disjoint=None,
            result=CountResult(
                path=('$', '%Common Requirements', '.count'),
                count=len(items),
                items=tuple(items),
                audit_clauses=tuple(),
                at_most=False,
                overridden=False,
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
            dept=area.dept,
            code=area.code,
            degree=area.degree,
            limit=area.limit,
            multicountable=area.multicountable,
            path=area.path,
            context=ctx,
            result=result,
            overridden=area.overridden,
            common_rules=area.common_rules,
            excluded_clbids=area.excluded_clbids,
        )

    def gpa(self) -> decimal.Decimal:
        if not self.result:
            return decimal.Decimal('0.00')

        if self.kind == 'degree':
            courses = self.context.transcript_with_failed_
        else:
            courses = list(self.matched_for_gpa())

        return grade_point_average(courses)

    def status(self) -> ResultStatus:
        logger.debug("computing status: start")
        if self.is_waived():
            logger.debug("computing status: end")
            return ResultStatus.Waived

        s = self.result.status()
        logger.debug("computing status: end")
        return s

    def rank(self) -> Tuple[decimal.Decimal, decimal.Decimal]:
        logger.debug("computing rank: start")
        r = self.result.rank()
        logger.debug("computing rank: end")
        return r

    def claims(self) -> List[Claim]:
        return self.result.claims()

    def keyed_claims(self) -> Dict[str, List[List[str]]]:
        def sort_claims_by_time(cl: Claim) -> Tuple:
            c = cl.course
            return (c.subject, c.number, c.section or '', c.sub_type.value, c.year, c.term)

        claims = sorted((c for c in self.claims() if not c.failed), key=sort_claims_by_time)

        by_clbid: Dict[str, List[Claim]] = defaultdict(list)
        for c in claims:
            by_clbid[c.course.clbid].append(c)

        return {
            clbid: [list(attempt.claimed_by) for attempt in claim_attempts]
            for clbid, claim_attempts in by_clbid.items()
        }

    def claims_for_gpa(self) -> List[Claim]:
        return self.result.claims_for_gpa()

    def is_waived(self) -> bool:
        return self.result.is_waived()


def prepare_common_rules(
    *,
    degree: Optional[str],
    dept_code: Optional[str],
    other_areas: Tuple[AreaPointer, ...] = tuple(),
    area_code: str,
    ctx: RequirementContext,
    c: Constants,
) -> Iterator[Rule]:
    if degree == 'B.M.':
        is_bm_major = True
    else:
        is_bm_major = False

    c_or_better = load_rule(
        data={"requirement": "Credits at a C or higher"},
        children={
            "Credits at a C or higher": {
                "message": "Of the credits counting toward the minimum requirements for a major, a total of six (6.00) must be completed with a grade of C or higher.",
                "result": {
                    "from": "courses",
                    "allow_claimed": True,
                    "claim": False,
                    "where": {
                        "$and": [
                            {
                                "$or": [
                                    {"grade": {"$gte": "C", "$during_covid": "C-"}},
                                    {"is_in_progress": {"$eq": True}},
                                ],
                            },
                            {"credits": {"$gt": 0}},
                        ],
                    },
                    "assert": {"sum(credits)": {"$gte": 6}},
                },
            },
        },
        path=['$', '%Common Requirements', '.count', '[0]'],
        c=c,
        ctx=ctx,
    )

    assert c_or_better is not None, TypeError('expected c_or_better to not be None')

    yield c_or_better

    if is_bm_major:
        s_u_detail = {
            "message": "No courses in a B.M Music major may be taken S/U.",
            "result": {
                "from": "courses",
                "allow_claimed": True,
                "claim": False,
                "where": {"grade_option": {"$eq": "s/u"}},
                "assert": {"count(courses)": {"$eq": 0}},
            },
        }
    else:
        s_u_detail = {
            "message": "Only one full-course equivalent (1.00-credit course) taken S/U may count toward the minimum requirements for a major.",
            "result": {
                "from": "courses",
                "allow_claimed": True,
                "claim": False,
                "where": {
                    "$and": [
                        {"grade_option": {"$eq": "s/u"}},
                        {"credits": {"$eq": 1}},
                    ],
                },
                "assert": {"count(courses)": {"$lte": 1}},
            },
        }

    s_u_credits = load_rule(
        data={"requirement": "Credits taken S/U"},
        children={"Credits taken S/U": s_u_detail},
        path=['$', '%Common Requirements', '.count', '[1]'],
        c=c,
        ctx=ctx,
    )

    assert s_u_credits is not None, TypeError('expected s_u_credits to not be None')

    yield s_u_credits

    if is_bm_major is False:
        other_area_codes = set(p.code for p in other_areas if p.code != area_code)

        studio_art_code = '140'
        art_history_code = '135'
        is_history_and_studio = \
            (area_code == studio_art_code and art_history_code in other_area_codes)\
            or (area_code == art_history_code and studio_art_code in other_area_codes)

        ba_music_code = '450'
        is_ba_music = area_code == ba_music_code

        outside_rule: Dict
        if dept_code is None:
            outside_rule = {
                "message": "21 total credits must be completed outside of the courses in the major",
                "department-audited": True,
            }

        elif is_history_and_studio:
            outside_rule = {
                "message": "Students who double-major in studio art and art history are required to complete at least 18 full-course credits outside the SIS 'ART' subject code.",
                "result": {
                    "from": "courses",
                    "where": {
                        "$and": [
                            {"subject": {"$neq": "ART"}},
                            {"subject": {"$neq": "REG"}},
                            {"subject": {"$neq": "OFFC"}},
                            {"credits": {"$eq": 1}},
                        ],
                    },
                    "allow_claimed": True,
                    "claim": False,
                    "assert": {"sum(credits)": {"$gte": 18}},
                },
            }

        elif is_ba_music:
            outside_rule = {
                "message": "21 total credits must be completed outside of the SIS 'subject' codes of the major: 'MUSIC', 'MUSPF', and 'MUSEN'.",
                "result": {
                    "from": "courses",
                    "where": {
                        "$and": [
                            {"subject": {"$nin": ["MUSIC", "MUSPF", "MUSEN"]}},
                            {"subject": {"$neq": "REG"}},
                            {"subject": {"$neq": "OFFC"}},
                        ],
                    },
                    "allow_claimed": True,
                    "claim": False,
                    "assert": {"sum(credits)": {"$gte": 21}},
                },
            }

        else:
            outside_rule = {
                "message": f"21 total credits must be completed outside of the SIS 'subject' code of the major, '{dept_code}'.",
                "result": {
                    "from": "courses",
                    "where": {
                        "$and": [
                            {"subject": {"$neq": dept_code}},
                            {"subject": {"$neq": "REG"}},
                            {"subject": {"$neq": "OFFC"}},
                        ],
                    },
                    "allow_claimed": True,
                    "claim": False,
                    "assert": {"sum(credits)": {"$gte": 21}},
                },
            }

        outside_the_major = load_rule(
            data={"requirement": "Credits outside the major"},
            children={"Credits outside the major": outside_rule},
            path=['$', '%Common Requirements', '.count', '[2]'],
            c=c,
            ctx=ctx,
        )
        assert outside_the_major is not None, TypeError('expected outside_the_major to not be None')

        yield outside_the_major
