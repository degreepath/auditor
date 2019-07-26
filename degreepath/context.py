from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Dict, Union, Set
from collections import defaultdict
import logging

from .data import CourseInstance, CourseStatus
from .rule import CourseRule
from .claim import ClaimAttempt, Claim

logger = logging.getLogger(__name__)

COMPLETED_COURSES: Dict[Any, List[CourseInstance]] = {}
COURSE_TRANSCRIPT_MAP: Dict[Any, Dict[str, CourseInstance]] = {}
CLBID_TRANSCRIPT_MAP: Dict[Any, Dict[str, CourseInstance]] = {}


@dataclass(frozen=False)
class RequirementContext:
    transcript: Tuple = tuple()
    areas: Tuple = tuple()
    requirements: Dict = field(default_factory=dict)
    multicountable: List[List] = field(default_factory=list)
    claims: Dict[str, Set] = field(default_factory=lambda: defaultdict(set))

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
        clause: Union,
        transcript: List[CourseInstance],
        allow_claimed: bool = False
    ):
        """
        If the crsid is not in the claims dictionary, insert it with an empty list.

        If the course that is being claimed has an empty list of claimants,
        then the claim succeeds.

        Otherwise...

        If the claimant is a {course} rule specified with the {including-claimed} option,
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

        potential_conflicts = [cl for cl in self.claims[course.crsid] if cl.crsid == claim.crsid]

        # allow topics courses to be taken multiple times
        if course.is_topic:
            conflicts_are_topics = (
                course.is_topic
                for course in (self.find_course_by_clbid(clm.clbid) for clm in potential_conflicts)
                if course is not None
            )

            if all(conflicts_are_topics):
                conflicting_clbids = set(claim.clbid for claim in potential_conflicts)

                if course.clbid not in conflicting_clbids:
                    courses_are_equivalent = (course.crsid == claim.crsid for claim in potential_conflicts)

                    if all(courses_are_equivalent):
                        return ClaimAttempt(claim, conflict_with=set())

        # If the course that is being claimed has an empty list of claimants,
        # then the claim succeeds.
        if not potential_conflicts:
            # logger.debug(claim)
            self.claims[course.crsid].add(claim)
            return ClaimAttempt(claim)

        applicable_rulesets = [
            ruleset
            for ruleset in self.multicountable
            if any(c.applies_to(course) for c in ruleset)
            and any(c.mc_applies_same(clause) for c in ruleset)
        ]

        claim_conflicts = set()

        # If the claimed course matches multiple `multicountable` rulesets,
        if applicable_rulesets:
            # the first ruleset applicable to both the course and the claimant is selected.
            ruleset = applicable_rulesets[0]

            # If the claimed course matches a `multicountable` ruleset,
            #   and the claimant is within said `multicountable` ruleset,
            #   and the claimant's clause has not already been used as a claim on this course,
            #   then the claim is recorded, and succeeds.
            for ruleclause in ruleset:
                for c in potential_conflicts:
                    if not ruleclause.mc_applies_same(c):
                        continue
                    claim_conflicts.add(c)
        else:
            # logger.debug('no applicable rulesets')
            claim_conflicts = potential_conflicts

        if claim_conflicts:
            return ClaimAttempt(claim, conflict_with=claim_conflicts)
        else:
            self.claims[course.crsid].add(claim)
            return ClaimAttempt(claim, conflict_with=set())
