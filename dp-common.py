import json
import traceback
import pathlib
import tarfile
from typing import Iterator, List, Dict, Any

import yaml
import csv
import sys
import os

from degreepath import load_course, Constants, AreaPointer, load_exception, AreaOfStudy
from degreepath.lib import grade_point_average_items, grade_point_average
from degreepath.data import GradeOption, GradeCode, CourseInstance, TranscriptCode
from degreepath.audit import audit, NoStudentsMsg, AuditStartMsg, ExceptionMsg, AreaFileNotFoundMsg, Message, Arguments


def run(args: Arguments, *, transcript_only: bool = False, gpa_only: bool = False) -> Iterator[Message]:  # noqa: C901
    if not args.student_files:
        yield NoStudentsMsg()
        return

    file_data = []

    try:
        if args.archive_file:
            with tarfile.open(args.archive_file, 'r') as tarball:
                for student_file in args.student_files:
                    data = tarball.extractfile(student_file)
                    assert data is not None
                    file_data.append(json.load(data))
        else:
            for student_file in args.student_files:
                with open(student_file, "r", encoding="utf-8") as infile:
                    file_data.append(json.load(infile))
    except FileNotFoundError as ex:
        yield ExceptionMsg(ex=ex, tb=traceback.format_exc(), stnum=None, area_code=None)
        return

    for student in file_data:
        area_pointers = tuple(AreaPointer.from_dict(a) for a in student['areas'])
        constants = Constants(matriculation_year=0 if student['matriculation'] == '' else int(student['matriculation']))
        transcript = tuple(sorted(load_transcript(student['courses']), key=lambda c: c.sort_order()))
        transcript_with_failed = tuple(load_transcript(student['courses'], include_failed=True))

        if transcript_only:
            writer = csv.writer(sys.stdout)
            writer.writerow(['course', 'clbid', 'course_type', 'credits', 'name', 'year', 'term', 'type', 'grade', 'gereqs', 'is_repeat', 'in_gpa', 'attributes'])
            for c in transcript:
                writer.writerow([
                    c.course(), c.clbid, c.course_type.value, str(c.credits), c.name, str(c.year), str(c.term),
                    c.sub_type.name, c.grade_code.value, ','.join(c.gereqs), str(c.is_repeat), str(c.is_in_gpa),
                    ','.join(c.attributes),
                ])
            return

        if gpa_only:
            for c in grade_point_average_items(transcript_with_failed):
                print(c.course(), c.grade_code.value, c.grade_points)
            print(grade_point_average(transcript_with_failed))
            return

        for area_file in args.area_files:
            try:
                with open(area_file, "r", encoding="utf-8") as infile:
                    area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            except FileNotFoundError:
                yield AreaFileNotFoundMsg(area_file=f"{os.path.dirname(area_file)}/{os.path.basename(area_file)}", stnum=student['stnum'])
                return

            area_code = area_spec['code']
            area_catalog = pathlib.Path(area_file).parent.stem

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
            )
            area.validate()

            yield AuditStartMsg(stnum=student['stnum'], area_code=area_code, area_catalog=area_catalog, student=student)

            try:
                yield from audit(
                    area=area,
                    exceptions=exceptions,
                    transcript=transcript,
                    transcript_with_failed=transcript_with_failed,
                    constants=constants,
                    area_pointers=area_pointers,
                    print_all=args.print_all,
                    estimate_only=args.estimate_only,
                )

            except Exception as ex:
                yield ExceptionMsg(ex=ex, tb=traceback.format_exc(), stnum=student['stnum'], area_code=area_code)


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
