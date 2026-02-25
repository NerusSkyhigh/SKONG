"""Status enum for skong project tracking."""

from enum import Enum


class Status(Enum):
    """Available statuses for a tracked computational project."""

    INITIALIZED = "INITIALIZED"
    FINISHED = "FINISHED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
