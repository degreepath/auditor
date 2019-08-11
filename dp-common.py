import json
import traceback
import pathlib

import yaml

from degreepath import load_course, Constants, AreaPointer, load_exception
from degreepath.audit import audit, NoStudentsMsg, AuditStartMsg, ExceptionMsg, Arguments


def run(args: Arguments, *, transcript_only=False):
    if not args.student_files:
        yield NoStudentsMsg()
        return

    for student_file in args.student_files:
        try:
            with open(student_file, "r", encoding="utf-8") as infile:
                student = json.load(infile)
        except FileNotFoundError as ex:
            yield ExceptionMsg(ex=ex, tb=traceback.format_exc())
            return

        area_pointers = tuple([AreaPointer.from_dict(**a) for a in student['areas']])
        transcript = [load_course(row) for row in student["courses"]]
        constants = Constants(matriculation_year=student['matriculation'])
        exceptions = [load_exception(e) for e in student.get("exceptions", [])]

        if transcript_only:
            for c in transcript:
                print(repr(c))
            return

        for area_file in args.area_files:
            try:
                with open(area_file, "r", encoding="utf-8") as infile:
                    area_spec = yaml.load(stream=infile, Loader=yaml.SafeLoader)
            except FileNotFoundError as ex:
                yield ExceptionMsg(ex=ex, tb=traceback.format_exc())
                return

            area_code = pathlib.Path(area_file).stem
            area_catalog = pathlib.Path(area_file).parent.stem

            yield AuditStartMsg(stnum=student['stnum'], area_code=area_code, area_catalog=area_catalog)

            try:
                yield from audit(
                    spec=area_spec,
                    exceptions=exceptions,
                    transcript=transcript,
                    constants=constants,
                    area_pointers=area_pointers,
                    print_all=args.print_all,
                    other_areas=area_pointers,
                    estimate_only=args.estimate_only,
                )

            except Exception as ex:
                yield ExceptionMsg(ex=ex, tb=traceback.format_exc())
