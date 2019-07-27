from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Dict, Union, Set
from collections import defaultdict
import logging

from .data import CourseInstance, CourseStatus, AreaPointer
from .rule.course import CourseRule
from .clause import Clause, SingleClause
from .claim import ClaimAttempt, Claim

logger = logging.getLogger(__name__)

COMPLETED_COURSES: Dict[Any, List[CourseInstance]] = {}
COURSE_TRANSCRIPT_MAP: Dict[Any, Dict[str, CourseInstance]] = {}
CLBID_TRANSCRIPT_MAP: Dict[Any, Dict[str, CourseInstance]] = {}


@dataclass(frozen=False)
class RequirementContext:
    transcript: Tuple[CourseInstance, ...] = tuple()
    areas: Tuple[AreaPointer, ...] = tuple()
    requirements: Dict = field(default_factory=dict)
    multicountable: List[List[SingleClause]] = field(default_factory=list)
    claims: Dict[str, Set[Claim]] = field(default_factory=lambda: defaultdict(set))

    _course_lookup_map: Dict = field(init=False)
    _clbid_lookup_map: Dict = field(init=False)
    _completed_courses: Dict = field(init=False)

    def __post_init__(self):
        tid = id(self.transcript)

        if tid not in COMPLETED_COURSES:
            COMPLETED_COURSES[tid] = [
                course
                for course in self.transcript
                if course.status != CourseStatus.DidNotComplete
            ]
        self._completed_courses = COMPLETED_COURSES[tid]

        if tid not in COURSE_TRANSCRIPT_MAP:
            COURSE_TRANSCRIPT_MAP[tid] = {
                **{c.course_shorthand(): c for c in self._completed_courses},
                **{c.course(): c for c in self._completed_courses},
            }
        self._course_lookup_map = COURSE_TRANSCRIPT_MAP[tid]

        if tid not in CLBID_TRANSCRIPT_MAP:
            CLBID_TRANSCRIPT_MAP[tid] = {c.clbid: c for c in self._completed_courses}
        self._clbid_lookup_map = CLBID_TRANSCRIPT_MAP[tid]

    def find_course(self, c: str) -> Optional[CourseInstance]:
        return self._course_lookup_map.get(c, None)

    def find_course_by_clbid(self, clbid: str) -> Optional[CourseInstance]:
        return self._clbid_lookup_map.get(clbid, None)

    def has_course(self, c: str) -> bool:
        return self.find_course(c) is not None

    def completed_courses(self):
        return iter(self._completed_courses)

    def reset_claims(self):
        self.claims = defaultdict(set)

    def make_claim(
        self, *,
        course: CourseInstance,
        path: List[str],
        clause: Union[Clause, CourseRule],
        allow_claimed: bool = False
    ):
        """
        If the crsid is not in the claims dictionary, insert it with an empty list.

        If the course that is being claimed has an empty list of claimants,
        then the claim succeeds.

        Otherwise...

        If the claimant is a {course} rule specified with the {allow_claimed} option,
        the claim is recorded, and succeeds.

        If the claimed course matches multiple `multicountable` rulesets,
            the first ruleset applicable to both the course and the claimant is selected.

        If the claimed course matches a `multicountable` ruleset,
            and the claimant is within said `multicountable` ruleset,
            and the claimant's clause has not already been used as a claim on this course,
            then the claim is recorded, and succeeds.

        Otherwise, the claim is rejected, with a list of the prior confirmed claims.
        """
        if clause is None:
            raise Exception("clause must be provided")

        claim = Claim(crsid=course.crsid, clbid=course.clbid, claimant_path=tuple(path), value=clause)

        # If the claimant is a CourseRule specified with the `.allow_claimed` option,
        # the claim succeeds (and is not recorded).
        if allow_claimed or isinstance(clause, CourseRule) and clause.allow_claimed:
            return ClaimAttempt(claim)

        potential_conflicts: Set[Claim] = set(cl for cl in self.claims[course.crsid] if cl.crsid == claim.crsid)

        # allow topics courses to be taken multiple times
        if course.is_topic:
            conflicting_courses = (self.find_course_by_clbid(clm.clbid) for clm in potential_conflicts)
            all_conflicts_are_topics = all(
                course.is_topic
                for course in conflicting_courses
                if course is not None
            )

            if all_conflicts_are_topics:
                conflicting_clbids = set(claim.clbid for claim in potential_conflicts)

                if course.clbid not in conflicting_clbids:
                    courses_are_equivalent = (course.crsid == claim.crsid for claim in potential_conflicts)

                    if all(courses_are_equivalent):
                        return ClaimAttempt(claim, conflict_with=frozenset())

        # potential rulesets are those which are contain a subset of the clause issuing the claim
        # IE:
        # - {attributes: {$eq: x}} is a subset of {attributes: {$in: [x,y,z]}};
        # - {attributes: {$eq: x}} is a subset of {$or: [{attributes: {$in: [x,y,z]}}]};
        # - {attributes: {$eq: x}} is a subset of {$and: [{attributes: {$in: [x,y,z]}}]};
        potential_rulesets = (
            ruleset
            for ruleset in self.multicountable
            if any(c.is_subset(clause) for c in ruleset)
        )

        # an "applicable ruleset" is any which can apply to the course in question
        applicable_rulesets = [
            ruleset
            for ruleset in potential_rulesets
            if any(course.apply_clause(c) for c in ruleset)
        ]

        # next, we see if any of the applicable rulesets have an open claim slot.
        # IE, with the input set of [{attributes: elective}, {attributes: post1800}],
        # we would have two "claim slots" for a course – it could be claimed by both
        # the {attributes: elective} and {attributes: post1800} clauses.

        # for each ruleset
        # - gather the "claiming clauses" from potential_conflicts
        # - exclude any items which are a subset of any of the "claiming clauses"

        # check if any potential_conflicts' claims are subsets of the any rules in the ruleset
        potential_conflict_claims: Set[Union[Clause, CourseRule]] = set(claim.value for claim in potential_conflicts)

        open_rulesets = []
        for ruleset in applicable_rulesets:
            ruleset = [
                c for c in ruleset
                if not any(c.is_subset(claim_clause) for claim_clause in potential_conflict_claims)
            ]

            if ruleset:
                open_rulesets.append(ruleset)

        for pc in potential_conflicts:
            logger.debug('potential conflict: %s', pc)
        for rs in open_rulesets:
            logger.debug('open ruleset: %s', rs)

        claim_conflicts: Set[Claim] = set()

        if open_rulesets:
            # the first ruleset applicable to both the course and the claimant is selected.
            ruleset = open_rulesets[0]

            logger.debug('there is an available ruleset: %s', ruleset)

            self.claims[course.crsid].add(claim)
            return ClaimAttempt(claim, conflict_with=frozenset())

        else:
            if applicable_rulesets:
                logger.debug('there was a ruleset that would apply, but all rules have been used')
            else:
                logger.debug('there were no open rulesets that could apply')
            # need to find the offending ruleset
            claim_conflicts = set(potential_conflicts)

            return ClaimAttempt(claim, conflict_with=frozenset(claim_conflicts))
