"""Core logic for skong project tracking."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .status import Status

SKONG_DIR = ".skong"
HISTORY_FILE = "history.jsonl"


def _skong_dir(path: Union[str, Path]) -> Path:
    """Return the .skong directory for the given project path."""
    return Path(path) / SKONG_DIR


def _require_initialized(path: Union[str, Path]) -> Path:
    """Return the .skong directory, raising if not initialized."""
    skong = _skong_dir(path)
    if not skong.is_dir():
        raise FileNotFoundError(
            f"No .skong directory found in {Path(path).resolve()}. "
            "Run 'skong init' first."
        )
    return skong


def init(path: Union[str, Path, None] = None) -> Path:
    """Initialize a .skong directory in *path* (defaults to cwd).

    Creates the directory and sets the status to INITIALIZED.
    Returns the path to the created .skong directory.
    """
    path = Path(path) if path else Path.cwd()
    skong = _skong_dir(path)
    skong.mkdir(parents=True, exist_ok=True)
    set_status(Status.INITIALIZED, path=path)
    return skong


def set_status(status: Status, *, path: Union[str, Path, None] = None) -> None:
    """Set the project status.

    Removes any existing status file and creates a new one named
    after the chosen enum member (e.g. ``.skong/RUNNING``).
    """
    path = Path(path) if path else Path.cwd()
    skong = _require_initialized(path) if status != Status.INITIALIZED else _skong_dir(path)

    # Remove every existing status file
    for s in Status:
        status_file = skong / s.value
        if status_file.exists():
            status_file.unlink()

    # Create the new status file
    (skong / status.value).touch()


def read_status(path: Union[str, Path, None] = None) -> Optional[Status]:
    """Read the current project status.

    Returns the ``Status`` enum member whose file is present inside
    ``.skong/``, or ``None`` if no status file is found.
    """
    path = Path(path) if path else Path.cwd()
    skong = _require_initialized(path)

    for s in Status:
        if (skong / s.value).exists():
            return s
    return None


def log(entry: dict, *, path: Union[str, Path, None] = None) -> None:
    """Append *entry* as a JSON line to ``.skong/history.jsonl``."""
    path = Path(path) if path else Path.cwd()
    skong = _require_initialized(path)

    history = skong / HISTORY_FILE
    with history.open("a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------

_GREEN = "\033[0;32m"
_YELLOW = "\033[0;33m"
_RED = "\033[0;31m"
_RESET = "\033[0m"

DEFAULT_JOB_SCRIPT = "job.pbs"


def list_status(
    status: Status,
    *,
    path: Union[str, Path, None] = None,
) -> list[Path]:
    """Return every immediate sub-directory of *path* whose status matches *status*."""
    path = Path(path) if path else Path.cwd()
    matches: list[Path] = []
    for child in sorted(path.iterdir()):
        if not child.is_dir():
            continue
        skong = child / SKONG_DIR
        if not skong.is_dir():
            continue
        if (skong / status.value).exists():
            matches.append(child)
    return matches


def submit_jobs(
    target_status: Status,
    *,
    limit: int = 10,
    job_script: str = DEFAULT_JOB_SCRIPT,
    path: Union[str, Path, None] = None,
) -> list[dict]:
    """Submit PBS jobs for sub-directories matching *target_status*.

    Parameters
    ----------
    target_status:
        Only directories whose current status equals this value will be
        submitted.  Typically ``Status.INITIALIZED`` (new) or
        ``Status.PARTIAL`` (needs more time).
    limit:
        Maximum number of jobs to submit.
    job_script:
        Filename of the PBS script inside each sub-directory.
    path:
        Parent directory to scan (defaults to cwd).

    Returns
    -------
    list[dict]
        One dict per submitted job with keys ``dir``, ``job_id``, ``timestamp``.
    """
    path = Path(path) if path else Path.cwd()
    restart = 1 if target_status == Status.PARTIAL else 0
    submitted: list[dict] = []

    candidates = list_status(target_status, path=path)

    for child in candidates:
        if limit <= 0:
            print(f"{_RED}[INFO] Job limit reached. Stopping submission.{_RESET}")
            break

        job_file = child / job_script
        if not job_file.exists():
            print(
                f"{_YELLOW}[WARNING] No {job_script} in {child.name}. "
                f"Skipping.{_RESET}"
            )
            continue

        # Submit via qsub from inside the job directory.
        # Pass the script name (not a prefixed path) to mirror the shell workflow.
        try:
            result = subprocess.run(
                ["qsub", "-v", f"RESTART={restart}", job_file.name],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(child),
            )
            # qsub typically returns something like "12345.pbs-server"
            raw_id = result.stdout.strip()
            job_id = raw_id.split(".")[0] if raw_id else raw_id
        except FileNotFoundError:
            print(
                f"{_RED}[ERROR] 'qsub' not found – are you on a cluster "
                f"with PBS installed?{_RESET}"
            )
            break
        except subprocess.CalledProcessError as exc:
            print(
                f"{_RED}[ERROR] qsub failed for {child.name}: "
                f"{exc.stderr.strip()}{_RESET}"
            )
            continue

        # Update status → SUBMITTED and write metadata into the status file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        skong_dir = child / SKONG_DIR

        # Remove old status
        (skong_dir / target_status.value).unlink(missing_ok=True)

        # Write SUBMITTED file with metadata
        submitted_file = skong_dir / Status.SUBMITTED.value
        submitted_file.write_text(
            f"Timestamp: {timestamp}\nJob ID: {job_id}\n"
        )

        # Also log the event
        log(
            {
                "event": "submitted",
                "job_id": job_id,
                "timestamp": timestamp,
                "restart": restart,
                "previous_status": target_status.value,
            },
            path=child,
        )

        print(
            f"\t{_GREEN}[INFO] {job_script} submitted from {child.name} "
            f"with ID: {job_id}{_RESET}"
        )
        submitted.append(
            {"dir": str(child), "job_id": job_id, "timestamp": timestamp}
        )
        limit -= 1

    return submitted
