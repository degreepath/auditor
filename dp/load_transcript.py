from typing import List, Dict, Any, Iterator

from .data.course import load_course, CourseInstance
from .data.course_enums import GradeOption, GradeCode, TranscriptCode


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
