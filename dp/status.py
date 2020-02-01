import enum


@enum.unique
class ResultStatus(enum.Enum):
    Empty = "empty"
    PendingApproval = "pending-approval"
    NeedsMoreItems = "needs-more-items"
    PendingRegistered = "pending-registered"
    PendingCurrent = "pending-current"
    Done = "done"
    Waived = "waived"


PassingStatuses = (ResultStatus.Waived, ResultStatus.Done, ResultStatus.PendingCurrent, ResultStatus.PendingRegistered)
PassingStatusValues = tuple(v.value for v in PassingStatuses)
