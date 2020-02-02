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


# build up these categories once, incrementally
WAIVED_ONLY = frozenset({ResultStatus.Waived})
WAIVED_AND_DONE = WAIVED_ONLY | {ResultStatus.Done}
WAIVED_DONE_CURRENT = WAIVED_AND_DONE | {ResultStatus.PendingCurrent}
WAIVED_DONE_CURRENT_PENDING = WAIVED_DONE_CURRENT | {ResultStatus.PendingRegistered}
WAIVED_DONE_CURRENT_PENDING_INCOMPLETE = WAIVED_DONE_CURRENT_PENDING | {ResultStatus.NeedsMoreItems}
