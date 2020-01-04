from typing import Tuple, FrozenSet, Dict, List, Any, Iterator
import attr
import datetime

from ..constants import Constants

from .course import load_course, CourseInstance
from .course_enums import GradeOption, GradeCode, TranscriptCode
from .area_pointer import AreaPointer
from .music import MusicAttendance, MusicPerformance, MusicProficiencies, MusicMediums


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, hash=True)
class TermInfo:
    start: datetime.date
    end: datetime.date
    term: str
    name: str

    @staticmethod
    def from_dict(data: Dict) -> 'TermInfo':
        return TermInfo(
            start=datetime.datetime.strptime(data['start'], '%Y-%m-%d'),
            end=datetime.datetime.strptime(data['end'], '%Y-%m-%d'),
            term=data['term'],
            name=data['name'],
        )


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True, hash=True)
class Student:
    stnum: str = '000000'
    curriculum: int = 0
    catalog: int = 0
    matriculation: int = 0

    courses: Tuple[CourseInstance, ...] = tuple()
    courses_with_failed: Tuple[CourseInstance, ...] = tuple()
    areas: Tuple[AreaPointer, ...] = tuple()

    enrollments: FrozenSet[str] = frozenset()
    terms: Tuple[TermInfo, ...] = tuple()

    music_performances: Tuple[MusicPerformance, ...] = tuple()
    music_recital_slips: Tuple[MusicAttendance, ...] = tuple()
    music_mediums: MusicMediums = MusicMediums()
    music_proficiencies: MusicProficiencies = MusicProficiencies()

    @staticmethod
    def load(data: Dict) -> 'Student':
        area_pointers = [AreaPointer.from_dict(a) for a in data.get('areas', [])]

        courses = [c for c in load_transcript(data.get('courses', []))]
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
            courses=tuple(courses),
            courses_with_failed=tuple(courses_with_failed),
            music_performances=tuple(music_performances),
            music_recital_slips=tuple(music_recital_slips),
            music_proficiencies=music_proficiencies,
            music_mediums=music_mediums,
        )

    def constants(self) -> Constants:
        return Constants(matriculation_year=self.matriculation)


def load_transcript(courses: List[Dict[str, Any]], *, include_failed: bool = False) -> Iterator[CourseInstance]:
    # We need to leave repeated courses in the transcript, because some majors
    # (THEAT) require repeated courses for completion (and others )
    for row in courses:
        c = load_course(row)

        # excluded Audited courses
        if c.grade_option is GradeOption.Audit:
            continue

        # excluded repeated courses
        if c.transcript_code in (TranscriptCode.RepeatedLater, TranscriptCode.RepeatInProgress):
            continue

        # exclude [N]o-Pass, [U]nsuccessful, [AU]dit, [UA]nsuccessfulAudit, [WF]ithdrawnFail, [WP]ithdrawnPass, and [Withdrawn]
        if c.grade_code in (GradeCode._N, GradeCode._U, GradeCode._AU, GradeCode._UA, GradeCode._WF, GradeCode._WP, GradeCode._W):
            continue

        # exclude courses at grade F
        if c.grade_code is GradeCode.F:
            if include_failed is True:
                pass
            else:
                continue

        yield c
