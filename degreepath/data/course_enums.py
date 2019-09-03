import enum
from typing import Any


@enum.unique
class GradeOption(enum.Enum):
    Audit = "audit"
    Grade = "grade"
    NoGrade = "no grade"
    PN = "p/n"
    SU = "s/u"


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
    Adjustment = "AD"
    AP = "AP"
    Carleton = "CA"
    ContinuingEducation = "CE"
    GeReq = "GE"
    Interim = "IN"
    InterimExchange = "IE"
    OffCampusCourse = "OC"
    OffCampusProgram = "OP"
    Other = "OT"
    ParaCollege = "PC"
    PSEO = "PS"
    Semester = "SE"
    Summer = "SM"
    Transfer = "TR"


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
    Aplus = "A+"
    Aminus = "A-"
    B = "B"
    Bplus = "B+"
    Bminus = "B-"
    C = "C"
    Cplus = "C+"
    Cminus = "C-"
    D = "D"
    Dplus = "D+"
    Dminus = "D-"
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
