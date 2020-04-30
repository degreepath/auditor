from typing import Tuple, Dict, List, Set, Any, Iterator, Optional, Sequence, Mapping

import attr

from ..constants import Constants
from ..exception import CourseOverrideException

from .area_enums import AreaStatus
from .course import load_course, CourseInstance
from .course_enums import GradeOption, GradeCode, TranscriptCode
from .area_pointer import AreaPointer
from .music import MusicAttendance, MusicPerformance, MusicProficiencies, MusicMediums


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Student:
    stnum: str = '000000'
    curriculum: int = 0
    catalog: int = 0
    matriculation: int = 0
    current_area_code: str = '000'

    courses: Tuple[CourseInstance, ...] = tuple()
    courses_with_failed: Tuple[CourseInstance, ...] = tuple()
    areas: Tuple[AreaPointer, ...] = tuple()

    music_performances: Tuple[MusicPerformance, ...] = tuple()
    music_recital_slips: Tuple[MusicAttendance, ...] = tuple()
    music_mediums: MusicMediums = MusicMediums()
    music_proficiencies: MusicProficiencies = MusicProficiencies()

    templates: Tuple[Tuple[str, str], ...] = tuple()

    @staticmethod
    def load(
        data: Dict,
        *,
        code: str = '000',
        overrides: Sequence[CourseOverrideException] = tuple(),
        credits_overrides: Optional[Dict[str, str]] = None,
    ) -> 'Student':
        if not credits_overrides:
            credits_overrides = {}

        overrides = list(overrides)

        area_pointers = [AreaPointer.from_dict(a) for a in data.get('areas', [])]
        # pretend that they've dropped any what-if-dropped areas
        area_pointers = [a for a in area_pointers if a.status is not AreaStatus.WhatIfDrop or a.code == code]

        current_term = data.get('current_term', None)

        data_courses = data.get('courses', [])
        load_transcript_args = dict(current_term=current_term, overrides=overrides, credits_overrides=credits_overrides)
        courses = [c for c in load_transcript(data_courses, **load_transcript_args)]
        courses = sorted(courses, key=lambda c: c.sort_order())

        courses_with_failed = [c for c in load_transcript(data_courses, include_failed=True, **load_transcript_args)]
        courses_with_failed = sorted(courses_with_failed, key=lambda c: c.sort_order())

        music_performances = [MusicPerformance.from_dict(d) for d in data.get('performances', [])]
        music_performances = sorted(music_performances, key=lambda p: p.sort_order())

        music_recital_slips = [MusicAttendance.from_dict(d) for d in data.get('performance_attendances', [])]
        music_recital_slips = sorted(music_recital_slips, key=lambda a: a.sort_order())

        music_proficiencies = MusicProficiencies.from_dict(data.get('proficiencies', {}))
        music_mediums = MusicMediums.from_dict(data.get('mediums', {}))

        matriculation = data.get('matriculation', None)
        if not matriculation:
            matriculation = 0
        else:
            matriculation = int(data.get('matriculation', '0'))

        templates_set = {(key, course) for key, courses in data.get('templates', {}).items() for course in courses}
        templates = tuple(sorted(templates_set))

        return Student(
            stnum=data.get('stnum', '000000'),
            curriculum=int(data.get('curriculum', 0)),
            catalog=int(data.get('catalog', 0)),
            current_area_code=code,
            matriculation=matriculation,
            areas=tuple(area_pointers),
            courses=tuple(courses),
            courses_with_failed=tuple(courses_with_failed),
            music_performances=tuple(music_performances),
            music_recital_slips=tuple(music_recital_slips),
            music_proficiencies=music_proficiencies,
            music_mediums=music_mediums,
            templates=templates,
        )

    def constants(self) -> Constants:
        try:
            current_area = next(a for a in self.areas if a.code == self.current_area_code)
            terms_since_declaring_major = current_area.terms_since_declaration
        except StopIteration:
            terms_since_declaring_major = 0

        terms_since_declaring_major = terms_since_declaring_major or 0

        return Constants(
            matriculation_year=self.matriculation,
            primary_performing_medium=self.music_mediums.ppm,
            current_area_code=self.current_area_code,
            terms_since_declaring_major=terms_since_declaring_major,
        )

    def templates_as_dict(self) -> Mapping[str, Tuple[str, ...]]:
        result: Dict[str, List[str]] = dict()
        for key, course in self.templates:
            result.setdefault(key, []).append(course)

        return {key: tuple(courses) for key, courses in result.items()}


def load_transcript(
    courses: List[Dict[str, Any]],
    *,
    include_failed: bool = False,
    current_term: Optional[str] = None,
    overrides: List[CourseOverrideException],
    credits_overrides: Dict[str, str],
) -> Iterator[CourseInstance]:
    skip_grades = {
        GradeCode._N,  # NoPass
        GradeCode._U,  # Unsuccessful
        GradeCode._AU,  # Audit
        GradeCode._UA,  # Unsuccessful Audit
        GradeCode._WF,  # WithdrawnFail
        GradeCode._WP,  # WithdrawnPass
        GradeCode._W,  # Withdrawn
    }

    # If someone has managed to be enrolled in the same CLBID twice, we prefer
    # the first one, such that the first one retains the actual CLBID, and the
    # second gets a generated ID of the form "clbid:schedid" instead.
    clbids: Set[str] = set()

    for row in courses:
        c = load_course(row, current_term=current_term, overrides=overrides, credits_overrides=credits_overrides)

        if c.clbid in clbids:
            old_clbid = c.clbid
            c = c.unique_clbid_via_schedid()
            new_clbid = c.clbid
            assert old_clbid != new_clbid
            assert new_clbid not in clbids
            clbids.add(c.clbid)
        else:
            clbids.add(c.clbid)

        # excluded Audited courses
        if c.grade_option is GradeOption.Audit:
            continue

        # excluded repeated courses
        if c.transcript_code in (TranscriptCode.RepeatedLater, TranscriptCode.RepeatInProgress):
            continue

        if c.grade_code in skip_grades:
            continue

        # exclude courses at grade F
        if c.grade_code is GradeCode.F:
            if include_failed is True:
                pass
            else:
                continue

        yield c
