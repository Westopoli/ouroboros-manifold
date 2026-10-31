#!/usr/bin/env python3
"""H-004: file `FINDING <words>` lines of a nightly log as `H-` rows in a harness file.

Usage: file_findings.py <log> <harness.md> [--push]
Without --push no git is touched. With --push: branch s/H-nightly-<date> from origin/main,
append, commit, push. Never edits a story or a test.
See also: scripts/method/nightly_play.sh, docs/stories/H-004.md.
"""
import re
import subprocess
import sys
from pathlib import Path


def main(argv):
    push = "--push" in argv
    args = [a for a in argv if a != "--push"]
    log, doc = Path(args[0]), Path(args[1])
    date = log.stem
    words = [l[8:].strip() for l in log.read_text().splitlines() if l.startswith("FINDING ")]
    if not words:
        return 0
    branch = f"s/H-nightly-{date}"
    if push:
        # H-033: repo root via git, not doc.parent (docs/method/ made `add` miss the path)
        repo = Path(subprocess.run(["git", "-C", str(doc.resolve().parent), "rev-parse", "--show-toplevel"],
                                   check=True, capture_output=True, text=True).stdout.strip()).resolve()
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True)
        git("fetch", "-q", "origin")
        git("checkout", "-q", "-B", branch, "origin/main")
    text = doc.read_text()
    ids = [int(m) for m in re.findall(r"^\| H-(\d+) \|", text, re.M)]
    nxt = max(ids, default=0) + 1
    rows = "".join(f'| H-{nxt + i:03d} | "{w}" | Spec\'d | `nightly/{date}.log` |\n'
                   for i, w in enumerate(words))
    if not text.endswith("\n"):
        text += "\n"
    # rows go right after the last existing H- row
    lines = text.splitlines(keepends=True)
    last = max(i for i, l in enumerate(lines) if l.startswith("| H-"))
    lines[last + 1:last + 1] = [rows]
    doc.write_text("".join(lines))
    if push:
        git("add", str(doc.resolve().relative_to(repo)))
        git("commit", "-q", "-m", f"H-nightly {date}: {len(words)} finding(s) filed for triage")
        git("push", "-q", "origin", f"HEAD:{branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
