import enum


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
class GradeCode(enum.Enum):
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
