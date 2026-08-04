"""
Shared utilities for script execution with agent-safe error handling.

This module provides centralized subprocess wrappers and common utilities
for scripts to ensure agent-safe execution patterns.
"""

import subprocess
import sys
from pathlib import Path


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """
    Agent-safe subprocess wrapper with clear error messages.

    Args:
        cmd: Command and arguments to execute
        cwd: Working directory for command execution
        check: If True, raise exception on non-zero exit code

    Returns:
        CompletedProcess with stdout, stderr, and returncode

    Raises:
        SystemExit: On command failure (with clear error message)
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed: {' '.join(cmd)}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: Command not found: {cmd[0]}")
        print(f"Please install '{cmd[0]}' before running this script")
        sys.exit(1)


def check_command_exists(cmd: str) -> bool:
    """
    Check if a command exists in PATH.

    Args:
        cmd: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def ensure_directory_exists(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary (idempotent).

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def load_json_config(config_path: Path) -> dict:
    """
    Load JSON configuration file with error handling.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        Parsed configuration as dictionary

    Raises:
        SystemExit: On file read or parse error
    """
    import json

    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in configuration file: {config_path}")
        print(f"Parse error: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: Cannot read configuration file: {config_path}")
        print(f"IO error: {e}")
        sys.exit(1)
