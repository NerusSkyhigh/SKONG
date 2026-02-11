"""
Command-line interface for SKONG
"""

import argparse
import sys
from skong import __version__


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        prog="skong",
        description="SKONG - System for Keeping Organized Numerical Goals",
        epilog="A command-line tool to ease the use of UNITN HPC (PBS)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command:
        print(f"Executing command: {args.command}")
        print("SKONG is ready to be extended with PBS/HPC functionality!")
    else:
        parser.print_help()
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
