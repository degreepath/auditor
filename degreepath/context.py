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
from .rule.course import CourseRule


logger = logging.getLogger(__name__)
debug: Optional[bool] = None


@attr.s(slots=True, kw_only=True, frozen=False, auto_attribs=True)
class RequirementContext:
    transcript_: List[CourseInstance] = attr.ib(factory=list)
    course_set_: Set[str] = attr.ib(factory=set)
    clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)
    forced_clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)
    transcript_with_failed_: List[CourseInstance] = attr.ib(factory=list)

    areas: Tuple[AreaPointer, ...] = tuple()
    multicountable: Dict[str, List[Tuple[str, ...]]] = attr.ib(factory=list)
    claims: Dict[str, Set[Claim]] = attr.ib(factory=lambda: defaultdict(set))
    exceptions: List[RuleException] = attr.ib(factory=dict)

    def with_transcript(
        self,
        transcript: Iterable[CourseInstance],
        *,
        forced: Optional[Dict[str, CourseInstance]] = None,
        including_failed: Iterable[CourseInstance] = tuple(),
    ) -> 'RequirementContext':
        transcript = list(transcript)
        course_set = set(c.course() for c in transcript)
        clbid_lookup_map = {c.clbid: c for c in transcript}

        return attr.evolve(
            self,
            transcript_=transcript,
            transcript_with_failed_=list(including_failed),
            course_set_=course_set,
            clbid_lookup_map_=clbid_lookup_map,
            forced_clbid_lookup_map_=forced or {},
        )

    def transcript(self) -> List[CourseInstance]:
        return self.transcript_

    def find_ap_ib_credit_course(self, *, name: str) -> Optional[CourseInstance]:
        for c in self.transcript():
            if c.course_type is CourseType.AP and c.name == name:
                return c
        return None

    def find_all_courses(self, c: str) -> Iterator[CourseInstance]:
        for crs in self.transcript():
            if not crs.is_stolaf:
                continue
            if crs.identity_ == c:
                yield crs

    def find_course_by_clbid(self, clbid: str) -> Optional[CourseInstance]:
        return self.clbid_lookup_map_.get(clbid, None)

    def forced_course_by_clbid(self, clbid: str, path: Sequence[str]) -> CourseInstance:
        match = self.find_course_by_clbid(clbid)
        if not match:
            match = self.forced_clbid_lookup_map_.get(clbid, None)
        if not match:
            raise Exception(f'attempted to use CLBID={clbid} at {list(path)}, but it was not found in the transcript')
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

        path_reqs_only = tuple(r for r in path if r.startswith('%'))

        # build a claim so it can be returned later
        claim = Claim(course=course, claimant_path=tuple(path), claimant_requirements=path_reqs_only)

        # > A multicountable set describes the ways in which a course may be
        # > counted.

        # > If no multicountable set describes the course, it may only be
        # > counted once.

        # If the claimant is a CourseRule specified with the `.allow_claimed`
        # option, the claim succeeds (and is not recorded).
        if allow_claimed or (isinstance(rule, CourseRule) and rule.allow_claimed):
            if debug: logger.debug('claim for clbid=%s allowed due to rule having allow_claimed', course.clbid)
            return ClaimAttempt(claim, conflict_with=frozenset(), failed=False)

        prior_claims = frozenset(self.claims[course.clbid])

        # If there are no prior claims, the claim is automatically allowed.
        if not prior_claims:
            if debug: logger.debug('no prior claims for clbid=%s', course.clbid)
            self.claims[course.clbid].add(claim)
            return ClaimAttempt(claim, conflict_with=frozenset(), failed=False)

        # Find any multicountable sets that may apply to this course
        applicable_reqpaths: List[Tuple[str, ...]] = self.multicountable.get(course.course(), [])

        # If there are no applicable multicountable sets, return a claim
        # attempt against the prior claims. If there are no prior claims, it
        # is automatically successful.
        if not applicable_reqpaths:
            if prior_claims:
                if debug: logger.debug('no multicountable reqpaths for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims), failed=True)
            else:
                if debug: logger.debug('no multicountable reqpaths for clbid=%s; the claim has no conflicts', course.clbid)
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset(), failed=False)

        # We can allow a course to be claimed by multiple requirements, if
        # that's what is required by the department.
        #
        # A `multicountable` attribute is a dictionary of {DEPTNUM: List[RequirementPath]}.
        #
        # That is, it looks like the following:
        #
        # multicountable: [
        #   "DEPT 123": [
        #     ["Requirement Name"],
        #     ["A", "Nested", "Requirement"],
        #   ],
        # }
        #
        # where each of the RequirementPath is a list of strings that match up
        # to a requirement defined somewhere in the file.

        prior_claimers = set(cl.claimant_requirements for cl in prior_claims)

        if debug: logger.debug('applicable reqpaths: %s', applicable_reqpaths)

        applicable_reqpath = None

        for reqpath in applicable_reqpaths:
            if debug: logger.debug('checking reqpath %s', reqpath)

            if reqpath == path_reqs_only:
                if debug: logger.debug('done checking reqpaths')
                applicable_reqpath = reqpath
                break

            if debug: logger.debug('done checking reqpath %s; ', reqpath)

        if applicable_reqpath is None:
            if prior_claims:
                if debug: logger.debug('no applicable multicountable reqpath was found for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims), failed=True)
            else:
                if debug: logger.debug('no applicable multicountable reqpath was found for clbid=%s; the claim has no conflicts', course.clbid)
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset(), failed=False)

        # now limit to just the clauses in the reqpath which have not been used
        available_reqpaths = [
            reqpath
            for reqpath in applicable_reqpath
            if reqpath not in prior_claimers
        ]

        if not available_reqpaths:
            if debug: logger.debug('there was an applicable multicountable reqpath for clbid=%s; however, all of the clauses have already been matched', course.clbid)
            if prior_claims:
                return ClaimAttempt(claim, conflict_with=frozenset(prior_claims), failed=True)
            else:
                self.claims[course.clbid].add(claim)
                return ClaimAttempt(claim, conflict_with=frozenset(), failed=False)

        if debug: logger.debug('there was an applicable multicountable reqpath for clbid=%s: %s', course.clbid, available_reqpaths)
        self.claims[course.clbid].add(claim)
        return ClaimAttempt(claim, conflict_with=frozenset(), failed=False)
