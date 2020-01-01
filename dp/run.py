import json
from typing import Iterator, List, Dict

import yaml
import csv
import sys

from . import Constants, AreaPointer, load_exception, AreaOfStudy
from .lib import grade_point_average_items, grade_point_average
from .data import MusicPerformance, MusicAttendance, MusicProficiencies
from .load_transcript import load_transcript
from .audit import audit, Message, Arguments


def run(args: Arguments, *, student: Dict, area_spec: Dict) -> Iterator[Message]:
    area_pointers = tuple(AreaPointer.from_dict(a) for a in student['areas'])
    constants = Constants(matriculation_year=0 if student['matriculation'] == '' else int(student['matriculation']))
    transcript = tuple(sorted(load_transcript(student['courses']), key=lambda course: course.sort_order()))
    transcript_with_failed = tuple(sorted(load_transcript(student['courses'], include_failed=True), key=lambda course: course.sort_order()))

    if args.transcript_only:
        writer = csv.writer(sys.stdout)
        writer.writerow(['course', 'name', 'clbid', 'type', 'credits', 'term', 'type', 'grade', 'in_gpa'])
        for c in transcript:
            writer.writerow([
                c.course(), c.name, c.clbid, c.course_type.value, str(c.credits), f"{c.year}-{c.term}",
                c.sub_type.name, c.grade_code.value, 'Y' if c.is_in_gpa else 'N',
            ])
        return

    if args.gpa_only:
        writer = csv.writer(sys.stdout)
        writer.writerow(['course', 'grade', 'points'])

        applicable = sorted(grade_point_average_items(transcript_with_failed), key=lambda c: (c.year, c.term, c.course(), c.clbid))
        for c in applicable:
            writer.writerow([c.course(), c.grade_code.value, str(c.grade_points)])

        writer.writerow(['---', 'gpa:', str(grade_point_average(transcript_with_failed))])
        return

    music_performances = tuple(sorted((MusicPerformance.from_dict(d) for d in student['performances']), key=lambda p: p.sort_order()))
    music_attendances = tuple(sorted((MusicAttendance.from_dict(d) for d in student['performance_attendances']), key=lambda a: a.sort_order()))
    music_proficiencies = MusicProficiencies.from_dict(student['proficiencies'])

    area_code = area_spec['code']

    exceptions = [
        load_exception(e)
        for e in student.get("exceptions", [])
        if e['area_code'] == area_code
    ]

    area = AreaOfStudy.load(
        specification=area_spec,
        c=constants,
        areas=area_pointers,
        transcript=transcript,
        exceptions=exceptions,
    )
    area.validate()

    yield from audit(
        area=area,
        music_performances=music_performances,
        music_attendances=music_attendances,
        music_proficiencies=music_proficiencies,
        exceptions=exceptions,
        transcript=transcript,
        transcript_with_failed=transcript_with_failed,
        constants=constants,
        area_pointers=area_pointers,
        args=args,
    )


def load_students(*filenames: str) -> List[Dict]:
    file_data = []

    for student_file in filenames:
        with open(student_file, "r", encoding="utf-8") as infile:
            file_data.append(json.load(infile))

    return file_data


def load_areas(*filenames: str) -> List[Dict]:
    specs: List[Dict] = []

    for area_file in filenames:
        with open(area_file, "r", encoding="utf-8") as infile:
            specs.append(yaml.load(stream=infile, Loader=yaml.SafeLoader))

    return specs
