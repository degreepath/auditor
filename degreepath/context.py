import attr
from typing import List, Optional, Tuple, Dict, Union, Set, Sequence, Iterable, Iterator
from collections import defaultdict
from contextlib import contextmanager
import logging

from .data import CourseInstance, AreaPointer
from .data.course_enums import CourseType
from .base import BaseCourseRule
from .clause import Clause, SingleClause
from .claim import ClaimAttempt, Claim
from .operator import Operator
from .exception import RuleException, OverrideException, InsertionException

logger = logging.getLogger(__name__)
debug: Optional[bool] = None


@attr.s(slots=True, kw_only=True, frozen=False, auto_attribs=True)
class RequirementContext:
    transcript_: List[CourseInstance] = attr.ib(factory=list)
    course_set_: Set[str] = attr.ib(factory=set)
    clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)

    areas: Tuple[AreaPointer, ...] = tuple()
    multicountable: List[List[SingleClause]] = attr.ib(factory=list)
    claims: Dict[str, Set[Claim]] = attr.ib(factory=lambda: defaultdict(set))
    exceptions: List[RuleException] = attr.ib(factory=dict)

    def with_transcript(self, transcript: Iterable[CourseInstance]) -> 'RequirementContext':
        transcript = list(transcript)
        course_set = set(cid for c in transcript for cid in c.course())
        clbid_lookup_map = {c.clbid: c for c in transcript}

        return attr.evolve(self, transcript_=transcript, course_set_=course_set, clbid_lookup_map_=clbid_lookup_map)

    def transcript(self) -> List[CourseInstance]:
        return self.transcript_

    def find_ap_ib_credit_course(self, *, name: str) -> Optional[CourseInstance]:
        for c in self.transcript():
            if c.course_type is CourseType.AP and c.name == name:
                return c
        return None

    def find_all_courses(self, c: str) -> Iterator[CourseInstance]:
        for crs in self.transcript():
            if crs.identity_ == c:
                yield crs

    def find_course_by_clbid(self, clbid: str) -> Optional[CourseInstance]:
        return self.clbid_lookup_map_.get(clbid, None)

    def forced_course_by_clbid(self, clbid: str) -> CourseInstance:
        match = self.find_course_by_clbid(clbid)
        if not match:
            raise Exception(f'attempted to use CLBID={clbid}, but it was not found in the transcript')
        return match

    def has_course(self, c: str) -> bool:
        return c in self.course_set_

    def has_exception(self, path: Sequence[str]) -> bool:
        tuple_path = tuple(path)
        return any(e.path[:len(path)] == tuple_path for e in self.exceptions)

    def get_insert_exceptions(self, path: Sequence[str]) -> Iterator[InsertionException]:
        tuple_path = tuple(path)
        did_yield = False
        for exception in self.exceptions:
            if isinstance(exception, InsertionException) and exception.path == tuple_path:
                logger.debug("exception found for %s: %s", path, exception)
                did_yield = True
                yield exception

        if not did_yield: logger.debug("no exception for %s", path)

    def get_waive_exception(self, path: Sequence[str]) -> Optional[OverrideException]:
        tuple_path = tuple(path)
        exception = None
        for e in self.exceptions:
            if isinstance(e, OverrideException) and e.path == tuple_path:
                exception = e
                break

        if exception:
            logger.debug("exception found for %s: %s", path, exception)
        else:
            logger.debug("no exception for %s", path)

        return exception

    @contextmanager
    def fresh_claims(self) -> Iterator[None]:
        claims = self.claims
        self.reset_claims()

        try:
            yield
        finally:
            self.set_claims(claims)

    def set_claims(self, claims: Dict[str, Set[Claim]]) -> None:
        self.claims = defaultdict(set, {k: set(v) for k, v in claims.items()})

    def reset_claims(self) -> None:
        self.claims = defaultdict(set)

    def make_claim(  # noqa: C901
        self,
        *,
        course: CourseInstance,
        path: Sequence[str],
        clause: Union[Clause, BaseCourseRule],
        allow_claimed: bool = False,
    ) -> ClaimAttempt:
        """
        Make claims against courses, to ensure that they are only used once
        (with exceptions) in an audit.
        """

        # This function is called often enough that we want to avoid even calling the `logging` module
        # unless we're actually logging things. (On a 90-second audit, this saved nearly 30 seconds.)
        global debug
        if debug is None:
            debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        if clause is None:
            raise TypeError("clause must be provided")

        if isinstance(clause, tuple):
            raise TypeError("make_claim only accepts clauses and course rules, not tuples")

        # coerce course rules to clauses
        rule = None
        if isinstance(clause, BaseCourseRule):
            rule = clause
            clause = SingleClause(key='course', expected=rule.course, expected_verbatim=rule.course, operator=Operator.EqualTo)

        # build a claim so it can be returned later
        claim = Claim(course=course, claimant_path=tuple(path), value=clause)

        # > A multicountable set describes the ways in which a course may be
        # > counted.

        # > If no multicountable set describes the course, it may only be
        # > counted once.

        # If the claimant is a CourseRule specified with the `.allow_claimed`
        # option, the claim succeeds (and is not recorded).
        if allow_claimed or getattr(rule, 'allow_claimed', False):
            if debug: logger.debug('claim for clbid=%s allowed due to rule having allow_claimed', course.clbid)
            return ClaimAttempt(claim, conflict_with=frozenset(), did_fail=False)

        prior_claims = frozenset(self.claims[course.clbid])

        # If there are no prior claims, the claim is automatically allowed.
        if not prior_claims:
            if debug: logger.debug('no prior claims for clbid=%s', course.clbid)
            self.claims[course.clbid].add(claim)
            return ClaimAttempt(claim, conflict_with=frozenset(), did_fail=False)

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
                if debug: logger.debug('no multicountable clausesets for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims), did_fail=True)
            else:
                if debug: logger.debug('no multicountable clausesets for clbid=%s; the claim has no conflicts', course.clbid)
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset(), did_fail=False)

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

        if debug: logger.debug('clauses to cover: %s', clauses_to_cover)
        if debug: logger.debug('applicable clausesets: %s', applicable_clausesets)

        applicable_clauseset = None

        for clauseset in applicable_clausesets:
            if debug: logger.debug('checking clauseset %s', clauseset)

            # all_are_supersets = True
            #
            # for p_clause in clauses_to_cover:
            #     # has_subset_clause = False
            #     #
            #     # for c in clauseset:
            #     #     if debug: logger.debug('is_subset: %s; p_clause: %s; c_clause: %s', c.is_subset(p_clause), p_clause, c)
            #     #     if c.is_subset(p_clause):
            #     #         has_subset_clause = True
            #     #     if debug: logger.debug('has_subset_clause: %s', has_subset_clause)
            #
            #     has_subset_clause = any(c.is_subset(p_clause) for c in clauseset)
            #
            #     all_are_supersets = all_are_supersets and has_subset_clause
            #     if debug: logger.debug('all_are_supersets: %s', all_are_supersets)

            all_are_supersets = all(
                any(c.is_subset(p_clause) for c in clauseset)
                for p_clause in clauses_to_cover
            )

            if all_are_supersets:
                if debug: logger.debug('done checking clausesets')
                applicable_clauseset = clauseset
                break

            if debug: logger.debug('done checking clauseset %s; ', clauseset)

        if applicable_clauseset is None:
            if prior_claims:
                if debug: logger.debug('no applicable multicountable clauseset was found for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims), did_fail=True)
            else:
                if debug: logger.debug('no applicable multicountable clauseset was found for clbid=%s; the claim has no conflicts', course.clbid)
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset(), did_fail=False)

        # now limit to just the clauses in the clauseset which have not been used
        available_clauses = [
            c for c in applicable_clauseset
            if not any(c.is_subset(prior_clause) for prior_clause in prior_clauses)
        ]

        if not available_clauses:
            if debug: logger.debug('there was an applicable multicountable clauseset for clbid=%s; however, all of the clauses have already been matched', course.clbid)
            if prior_claims:
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims), did_fail=True)
            else:
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset(), did_fail=False)

        if debug: logger.debug('there was an applicable multicountable clauseset for clbid=%s: %s', course.clbid, available_clauses)
        self.claims[course.clbid].add(claim)
        return ClaimAttempt(claim, conflict_with=frozenset(), did_fail=False)
