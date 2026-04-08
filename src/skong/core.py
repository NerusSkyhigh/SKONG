"""Core logic for skong project tracking."""

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Union, cast

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


def valid_dir(path: Union[str, Path, None] = None) -> bool:
    """Check if the given path is a valid skong project.

    Returns True if the path contains a .skong directory, False otherwise.
    Defaults to checking the current working directory if no path is provided.
    """
    path = Path(path) if path else Path.cwd()
    return _skong_dir(path).is_dir()


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
DEFAULT_PBS_JOB_SCRIPT = "job.pbs"
DEFAULT_SLURM_JOB_SCRIPT = "job.slurm"

Scheduler = Literal["pbs", "slurm"]


def detect_scheduler(preferred: str = "auto") -> Scheduler:
    """Detect which scheduler should be used for job submissions.

    Detection precedence (first match wins):
    1) explicit ``preferred`` value (``pbs`` or ``slurm``)
    2) ``SKONG_SCHEDULER`` environment variable
    3) scheduler-specific allocation environment variables
    4) command availability in ``PATH`` (``sbatch`` / ``qsub``)

    When both scheduler binaries are available and no other hint exists,
    Slurm is preferred by default.
    """
    preferred = preferred.strip().lower()
    if preferred in {"pbs", "slurm"}:
        return cast(Scheduler, preferred)
    if preferred != "auto":
        raise ValueError(
            "Invalid scheduler value. Use one of: auto, pbs, slurm."
        )

    env_choice = os.getenv("SKONG_SCHEDULER", "").strip().lower()
    if env_choice in {"pbs", "slurm"}:
        return cast(Scheduler, env_choice)

    if os.getenv("SLURM_JOB_ID") or os.getenv("SLURM_CLUSTER_NAME"):
        return "slurm"
    if os.getenv("PBS_JOBID") or os.getenv("PBS_O_HOST"):
        return "pbs"

    has_sbatch = shutil.which("sbatch") is not None
    has_qsub = shutil.which("qsub") is not None

    if has_sbatch and not has_qsub:
        return "slurm"
    if has_qsub and not has_sbatch:
        return "pbs"
    if has_sbatch and has_qsub:
        return "slurm"

    raise RuntimeError(
        "Could not detect a scheduler automatically. "
        "No 'sbatch' or 'qsub' command was found in PATH."
    )


def _default_job_script_for(scheduler: Scheduler) -> str:
    """Return the default job filename for a given scheduler."""
    if scheduler == "slurm":
        return DEFAULT_SLURM_JOB_SCRIPT
    return DEFAULT_PBS_JOB_SCRIPT


def _submit_command(scheduler: Scheduler, restart: int, script_name: str) -> list[str]:
    """Build the submit command for the selected scheduler."""
    if scheduler == "slurm":
        return ["sbatch", f"--export=ALL,RESTART={restart}", script_name]
    return ["qsub", "-v", f"RESTART={restart}", script_name]


def _extract_job_id(scheduler: Scheduler, stdout: str) -> str:
    """Extract a numeric-ish job id from scheduler output."""
    raw = stdout.strip()
    if not raw:
        return raw
    if scheduler == "pbs":
        # qsub usually returns something like "12345.pbs-server".
        return raw.split(".")[0]

    # sbatch usually returns "Submitted batch job 12345".
    match = re.search(r"Submitted\s+batch\s+job\s+(\S+)", raw)
    return match.group(1) if match else raw


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


def describe_statuses(
    *,
    path: Union[str, Path, None] = None,
) -> dict[Status, list[Path]]:
    """Return sub-directories grouped by status.

    The mapping preserves ``Status`` declaration order, so callers can render a
    stable report section for each status.
    """
    path = Path(path) if path else Path.cwd()
    return {status: list_status(status, path=path) for status in Status}


def submit_jobs(
    target_status: Status,
    *,
    limit: int = 10,
    job_script: Optional[str] = None,
    scheduler: str = "auto",
    path: Union[str, Path, None] = None,
) -> list[dict]:
    """Submit jobs for sub-directories matching *target_status*.

    Parameters
    ----------
    target_status:
        Only directories whose current status equals this value will be
        submitted.  Typically ``Status.INITIALIZED`` (new) or
        ``Status.PARTIAL`` (needs more time).
    limit:
        Maximum number of jobs to submit.
    job_script:
        Filename of the scheduler script inside each sub-directory.
        If omitted, uses ``job.pbs`` for PBS and ``job.slurm`` for Slurm.
    scheduler:
        Scheduler selection strategy: ``auto`` (default), ``pbs`` or ``slurm``.
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
    chosen_scheduler = detect_scheduler(scheduler)
    effective_job_script = job_script or _default_job_script_for(chosen_scheduler)

    candidates = list_status(target_status, path=path)

    for child in candidates:
        if limit <= 0:
            print(f"{_RED}[INFO] Job limit reached. Stopping submission.{_RESET}")
            break

        job_file = child / effective_job_script
        if not job_file.exists():
            print(
                f"{_YELLOW}[WARNING] No {effective_job_script} in {child.name}. "
                f"Skipping.{_RESET}"
            )
            continue

        # Submit from inside the job directory and pass only the script name.
        try:
            result = subprocess.run(
                _submit_command(chosen_scheduler, restart, job_file.name),
                capture_output=True,
                text=True,
                check=True,
                cwd=str(child),
            )
            job_id = _extract_job_id(chosen_scheduler, result.stdout)
        except FileNotFoundError:
            print(
                f"{_RED}[ERROR] Submit command not found for scheduler "
                f"'{chosen_scheduler}'.{_RESET}"
            )
            break
        except subprocess.CalledProcessError as exc:
            print(
                f"{_RED}[ERROR] Submission failed for {child.name}: "
                f"{(exc.stderr or exc.stdout).strip()}{_RESET}"
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
            f"\t{_GREEN}[INFO] {effective_job_script} submitted from {child.name} "
            f"with ID: {job_id}{_RESET}"
        )
        submitted.append(
            {"dir": str(child), "job_id": job_id, "timestamp": timestamp}
        )
        limit -= 1

    return submitted
