from typing import Tuple, FrozenSet, Dict, List, Any, Iterator, Optional
import datetime

import attr

from ..constants import Constants

from .course import load_course, CourseInstance
from .course_enums import GradeOption, GradeCode, TranscriptCode
from .area_pointer import AreaPointer
from .music import MusicAttendance, MusicPerformance, MusicProficiencies, MusicMediums
from .terminfo import TermInfo, find_current_or_next_term, TermType


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class Student:
    stnum: str = '000000'
    curriculum: int = 0
    catalog: int = 0
    matriculation: int = 0

    courses: Tuple[CourseInstance, ...] = tuple()
    courses_with_failed: Tuple[CourseInstance, ...] = tuple()
    areas: Tuple[AreaPointer, ...] = tuple()

    enrollments: FrozenSet[str] = frozenset()
    semesters: Tuple[TermInfo, ...] = tuple()

    music_performances: Tuple[MusicPerformance, ...] = tuple()
    music_recital_slips: Tuple[MusicAttendance, ...] = tuple()
    music_mediums: MusicMediums = MusicMediums()
    music_proficiencies: MusicProficiencies = MusicProficiencies()

    @staticmethod
    def load(data: Dict, *, now: datetime.datetime = datetime.datetime.now()) -> 'Student':
        area_pointers = [AreaPointer.from_dict(a) for a in data.get('areas', [])]

        terms = [TermInfo.from_dict(t) for t in data.get('terms', [])]
        current_term = find_current_or_next_term(terms, ts=now)
        semesters = [t for t in terms if t.type is TermType.Semester]

        enrollments = frozenset(data.get('enrollments', []))

        courses = [c for c in load_transcript(data.get('courses', []), current_term=current_term)]
        courses = sorted(courses, key=lambda c: c.sort_order())

        courses_with_failed = [c for c in load_transcript(data.get('courses', []), include_failed=True)]
        courses_with_failed = sorted(courses_with_failed, key=lambda c: c.sort_order())

        music_performances = [MusicPerformance.from_dict(d) for d in data.get('performances', [])]
        music_performances = sorted(music_performances, key=lambda p: p.sort_order())

        music_recital_slips = [MusicAttendance.from_dict(d) for d in data.get('performance_attendances', [])]
        music_recital_slips = sorted(music_recital_slips, key=lambda a: a.sort_order())

        music_proficiencies = MusicProficiencies.from_dict(data.get('proficiencies', {}))
        music_mediums = MusicMediums.from_dict(data.get('mediums', {}))

        matriculation = data.get('matriculation', '0')
        if matriculation == '':
            matriculation = 0
        else:
            matriculation = int(data.get('matriculation', '0'))

        return Student(
            stnum=data.get('stnum', '000000'),
            curriculum=int(data.get('curriculum', 0)),
            catalog=int(data.get('catalog', 0)),
            matriculation=matriculation,
            areas=tuple(area_pointers),
            enrollments=enrollments,
            courses=tuple(courses),
            courses_with_failed=tuple(courses_with_failed),
            music_performances=tuple(music_performances),
            music_recital_slips=tuple(music_recital_slips),
            music_proficiencies=music_proficiencies,
            music_mediums=music_mediums,
            semesters=tuple(semesters),
        )

    def constants(self) -> Constants:
        return Constants(
            matriculation_year=self.matriculation,
            primary_performing_medium=self.music_mediums.ppm,
        )


def load_transcript(courses: List[Dict[str, Any]], *, include_failed: bool = False, current_term: Optional[TermInfo] = None) -> Iterator[CourseInstance]:
    skip_grades = {
        GradeCode._N,  # NoPass
        GradeCode._U,  # Unsuccessful
        GradeCode._AU,  # Audit
        GradeCode._UA,  # Unsuccessful Audit
        GradeCode._WF,  # WithdrawnFail
        GradeCode._WP,  # WithdrawnPass
        GradeCode._W,  # Withdrawn
    }

    for row in courses:
        c = load_course(row, current_term=current_term)

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
