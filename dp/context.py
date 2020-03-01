from typing import List, Optional, Tuple, Dict, Set, Sequence, Collection, Iterable, Iterator
from contextlib import contextmanager
import logging

import attr

from .base.course import BaseCourseRule
from .clause import Clause, apply_clause
from .context_claims import ContextClaims
from .context_exceptions import ContextExceptions
from .data.area_pointer import AreaPointer
from .data.course import CourseInstance
from .data.course_enums import CourseType
from .data.music import MusicPerformance, MusicAttendance, MusicProficiencies

logger = logging.getLogger(__name__)


@attr.s(slots=True, kw_only=True, frozen=False, auto_attribs=True, hash=False, eq=False)
class RequirementContext:
    transcript_: List[CourseInstance] = attr.ib(factory=list)
    transcript_with_excluded_: List[CourseInstance] = attr.ib(factory=list)
    course_set_: Set[str] = attr.ib(factory=set)
    clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)
    forced_clbid_lookup_map_: Dict[str, CourseInstance] = attr.ib(factory=dict)
    transcript_with_failed_: List[CourseInstance] = attr.ib(factory=list)

    claims: ContextClaims = ContextClaims()
    exceptions: ContextExceptions = ContextExceptions()

    areas: Tuple[AreaPointer, ...] = tuple()
    music_performances: Tuple[MusicPerformance, ...] = tuple()
    music_attendances: Tuple[MusicAttendance, ...] = tuple()
    music_proficiencies: MusicProficiencies = MusicProficiencies()

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

    def courses__claimed(self, *, path: Sequence[str], where: Optional[Clause], inserted: Collection[str] = tuple()) -> List[CourseInstance]:
        output: List[CourseInstance] = self.all_claimed()

        if where:
            output = [item for item in output if apply_clause(where, item)]

        for clbid in inserted:
            matched_course = self.forced_course_by_clbid(clbid, path=path)
            output.append(matched_course)

        return output

    def transcript(self) -> List[CourseInstance]:
        return self.transcript_

    def transcript_with_excluded(self) -> List[CourseInstance]:
        return self.transcript_with_excluded_

    def all_claimed(self) -> List[CourseInstance]:
        return [self.clbid_lookup_map_[clbid] for clbid in self.claims.claimed_clbids()]

    def find_courses(self, *, rule: BaseCourseRule, from_claimed: bool = False) -> Iterator[CourseInstance]:
        if rule.clbid:
            match_by_clbid = self.find_course_by_clbid(rule.clbid)
            if match_by_clbid:
                yield match_by_clbid
            return

        ap = rule.ap
        course = rule.course
        institution = rule.institution
        name = rule.name

        query = (course, name, ap, institution, CourseType.AP if ap else None)

        source = self.transcript() if not from_claimed else self.all_claimed()

        for c in source:
            if not c.is_stolaf and institution is None and ap is None:
                continue

            matcher = (
                c.identity_ if course else None,
                c.name if name else None,
                c.name if ap else None,
                c.institution if institution else None,
                c.course_type if ap else None,
            )

            if query == matcher:
                yield c

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

    def with_empty_claims(self) -> 'RequirementContext':
        return attr.evolve(self, claims=self.claims.empty())

    @contextmanager
    def fresh_claims(self) -> Iterator[None]:
        claims = self.claims

        self.claims = self.claims.empty()

        try:
            yield
        finally:
            self.claims = claims
