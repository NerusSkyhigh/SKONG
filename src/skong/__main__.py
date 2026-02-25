"""CLI entry point for skong – run with ``python -m skong``."""

import argparse
import json
import sys

from .core import init, list_status, log, read_status, set_status, submit_jobs
from .status import Status


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skong",
        description="Track the history of a computational project.",
    )
    sub = parser.add_subparsers(dest="command")

    # --- init ---
    init_p = sub.add_parser("init", help="Initialize .skong tracking in a directory.")
    init_p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to initialize (default: current directory).",
    )

    # --- set-status ---
    ss_p = sub.add_parser("set-status", help="Set the project status.")
    ss_p.add_argument(
        "status",
        choices=[s.value for s in Status],
        help="Status to set.",
    )
    ss_p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )

    # --- read-status ---
    rs_p = sub.add_parser("read-status", help="Read the current project status.")
    rs_p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )

    # --- log ---
    log_p = sub.add_parser("log", help="Append a JSON entry to history.jsonl.")
    log_p.add_argument(
        "entry",
        help='JSON string to log, e.g. \'{"step": 1, "energy": -42.5}\'.',
    )
    log_p.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )

    # --- sub ---
    sub_p = sub.add_parser(
        "sub",
        help="Submit INITIALIZED jobs via qsub.",
    )
    sub_p.add_argument(
        "limit",
        nargs="?",
        type=int,
        default=10,
        help="Max number of jobs to submit (default: 10).",
    )
    sub_p.add_argument(
        "--job",
        default="job.pbs",
        help="PBS script filename (default: job.pbs).",
    )
    sub_p.add_argument(
        "--path",
        default=".",
        help="Parent directory to scan (default: current directory).",
    )

    # --- continue ---
    cont_p = sub.add_parser(
        "continue",
        help="Re-submit PARTIAL (incomplete) jobs via qsub.",
    )
    cont_p.add_argument(
        "limit",
        nargs="?",
        type=int,
        default=10,
        help="Max number of jobs to submit (default: 10).",
    )
    cont_p.add_argument(
        "--job",
        default="job.pbs",
        help="PBS script filename (default: job.pbs).",
    )
    cont_p.add_argument(
        "--path",
        default=".",
        help="Parent directory to scan (default: current directory).",
    )

    # --- ls ---
    ls_p = sub.add_parser(
        "ls",
        help="List sub-directories matching a given status.",
    )
    ls_p.add_argument(
        "status",
        choices=[s.value for s in Status],
        help="Status to filter by.",
    )
    ls_p.add_argument(
        "--path",
        default=".",
        help="Parent directory to scan (default: current directory).",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        skong_dir = init(args.path)
        print(f"Initialized .skong in {skong_dir.resolve()}")

    elif args.command == "set-status":
        status = Status(args.status)
        set_status(status, path=args.path)
        print(f"Status set to {status.value}")

    elif args.command == "read-status":
        status = read_status(args.path)
        if status is None:
            print("No status found.")
            sys.exit(1)
        print(status.value)

    elif args.command == "log":
        try:
            entry = json.loads(args.entry)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON: {exc}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(entry, dict):
            print("Entry must be a JSON object (dict).", file=sys.stderr)
            sys.exit(1)
        log(entry, path=args.path)
        print("Entry logged.")

    elif args.command == "sub":
        results = submit_jobs(
            Status.INITIALIZED,
            limit=args.limit,
            job_script=args.job,
            path=args.path,
        )
        print(f"\n{len(results)} job(s) submitted.")

    elif args.command == "continue":
        results = submit_jobs(
            Status.PARTIAL,
            limit=args.limit,
            job_script=args.job,
            path=args.path,
        )
        print(f"\n{len(results)} job(s) re-submitted.")

    elif args.command == "ls":
        status = Status(args.status)
        dirs = list_status(status, path=args.path)
        if not dirs:
            print(f"No sub-directories with status {status.value}.")
        else:
            for d in dirs:
                print(d.name)


if __name__ == "__main__":
    main()
