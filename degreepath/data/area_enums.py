import enum


@enum.unique
class AreaStatus(enum.Enum):
    Certified = "certified"
    Declared = "declared"


@enum.unique
class AreaType(enum.Enum):
    Degree = "degree"
    Major = "major"
    Concentration = "concentration"
    Emphasis = "emphasis"
