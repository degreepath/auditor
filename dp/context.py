import attr
from typing import List, Optional, Mapping, Tuple, Dict, Set, Sequence, Iterable, Iterator
from collections import defaultdict
from contextlib import contextmanager
import logging

from .base.course import BaseCourseRule
from .data.course import CourseInstance
from .data.area_pointer import AreaPointer
from .data.music import MusicPerformance, MusicAttendance, MusicProficiencies
from .data.student import TemplateCourse, course_filter, SUB_TYPE_LOOKUP
from .claim import Claim
from .exception import RuleException, OverrideException, InsertionException, ValueException

logger = logging.getLogger(__name__)
debug: Optional[bool] = None

ExceptionsDict = Mapping[Tuple[str, ...], List[RuleException]]


def group_exceptions(exceptions: Sequence[RuleException]) -> ExceptionsDict:
    grouped: Dict[Tuple[str, ...], List[RuleException]] = defaultdict(list)

    for e in exceptions:
        grouped[e.path].append(e)

    return grouped


@attr.s(slots=True, kw_only=True, frozen=False, auto_attribs=True)
class RequirementContext:
    transcript_: List[CourseInstance] = attr.ib(factory=list)
    transcript_with_excluded_: List[CourseInstance] = attr.ib(factory=list)
    course_set_: Set[str] = attr.ib(factory=set)
    clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)
    forced_clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)
    transcript_with_failed_: List[CourseInstance] = attr.ib(factory=list)

    multicountable: Dict[str, List[Tuple[str, ...]]] = attr.ib(factory=dict)
    claims: Dict[str, List[Claim]] = attr.ib(factory=lambda: defaultdict(list))

    exceptions: ExceptionsDict = attr.ib(factory=dict)
    exceptions_path_lookup_cache: Dict[Tuple[str, ...], bool] = attr.ib(factory=dict)

    areas: Tuple[AreaPointer, ...] = tuple()
    music_performances: Tuple[MusicPerformance, ...] = tuple()
    music_attendances: Tuple[MusicAttendance, ...] = tuple()
    music_proficiencies: MusicProficiencies = MusicProficiencies()

    templates: Mapping[str, Tuple[TemplateCourse, ...]] = attr.ib(factory=dict)

    def with_transcript(
        self,
        transcript: Iterable[CourseInstance],
        *,
        forced: Optional[Dict[str, CourseInstance]] = None,
        full: Iterable[CourseInstance] = tuple(),
        including_failed: Iterable[CourseInstance] = tuple(),
    ) -> 'RequirementContext':
        transcript = list(transcript)
        course_set = set(c.course() for c in transcript)
        clbid_lookup_map = {c.clbid: c for c in transcript}

        return attr.evolve(
            self,
            transcript_=transcript,
            transcript_with_failed_=list(including_failed),
            transcript_with_excluded_=list(full),
            course_set_=course_set,
            clbid_lookup_map_=clbid_lookup_map,
            forced_clbid_lookup_map_=forced or {},
        )

    def transcript(self) -> List[CourseInstance]:
        return self.transcript_

    def transcript_with_excluded(self) -> List[CourseInstance]:
        return self.transcript_with_excluded_

    def all_claimed(self) -> List[CourseInstance]:
        return [self.clbid_lookup_map_[clbid] for clbid in self.claims.keys()]

    def has_claim(self, *, clbid: str) -> bool:
        return clbid in self.claims and len(self.claims[clbid]) > 0

    def find_courses(self, *, rule: BaseCourseRule, from_claimed: bool = False) -> Iterator[CourseInstance]:
        if rule.clbid:
            clbid_match = self.find_course_by_clbid(rule.clbid)
            if clbid_match:
                yield clbid_match
            return

        source = self.transcript() if not from_claimed else self.all_claimed()

        yield from filter(course_filter(
            ap=rule.ap,
            course=rule.course,
            institution=rule.institution,
            name=rule.name,
            year=rule.year,
            term=rule.term,
            section=rule.section,
            sub_type=SUB_TYPE_LOOKUP.get(rule.sub_type or '', None),
        ), source)

    def find_course_by_clbid(self, clbid: str) -> Optional[CourseInstance]:
        return self.clbid_lookup_map_.get(clbid, None)

    def forced_course_by_clbid(self, clbid: str, path: Sequence[str]) -> CourseInstance:
        match = self.find_course_by_clbid(clbid)
        if not match:
            match = self.forced_clbid_lookup_map_.get(clbid, None)
        if not match:
            raise Exception(f'attempted to use CLBID={clbid} at {list(path)}, but it was not found in the transcript')
        return match

    def has_area_code(self, code: str) -> bool:
        return any(code == c.code for c in self.areas)

    def has_course(self, c: str) -> bool:
        return c in self.course_set_

    def has_ip_course(self, c: str) -> bool:
        for _ in filter(course_filter(course=c, in_progress=True), self.transcript()):
            return True

        return False

    def has_completed_course(self, c: str) -> bool:
        for _ in filter(course_filter(course=c, in_progress=False), self.transcript()):
            return True

        return False

    def has_exception_beneath(self, path: Tuple[str, ...]) -> bool:
        cached_lookup = self.exceptions_path_lookup_cache.get(path, None)

        if cached_lookup is not None:
            return cached_lookup

        exists = (
            path in self.exceptions or any(
                e.path[:len(path)] == path
                for group in self.exceptions.values()
                for e in group
            )
        )

        self.exceptions_path_lookup_cache[path] = exists

        return exists

    def get_insert_exceptions(self, path: Tuple[str, ...]) -> Iterator[InsertionException]:
        if path not in self.exceptions:
            return

        for exception in self.exceptions.get(path, []):
            if isinstance(exception, InsertionException):
                yield exception

    def get_insert_exceptions_beneath(self, path: Tuple[str, ...]) -> Iterator[InsertionException]:
        if not self.has_exception_beneath(path):
            return

        path_len = len(path)

        for known_path, group in self.exceptions.items():
            if known_path[:path_len] == path:
                for exception in group:
                    if isinstance(exception, InsertionException):
                        yield exception

    def get_waive_exception(self, path: Tuple[str, ...]) -> Optional[OverrideException]:
        if path not in self.exceptions:
            return None

        for exception in self.exceptions.get(path, []):
            if isinstance(exception, OverrideException):
                return exception

        return None

    def get_value_exception(self, path: Tuple[str, ...]) -> Optional[ValueException]:
        if path not in self.exceptions:
            return None

        for exception in self.exceptions.get(path, []):
            if isinstance(exception, ValueException):
                return exception

        return None

    @contextmanager
    def fresh_claims(self) -> Iterator[None]:
        claims = self.claims
        self.reset_claims()

        try:
            yield
        finally:
            self.set_claims(claims)

    def set_claims(self, claims: Dict[str, List[Claim]]) -> None:
        self.claims = defaultdict(list, {k: list(v) for k, v in claims.items()})

    def reset_claims(self) -> None:
        self.claims = defaultdict(list)

    def with_empty_claims(self) -> 'RequirementContext':
        return attr.evolve(self, claims=defaultdict(list))

    def make_claim(self, *, course: CourseInstance, path: Tuple[str, ...], allow_claimed: bool = False) -> Claim:
        """
        Make claims against courses, to ensure that they are only used once
        (with exceptions) in an audit.
        """

        # This function is called often enough that we want to avoid even
        # calling the `logging` module unless we're actually logging things.
        # (On a 90-second audit, this saved nearly 30 seconds.)
        global debug
        if debug is None:
            debug = __debug__ and logger.isEnabledFor(logging.DEBUG)

        if debug:
            logger.debug('attempting claim for %r [at %s]', course, path)

        # If the `.allow_claimed` option is set, the claim succeeds (and is
        # not recorded).
        if allow_claimed:
            if debug: logger.debug('claim approved; rule has allow_claimed==True')
            return Claim(course=course, claimed_by=path, failed=False)

        # If there are no prior claims, the claim is automatically allowed.
        if course.clbid not in self.claims:
            if debug: logger.debug('claim approved; no prior claims')
            claim = Claim(course=course, claimed_by=path, failed=False)
            self.claims[course.clbid].append(claim)
            return claim

        prior_claims = self.claims[course.clbid]

        # > A multicountable set describes the ways in which a course may be
        # > counted. If no multicountable set describes the course, it may only
        # > be counted once.

        # See if any multicountable sets apply to this course.
        if course.course() in self.multicountable:
            return self._make_multicountable_claim(course=course, path=path, allow_claimed=allow_claimed)

        # If there are no applicable multicountable sets, return a claim
        # attempt against the prior claims.
        if prior_claims:
            if debug: logger.debug('claim denied; no multicountable reqpaths; conflicts with %s', prior_claims)
            return Claim(course=course, claimed_by=path, failed=True)

        # If there are no prior claims, it is automatically successful.
        if debug: logger.debug('claim approved; no multicountable reqpaths; no conflicts')
        claim = Claim(course=course, claimed_by=path, failed=False)
        self.claims[course.clbid].append(claim)
        return claim

    def _make_multicountable_claim(self, *, course: CourseInstance, path: Tuple[str, ...], allow_claimed: bool) -> Claim:
        """
        We can allow a course to be claimed by multiple requirements, if
        that's what is required by the department.

        A `multicountable` attribute is a dictionary of {DEPTNUM: List[RequirementPath]}.

        That is, it looks like the following:

        multicountable: [
          "DEPT 123": [
            ["Requirement Name"],
            ["A", "Nested", "Requirement"],
          ],
        }

        where each of the RequirementPath is a list of strings that match up
        to a requirement defined somewhere in the file.
        """

        path_reqs_only = tuple(r for r in path if r[0] == '%')

        prior_claims = self.claims[course.clbid]
        applicable_reqpaths: List[Tuple[str, ...]] = self.multicountable.get(course.course(), [])

        prior_claimers = list(set(tuple(r for r in cl.claimed_by if r[0] == '%') for cl in prior_claims))

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
                if debug: logger.debug('no applicable multicountable reqpath was found for %r; the claim conflicts with %s', course, prior_claims)
                return Claim(course=course, claimed_by=path, failed=True)
            else:
                if debug: logger.debug('no applicable multicountable reqpath was found for %r; the claim has no conflicts', course)
                claim = Claim(course=course, claimed_by=path, failed=False)
                self.claims[course.clbid].append(claim)
                return claim

        # now limit to just the clauses in the reqpath which have not been used
        available_reqpaths = [
            reqpath
            for reqpath in applicable_reqpath
            if reqpath not in prior_claimers
        ]

        if not available_reqpaths:
            if debug: logger.debug('there was an applicable multicountable reqpath for %r; however, all of the clauses have already been matched', course)
            if prior_claims:
                return Claim(course=course, claimed_by=path, failed=True)
            else:
                claim = Claim(course=course, claimed_by=path, failed=False)
                self.claims[course.clbid].append(claim)
                return claim

        if debug: logger.debug('there was an applicable multicountable reqpath for %r: %s', course, available_reqpaths)
        claim = Claim(course=course, claimed_by=path, failed=False)
        self.claims[course.clbid].append(claim)
        return claim
