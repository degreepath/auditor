from typing import Tuple, Dict, List, Set, Any, Iterator, Optional, Sequence, Mapping, Iterable, Union, Callable
import re
import logging

import attr

from ..constants import Constants
from ..exception import CourseOverrideException

from .area_enums import AreaStatus
from .course import load_course, CourseInstance
from .course_enums import GradeOption, GradeCode, TranscriptCode, CourseType, SubType, SUB_TYPE_LOOKUP
from .area_pointer import AreaPointer
from .music import MusicAttendance, MusicPerformance, MusicProficiencies, MusicMediums

logger = logging.getLogger(__name__)


@attr.s(cache_hash=True, slots=True, kw_only=True, frozen=True, auto_attribs=True)
class TemplateCourse:
    subject: str = ''
    num: str = ''
    section: Optional[str] = None
    sub_type: Optional[str] = None
    year: Optional[int] = None
    term: Optional[int] = None
    institution: str = ''
    name: Optional[str] = None
    clbid: str = ''

    def to_course_rule_as_dict(self) -> Dict:
        course: Dict[str, Union[int, str]] = dict()

        if self.clbid:
            course['clbid'] = self.clbid

        if self.subject:
            course['course'] = f"{self.subject} {self.num}"

        if self.section:
            course['section'] = self.section

        if self.sub_type:
            course['sub_type'] = self.sub_type

        if self.institution:
            course['institution'] = self.institution

        if self.name:
            course['ap'] = self.name

        if self.year is not None:
            assert self.term is not None
            course['year'] = self.year
            course['term'] = self.term

        return course


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

    templates: Tuple[Tuple[str, TemplateCourse], ...] = tuple()

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

        templates_set = set(
            (key, parse_template_course_rule(course, transcript=courses))
            for key, course_items in data.get('templates', {}).items()
            for course in course_items
        )
        # exclude the None items from the parsing
        templates = tuple(sorted((key, parsed) for key, parsed in templates_set if parsed))

        curriculum_s: str = data.get('curriculum', 'None')
        if curriculum_s == 'None':
            curriculum_s = '0'
        curriculum = int(curriculum_s)

        return Student(
            stnum=data.get('stnum', '000000'),
            curriculum=curriculum,
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

    def templates_as_dict(self) -> Mapping[str, Tuple[TemplateCourse, ...]]:
        result: Dict[str, List[TemplateCourse]] = dict()
        for key, course in self.templates:
            result.setdefault(key, []).append(course)

        return {key: tuple(courses) for key, courses in result.items()}


DEPTNUM_REGEX = re.compile(r"""
    (?P<subject>[A-Z/]{2,5})           # the subject code
    [ ]                                # a space
    (?P<num>[0-9]{3})                  # the course number
    (?P<section>[A-Z])?                # (optional) the section
    (.(?P<sub_type>[A-Z]))?            # (optional) the sub_type: .L for lab, .F for flac, etc
    (\ (?P<year>\d{4})-(?P<term>\d))?  # (optional) the year-term
    (\ \[(?P<inst>.+)\])?              # (optional) the [INSTITUTION] code
""", re.VERBOSE)

NAME_REGEX = re.compile(r"""
    ^
    name=(?P<name>[^(\[]*)    # the course name
    ([ ]\[(?P<inst>.+)\])?  # (optional) the institution
    $
""", re.VERBOSE)


def parse_template_course_rule(course_label: str, *, transcript: Iterable[CourseInstance]) -> Optional[TemplateCourse]:
    logger.debug(course_label)

    match = DEPTNUM_REGEX.match(course_label)
    if match is not None:
        return parse_identified_course(course_label, match_groups=match.groupdict(), transcript=transcript)

    match = NAME_REGEX.match(course_label)
    if match is not None:
        return parse_named_course(course_label, match_groups=match.groupdict(), transcript=transcript)

    logger.debug('skipping %s', course_label)
    return None


def parse_identified_course(course_label: str, *, match_groups: Dict, transcript: Iterable[CourseInstance]) -> Optional[TemplateCourse]:
    logger.debug('%s: %s', course_label, match_groups)

    subject = match_groups['subject']
    num = match_groups['num']
    section = match_groups['section']
    sub_type = match_groups['sub_type']
    term = int(match_groups['term']) if match_groups['term'] else None
    year = int(match_groups['year']) if match_groups['year'] else None
    institution: str = match_groups.get('inst', '') or ''

    iterable = filter(course_filter(
        course=f"{subject} {num}" if subject else None,
        section=section,
        sub_type=SUB_TYPE_LOOKUP.get(sub_type, None),
        institution=institution,
    ), transcript)

    for crs in iterable:
        logger.debug('found match for %s: %s', course_label, crs)

        return TemplateCourse(
            subject=crs.subject,
            num=crs.number,
            section=section,
            sub_type=sub_type,
            term=term,
            year=year,
            institution=institution,
            name=None,
            clbid=crs.clbid,
        )

    logger.debug('did not find existing match for %s', course_label)

    return TemplateCourse(
        subject=subject,
        num=num,
        section=section,
        sub_type=sub_type,
        term=term,
        year=year,
        institution=institution,
        name=None,
    )


def parse_named_course(course_label: str, *, match_groups: Dict, transcript: Iterable[CourseInstance]) -> Optional[TemplateCourse]:
    logger.debug('%s: %s', course_label, match_groups)

    name = match_groups['name']
    institution: str = match_groups.get('inst', '') or ''

    for crs in transcript:
        if name and crs.name != name:
            continue

        if institution and crs.institution != institution:
            continue

        logger.debug('found match for %s: %s', course_label, crs)

        return TemplateCourse(
            name=name,
            institution=institution,
            subject=crs.subject,
            num=crs.number,
            clbid=crs.clbid,
            section=None,
            sub_type=None,
            term=None,
            year=None,
        )

    logger.debug('did not find existing match for %s', course_label)

    return TemplateCourse(
        institution=institution,
        name=name,
    )


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


@attr.s(slots=True, kw_only=True, frozen=False, auto_attribs=True, order=False, hash=False, repr=False)
class CourseFilterArgs:
    ap: Optional[str] = None
    course: Optional[str] = None
    crsid: Optional[str] = None
    institution: Optional[str] = None
    name: Optional[str] = None
    year: Optional[int] = None
    term: Optional[int] = None
    section: Optional[str] = None
    sub_type: Optional[SubType] = None
    in_progress: Optional[bool] = None


def course_filter(
    *,
    ap: Optional[str] = None,
    course: Optional[str] = None,
    crsid: Optional[str] = None,
    institution: Optional[str] = None,
    name: Optional[str] = None,
    year: Optional[int] = None,
    term: Optional[int] = None,
    section: Optional[str] = None,
    sub_type: Optional[SubType] = None,
    in_progress: Optional[bool] = None,
) -> Callable[[CourseInstance], bool]:
    filter_args = CourseFilterArgs(
        ap=ap,
        course=course,
        crsid=crsid,
        institution=institution,
        name=name,
        year=year,
        term=term,
        section=section,
        sub_type=sub_type,
        in_progress=in_progress,
    )
    return lambda c: _course_filter(c, filter_args)


def _course_filter(c: CourseInstance, f: CourseFilterArgs) -> bool:
    # skip non-STOLAF courses if we're not given an institution
    # and aren't looking for an AP course
    if f.institution is None and f.ap is None and not c.is_stolaf:
        return False

    if f.crsid is not None and f.crsid != c.crsid:
        return False

    # compare course identity
    if f.course is not None:
        if c.identity_ != f.course:
            return False

        # compare sections (given by template majors)
        if f.section is not None and c.section != f.section:
            return False

        # compare years (given by template majors)
        if f.year is not None:
            assert f.term is not None
            if c.year != f.year or c.term != f.term:
                return False

        if f.sub_type is not None and c.sub_type != f.sub_type:
            return False

    # compare course names
    if f.name is not None and c.name != f.name:
        return False

    # compare course institutions
    if f.institution is not None and c.institution != f.institution:
        return False

    # compare for AP courses
    if f.ap is not None:
        if c.course_type != CourseType.AP or c.name != f.ap:
            return False

    if f.in_progress is not None:
        # if we've requested only IP or non-IP courses, and this course
        # doesn't match, then skip it
        if f.in_progress != c.is_in_progress:
            return False

    # if all of the previous have matched, we pass the checks
    return True
