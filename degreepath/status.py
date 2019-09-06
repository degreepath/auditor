import enum


@enum.unique
class ResultStatus(enum.Enum):
    Pass = "pass"
    InProgress = "in-progress"
    Problem = "problem"
    Pending = "pending"
