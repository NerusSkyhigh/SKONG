"""
Entry point for running SKONG as a module with python -m skong
"""

import sys
from skong.cli import main

if __name__ == "__main__":
    sys.exit(main())
