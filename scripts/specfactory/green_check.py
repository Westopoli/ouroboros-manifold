#!/usr/bin/env python3
"""Proves a reference implementation flips a card's acceptance from failing
to passing. Mirrors red_check.py's shape but checks the opposite side of a
card's acceptance test: a reference is only proof of anything if the card's
stub fails acceptance before the reference is applied, and passes after.

Usage:
    scripts/specfactory/green_check.py <card_file> <reference_file>

Exit code 0 if applying the reference file makes every acceptance command
pass.
Exit code 1 if acceptance still fails after the reference file is applied.
Exit code 2 if acceptance already passes before the reference file is
applied -- the detector can never fail, so this reference proves nothing.
Exit code 3 for usage/parse errors: missing card, missing reference file,
no acceptance commands, or a project path that is not a directory.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _unquote(val: str) -> str:
    if len(val) >= 2 and val[0] == val[-1] == '"':
        return val[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return val


def parse_card(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing frontmatter")
    card: dict = {"acceptance": []}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"\s*-\s+", line) and key:
            val = _unquote(re.sub(r"^\s*-\s+", "", line).strip())
            card.setdefault(key, []).append(val)
        elif ":" in line:
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v == "":
                key = k
                card.setdefault(k, [])
            else:
                card[k] = _unquote(v)
                key = None
    return card


def target_file(card: dict) -> str:
    snippet = card.get("snippet_file")
    if isinstance(snippet, str) and snippet:
        return snippet
    allowed = card.get("allowed_files", "")
    if isinstance(allowed, list):
        allowed = allowed[0] if allowed else ""
    return allowed.split(",")[0].strip() if allowed else ""


def run_acceptance(commands: list[str], cwd: Path) -> tuple[bool, str]:
    parts = []
    for cmd in commands:
        proc = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True)
        parts.append(f"$ {cmd}\n{proc.stdout}{proc.stderr}")
        if proc.returncode != 0:
            return False, "\n".join(parts)
    return True, "\n".join(parts)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: green_check.py <card_file> <reference_file>", file=sys.stderr)
        return 3

    card_path, reference_path = Path(argv[0]), Path(argv[1])
    if not card_path.is_file():
        print(f"card not found: {card_path}", file=sys.stderr)
        return 3
    if not reference_path.is_file():
        print(f"reference not found: {reference_path}", file=sys.stderr)
        return 3

    try:
        card = parse_card(card_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    acceptance = card.get("acceptance") or []
    if not acceptance:
        print(f"{card_path}: no acceptance commands", file=sys.stderr)
        return 3

    project = Path(card.get("project", "")).expanduser()
    if not project.is_dir():
        print(f"project is not a directory: {project}", file=sys.stderr)
        return 3

    rel_target = target_file(card)
    if not rel_target:
        print(f"{card_path}: no snippet_file or allowed_files", file=sys.stderr)
        return 3

    scratch_dir = Path(tempfile.mkdtemp(prefix="green_check_"))
    worktree = scratch_dir / "wt"
    try:
        add = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
            cwd=str(project), capture_output=True, text=True,
        )
        if add.returncode != 0:
            print(add.stdout + add.stderr, file=sys.stderr)
            return 3

        passed, output = run_acceptance(acceptance, worktree)
        if passed:
            print(output)
            print("GREEN CHECK REFUSED: acceptance already passes before the reference is applied")
            return 2

        (worktree / rel_target).write_text(reference_path.read_text())

        passed, output = run_acceptance(acceptance, worktree)
        print(output)
        if passed:
            print("GREEN CHECK OK: reference makes acceptance pass")
            return 0
        print("GREEN CHECK FAILED: reference does not make acceptance pass", file=sys.stderr)
        return 1
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=str(project), capture_output=True, text=True,
        )
        shutil.rmtree(scratch_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
