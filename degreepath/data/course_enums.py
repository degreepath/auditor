import enum


@enum.unique
class CourseStatus(enum.Enum):
    Ok = enum.auto()
    InProgress = enum.auto()
    Incomplete = enum.auto()
    Repeat = enum.auto()


@enum.unique
class GradeType(enum.Enum):
    AU = "Audit"
    GR = "Graded"
    NG = "No Grade"
    PN = "P/N"
    SU = "S/U"


@enum.unique
class SubType(enum.Enum):
    Discussion = "D"
    E = "E"
    FLAC = "F"
    Lab = "L"
    Research = "R"
    Seminar = "S"
    Topic = "T"
    Normal = ""


@enum.unique
class Grade(enum.Enum):
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
    _AU = "AU"
    _I = "I"
    _IP = "IP"
    _N = "N"
    _NG = "NG"
    _P = "P"
    _S = "S"
    _U = "U"
    _UA = "UA"
    _W = "W"
    _WF = "WF"
    _WP = "WP"


@enum.unique
class TranscriptCode(enum.Enum):
    TakenAtCarleton = "#"
    RepeatedLater = "R"
    Incomplete = "*"
    NoCode = None
