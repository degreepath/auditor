from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Dict, Union, Set
from collections import defaultdict
import logging

from .data import CourseInstance, AreaPointer
from .rule.course import CourseRule
from .clause import Clause, SingleClause
from .claim import ClaimAttempt, Claim
from .operator import Operator

logger = logging.getLogger(__name__)

COMPLETED_COURSES: Dict[Any, List[CourseInstance]] = {}
COURSE_TRANSCRIPT_MAP: Dict[Any, Dict[str, CourseInstance]] = {}
CLBID_TRANSCRIPT_MAP: Dict[Any, Dict[str, CourseInstance]] = {}


@dataclass(frozen=False)
class RequirementContext:
    transcript: Tuple[CourseInstance, ...] = tuple()
    areas: Tuple[AreaPointer, ...] = tuple()
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
                if not course.is_in_progress
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

    def make_claim(self, *, course: CourseInstance, path: List, clause: Union[Clause, CourseRule], allow_claimed: bool = False):  # noqa: C901
        """
        Make claims against courses, to ensure that they are only used once
        (with exceptions) in an audit.
        """

        if clause is None:
            raise TypeError("clause must be provided")

        if isinstance(clause, tuple):
            raise TypeError("make_claim only accepts clauses and courserules, not tuples")

        # coerce courserules to clauses
        rule = None
        if isinstance(clause, CourseRule):
            rule = clause
            clause = SingleClause(key='course', expected=rule.course, expected_verbatim=rule.course, operator=Operator.EqualTo)

        # build a claim so it can be returned later
        claim = Claim(
            crsid=course.crsid,
            clbid=course.clbid,
            claimant_path=tuple(path),
            value=clause,
        )

        # > A multicountable set describes the ways in which a course may be
        # > counted.

        # > If no multicountable set describes the course, it may only be
        # > counted once.

        # If the claimant is a CourseRule specified with the `.allow_claimed`
        # option, the claim succeeds (and is not recorded).
        if allow_claimed or getattr(rule, 'allow_claimed', False):
            return ClaimAttempt(claim)

        prior_claims = frozenset(self.claims[course.clbid])

        # If there are no prior claims, the claim is automatically allowed.
        if not prior_claims:
            logger.debug('no prior claims for clbid=%s', course.clbid)
            self.claims[course.clbid].add(claim)
            return ClaimAttempt(claim, conflict_with=frozenset())

        # Find any multicountable sets that may apply to this course
        applicable_clausesets = [
            clauseset
            for clauseset in self.multicountable
            if any(c.is_subset(clause) for c in clauseset)
        ]

        # If there are no applicable multicountable sets, return a claim
        # attempt against the prior claims. If there are no prior claims, it
        # is automatically successful.
        if not applicable_clausesets:
            if prior_claims:
                logger.debug('no multicountable clausesets for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims))
            else:
                logger.debug('no multicountable clausesets for clbid=%s; the claim has no conflicts', course.clbid)
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset())

        # > Otherwise, if a course was counted in _this_ fashion, it may also
        # > be counted like _that_ (or _that_, or _that_.)
        #
        # > Something may only be used as part of a single multicountable set.
        # > If it matches multiple, the first set which covers both the prior
        # > claims and the current one will be chosen.
        #
        # > Otherwise, it may only be counted once.

        # Assume following multicountable.
        #
        # ```python
        # [
        #   [{attributes: elective}, {attributes: post1800}],
        #   [{attributes: elective}, {attributes: warBetweenWorlds}],
        # ]
        # ```
        #
        # A courses with `{attributes: [elective]}` _could_ be claimed under
        # both clausesets. Because we don't want to allow _three_ claims for
        # the course, though -- we only want elective/post1800 and
        # elective/warBetweenWorlds as our claim pairs -- we need to figure
        # out which clauseset covers both all previous claims and the current
        # claim.
        #
        # If there are no clausesets which cover both all previous claims and
        # the current one, the claim is denied.

        prior_clauses = [cl.value for cl in prior_claims]
        clauses_to_cover = prior_clauses + [clause]

        logger.debug('clauses to cover: %s', clauses_to_cover)
        logger.debug('applicable clausesets: %s', applicable_clausesets)

        applicable_clauseset = None

        for clauseset in applicable_clausesets:
            logger.debug('checking clauseset %s', clauseset)

            all_are_supersets = True

            for p_clause in clauses_to_cover:
                has_subset_clause = False

                for c in clauseset:
                    logger.debug('is_subset: %s; p_clause: %s; c_clause: %s', c.is_subset(p_clause), p_clause, c)
                    if c.is_subset(p_clause):
                        has_subset_clause = True
                    logger.debug('has_subset_clause: %s', has_subset_clause)

                all_are_supersets = all_are_supersets and has_subset_clause
                logger.debug('all_are_supersets: %s', all_are_supersets)

            if all_are_supersets:
                logger.debug('done checking clausesets')
                applicable_clauseset = clauseset
                break

            logger.debug('done checking clauseset %s; ', clauseset)

        if applicable_clauseset is None:
            if prior_claims:
                logger.debug('no applicable multicountable clauseset was found for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims))
            else:
                logger.debug('no applicable multicountable clauseset was found for clbid=%s; the claim has no conflicts', course.clbid)
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset())

        # now limit to just the clauses in the clauseset which have not been used
        available_clauses = [
            c
            for c in applicable_clauseset
            if not any(c.is_subset(prior_clause) for prior_clause in prior_clauses)
        ]

        if not available_clauses:
            logger.debug('there was an applicable multicountable clauseset for clbid=%s; however, all of the clauses have already been matched', course.clbid)
            if prior_claims:
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims))
            else:
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset())

        logger.debug('there was an applicable multicountable clauseset for clbid=%s: %s', course.clbid, available_clauses)
        self.claims[course.clbid].add(claim)
        return ClaimAttempt(claim, conflict_with=frozenset())
