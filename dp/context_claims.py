from typing import List, Optional, Tuple, Dict
from collections import defaultdict
import logging

import attr

from .claim import Claim
from .data.course import CourseInstance

logger = logging.getLogger(__name__)
debug: Optional[bool] = None


@attr.s(slots=True, kw_only=True, frozen=False, auto_attribs=True)
class ContextClaims:
    multicountable: Dict[str, List[Tuple[str, ...]]] = attr.ib(factory=dict)
    claims: Dict[str, List[Claim]] = attr.ib(factory=lambda: defaultdict(list))

    def claimed_clbids(self) -> List[str]:
        return list(self.claims.keys())

    def merge(self, other: 'ContextClaims') -> 'ContextClaims':
        merged_dict = {**self.claims, **other.claims}
        return attr.evolve(self, claims=defaultdict(list, {k: list(v) for k, v in merged_dict.items()}))

    def empty(self) -> 'ContextClaims':
        return attr.evolve(self, claims=defaultdict(list))

    def has_claims(self) -> bool:
        return bool(self.claims)

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

        # If the `.allow_claimed` option is set, the claim succeeds (and is
        # not recorded).
        if allow_claimed:
            if debug: logger.debug('claim for clbid=%s allowed due to rule having allow_claimed', course.clbid)
            return Claim(course=course, claimed_by=path, failed=False)

        # If there are no prior claims, the claim is automatically allowed.
        if course.clbid not in self.claims:
            if debug: logger.debug('no prior claims for clbid=%s', course.clbid)
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
            if debug: logger.debug('no multicountable reqpaths for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
            return Claim(course=course, claimed_by=path, failed=True)

        # If there are no prior claims, it is automatically successful.
        if debug: logger.debug('no multicountable reqpaths for clbid=%s; the claim has no conflicts', course.clbid)
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
                if debug: logger.debug('no applicable multicountable reqpath was found for clbid=%s; the claim conflicts with %s', course.clbid, prior_claims)
                return Claim(course=course, claimed_by=path, failed=True)
            else:
                if debug: logger.debug('no applicable multicountable reqpath was found for clbid=%s; the claim has no conflicts', course.clbid)
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
            if debug: logger.debug('there was an applicable multicountable reqpath for clbid=%s; however, all of the clauses have already been matched', course.clbid)
            if prior_claims:
                return Claim(course=course, claimed_by=path, failed=True)
            else:
                claim = Claim(course=course, claimed_by=path, failed=False)
                self.claims[course.clbid].append(claim)
                return claim

        if debug: logger.debug('there was an applicable multicountable reqpath for clbid=%s: %s', course.clbid, available_reqpaths)
        claim = Claim(course=course, claimed_by=path, failed=False)
        self.claims[course.clbid].append(claim)
        return claim
