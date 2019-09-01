import json
import traceback
import pathlib
from typing import Iterator, List, Dict, Any

import yaml
import csv
import sys
import os

from degreepath import load_course, Constants, AreaPointer, load_exception, AreaOfStudy
from degreepath.data import GradeOption, GradeCode, CourseInstance
from degreepath.audit import audit, NoStudentsMsg, AuditStartMsg, ExceptionMsg, AreaFileNotFoundMsg, Message, Arguments


def run(args: Arguments, *, transcript_only: bool = False) -> Iterator[Message]:  # noqa: C901
    if not args.student_files:
        yield NoStudentsMsg()
        return

    for student_file in args.student_files:
        try:
            with open(student_file, "r", encoding="utf-8") as infile:
                student = json.load(infile)
        except FileNotFoundError as ex:
            yield ExceptionMsg(ex=ex, tb=traceback.format_exc(), stnum=None, area_code=None)
            return

        area_pointers = tuple([AreaPointer.from_dict(a) for a in student['areas']])
        constants = Constants(matriculation_year=student['matriculation'])
        transcript = tuple(load_transcript(student['courses']))

        if transcript_only:
            writer = csv.writer(sys.stdout)
            writer.writerow(['course', 'clbid', 'course_type', 'credits', 'name', 'year', 'term', 'type', 'gereqs', 'is_repeat', 'in_gpa', 'attributes'])
            for c in transcript:
                writer.writerow([
                    c.course(), c.clbid, c.course_type.value, str(c.credits), c.name, str(c.year), str(c.term),
                    c.sub_type.name, ','.join(c.gereqs), str(c.is_repeat), str(c.is_in_gpa),
                    ','.join(c.attributes),
                ])
            return

        for area_file in args.area_files:
            try:
                with open(area_file, "r", encoding="utf-8") as infile:
                    area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            except FileNotFoundError:
                yield AreaFileNotFoundMsg(area_file=f"{os.path.dirname(area_file)}/{os.path.basename(area_file)}", stnum=student['stnum'])
                return

            area_code = pathlib.Path(area_file).stem
            area_catalog = pathlib.Path(area_file).parent.stem

            exceptions = [
                load_exception(e)
                for e in student.get("exceptions", [])
                if e['area_code'] == area_code
            ]

            area = AreaOfStudy.load(specification=area_spec, c=constants, areas=area_pointers, area_code=area_code)
            area.validate()

            yield AuditStartMsg(stnum=student['stnum'], area_code=area_code, area_catalog=area_catalog)

            try:
                yield from audit(
                    area=area,
                    exceptions=exceptions,
                    transcript=transcript,
                    constants=constants,
                    area_pointers=area_pointers,
                    print_all=args.print_all,
                    estimate_only=args.estimate_only,
                )

            except Exception as ex:
                yield ExceptionMsg(ex=ex, tb=traceback.format_exc(), stnum=student['stnum'], area_code=area_code)


def load_transcript(courses: List[Dict[str, Any]]) -> Iterator[CourseInstance]:
    # We need to leave repeated courses in the transcript, because some majors
    # (THEAT) require repeated courses for completion (and others )
    for row in courses:
        c = load_course(row)

        # excluded Audited courses
        if c.grade_option is GradeOption.Audit:
            continue

        # exclude [N]o-Pass, [U]nsuccessful, [UA]nsuccessfulAudit, [WF]ithdrawnFail, [WP]ithdrawnPass, and [Withdrawn]
        if c.grade_code in (GradeCode._N, GradeCode._U, GradeCode._UA, GradeCode._WF, GradeCode._WP, GradeCode._W):
            continue

        # exclude courses at grade F
        if c.grade_code is GradeCode.F:
            continue

        yield c
