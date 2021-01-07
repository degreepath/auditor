import enum


@enum.unique
class DataType(enum.Enum):
    Course = 'course'
    Area = 'area'
    MusicPerformance = "music-performance"
    Recital = "recital"
