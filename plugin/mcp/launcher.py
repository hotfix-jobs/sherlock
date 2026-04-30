#!/usr/bin/env python3
"""Bootstrap launcher for the Sherlock MCP server.

Modern Python installations (Homebrew, Linux distro Python, macOS system
Python) are PEP 668 "externally managed" and refuse `pip install` outside
a virtual environment. This launcher creates an isolated venv at
~/.claude/data/sherlock/venv/ on first run, installs the MCP server's
dependencies into it, then execs the real server with the venv's Python.

Subsequent runs just check the venv is intact and exec immediately
(adds ~50ms of overhead). First run takes 10 to 30 seconds depending
on download speed.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(os.environ.get(
    "SHERLOCK_DATA_DIR",
    Path.home() / ".claude" / "data" / "sherlock",
))
VENV_DIR = DATA_DIR / "venv"
HERE = Path(__file__).resolve().parent
REQUIREMENTS = HERE / "requirements.txt"
SERVER_SCRIPT = HERE / "server.py"


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_is_ready() -> bool:
    py = venv_python()
    if not py.exists():
        return False
    # Verify the deps are actually importable in the venv
    result = subprocess.run(
        [str(py), "-c", "import mcp.server.fastmcp, zstandard"],
        capture_output=True,
    )
    return result.returncode == 0


def setup_venv() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(
        "Sherlock: first-run setup (creating Python venv and installing "
        "dependencies, takes 10 to 30 seconds)...",
        file=sys.stderr,
        flush=True,
    )
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )
        subprocess.run(
            [
                str(venv_python()), "-m", "pip", "install",
                "--quiet", "--disable-pip-version-check",
                "-r", str(REQUIREMENTS),
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(
            f"Sherlock: setup failed ({e}). Ensure you have python3 with the "
            f"venv module and network access for pip.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Sherlock: setup complete.", file=sys.stderr, flush=True)


def main() -> None:
    if not venv_is_ready():
        setup_venv()
    py = str(venv_python())
    os.execv(py, [py, str(SERVER_SCRIPT)])


if __name__ == "__main__":
    main()
