"""skong – lightweight tracking for computational projects."""

from .core import (
    describe_statuses,
    detect_scheduler,
    init,
    list_status,
    log,
    read_status,
    set_status,
    submit_jobs,
)
from .status import Status

__all__ = [
    "Status",
    "describe_statuses",
    "detect_scheduler",
    "init",
    "list_status",
    "log",
    "read_status",
    "set_status",
    "submit_jobs",
]
