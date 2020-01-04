import enum
from typing import Any, Dict
from decimal import Decimal


@enum.unique
class GradeOption(enum.Enum):
    Audit = "audit"
    Grade = "grade"
    NoGrade = "no grade"
    PN = "p/n"
    SU = "s/u"


@enum.unique
class TranscriptCode(enum.Enum):
    Empty = ""
    Carleton = "#"
    WasIncomplete = "*"
    IndividualMajor = "+"
    RepeatedLater = "R"
    RepeatInProgress = "Z"


@enum.unique
class SubType(enum.Enum):
    Discussion = "discussion"
    Ensemble = "ensemble"
    Flac = "flac"
    Lab = "lab"
    Research = "research"
    Seminar = "seminar"
    Topic = "topic"
    Normal = ""


@enum.unique
class CourseType(enum.Enum):
    Semester = "SE"
    Interim = "IN"
    Summer = "SM"
    Carleton = "CA"
    InterimExchange = "IE"
    OffCampusCourse = "OC"
    OffCampusProgram = "OP"
    ContinuingEducation = "CE"

    AP = "AP"
    PSEO = "PS"
    Adjustment = "AD"
    GeReq = "GE"
    Other = "OT"
    Transfer = "TR"
    ParaCollege = "PC"


# We want AP courses to be superseded by St. Olaf courses, if possible.
# Because most rules will take the first item out of the transcript that they can,
# we can accomplish this by grouping St. Olaf courses before pre-St. Olaf courses.
CourseTypeSortOrder: Dict[CourseType, int] = {
    CourseType.Semester: 1,
    CourseType.Interim: 1,
    CourseType.Summer: 1,
    CourseType.Carleton: 1,
    CourseType.InterimExchange: 1,
    CourseType.OffCampusCourse: 1,
    CourseType.OffCampusProgram: 1,
    CourseType.ContinuingEducation: 1,

    CourseType.AP: 2,
    CourseType.PSEO: 2,
    CourseType.Adjustment: 2,
    CourseType.GeReq: 2,
    CourseType.Other: 2,
    CourseType.Transfer: 2,
    CourseType.ParaCollege: 2,
}


class OrderedEnum(enum.Enum):
    def __ge__(self, other: Any) -> Any:
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other: Any) -> Any:
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other: Any) -> Any:
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other: Any) -> Any:
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


@enum.unique
class GradeCode(OrderedEnum):
    A = "A"
    A_plus = "A+"
    A_minus = "A-"
    B = "B"
    B_plus = "B+"
    B_minus = "B-"
    C = "C"
    C_plus = "C+"
    C_minus = "C-"
    D = "D"
    D_plus = "D+"
    D_minus = "D-"
    F = "F"

    _BC = "BC"
    _AB = "AB"
    _NG = "NG"
    _IP = "IP"
    _I = "I"
    _P = "P"
    _N = "N"
    _S = "S"
    _U = "U"
    _AU = "AU"
    _UA = "UA"
    _WF = "WF"
    _WP = "WP"
    _W = "W"
    _REG = "DP_REG"


grade_code_to_points: Dict[GradeCode, Decimal] = {
    GradeCode.A_plus: Decimal("4.00"),
    GradeCode.A: Decimal("4.00"),
    GradeCode.A_minus: Decimal("3.70"),
    GradeCode.B_plus: Decimal("3.30"),
    GradeCode.B: Decimal("3.00"),
    GradeCode.B_minus: Decimal("2.70"),
    GradeCode.C_plus: Decimal("2.30"),
    GradeCode.C: Decimal("2.00"),
    GradeCode.C_minus: Decimal("1.70"),
    GradeCode.D_plus: Decimal("1.30"),
    GradeCode.D: Decimal("1.00"),
    GradeCode.D_minus: Decimal("0.70"),
    GradeCode.F: Decimal("0.00"),
}
