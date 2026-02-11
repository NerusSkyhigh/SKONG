"""
Tests for SKONG CLI
"""

import pytest
from skong.cli import main
from skong import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_main_no_args(capsys, monkeypatch):
    """Test CLI with no arguments shows help."""
    monkeypatch.setattr("sys.argv", ["skong"])
    result = main()
    
    # Check exit code is 0 and help was printed
    captured = capsys.readouterr()
    assert "SKONG" in captured.out
    assert result == 0


def test_main_with_command(capsys, monkeypatch):
    """Test CLI with a command argument."""
    monkeypatch.setattr("sys.argv", ["skong", "test-command"])
    result = main()
    
    captured = capsys.readouterr()
    assert "Executing command: test-command" in captured.out
    assert result == 0
