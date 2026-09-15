#!/usr/bin/env python3
"""Runs pytest against a set of newly generated test files and confirms every
one fails or errors -- none may pass. A passing new test before any C code
exists for it is a defect (either the test is trivially true, or it is
testing something already implemented elsewhere by accident); this script
turns that into a loud, scriptable check instead of a manual read of pytest
output.

Usage:
    scripts/specfactory/red_check.py tests/csim/test_E03_*.py tests/csim/controls/test_control_e03_*.py

Exit code 0 if every collected test failed or errored (red, as required).
Exit code 1 if pytest could not even collect the files, or if any test passed.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

SUMMARY_RE = re.compile(
    r"=+ (?:(\d+) failed)?,? ?(?:(\d+) passed)?,? ?(?:(\d+) error)?[^=]*=+"
)


def python_bin() -> str:
    venv_python = REPO / ".venv" / "bin" / "python3"
    return str(venv_python) if venv_python.exists() else sys.executable


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: red_check.py <test files/globs...>", file=sys.stderr)
        return 1

    proc = subprocess.run(
        [python_bin(), "-m", "pytest", *argv, "-q", "--no-header"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    print(output)

    passed = len(re.findall(r"^(.+) PASSED", output, re.MULTILINE))
    if passed == 0:
        m = re.search(r"(\d+) passed", output)
        if m:
            passed = int(m.group(1))

    collected_nothing = "no tests ran" in output.lower() or "error in configuration" in output.lower()
    if collected_nothing and "collected 0 items" in output.lower():
        print("RED CHECK FAILED: nothing was collected", file=sys.stderr)
        return 1

    if passed > 0:
        print(f"RED CHECK FAILED: {passed} test(s) passed; every new test must fail or error", file=sys.stderr)
        return 1

    print("RED CHECK OK: every collected test failed or errored")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
