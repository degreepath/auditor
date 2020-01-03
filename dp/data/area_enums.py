import enum


@enum.unique
class AreaStatus(enum.Enum):
    WhatIf = "what-if"
    Declared = "declared"
    Certified = "certified"
    Awarded = "awarded"


@enum.unique
class AreaType(enum.Enum):
    Degree = "degree"
    Major = "major"
    Concentration = "concentration"
    Emphasis = "emphasis"
