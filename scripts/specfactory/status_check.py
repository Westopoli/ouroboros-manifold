#!/usr/bin/env python3
"""status_check.py: the trailer schema of docs/method/story_loop.md, checked from git.

Four checks, one `STATUS <check> DRIFT <id>` line per failure (the merge gate's status
stage matches `^STATUS [a-z_]* DRIFT`), exit 1 when any, else `STATUS OK <n> landings
checked` and exit 0:
  land_trailer          a first-parent `Land <id>` commit after the anchor lacks any of
                        Story, Tests, Play, Played, Gate, Flag
  tested_without_land   a story marked Tested in stories.md or harness.md has no
                        `Land <id>` commit on main
  seen_without_verdict  a `Seen <id>` commit has no Verdict: trailer
  seen_without_commit   a story marked Seen has no `Seen <id>` commit
Every check looks only at history after the anchor: a story counts only if a commit after
it changed its row (`git log <anchor>..<ref> -S<id> -- stories.md harness.md` non-empty);
stories marked by the old method before it are history. Anchor: the sha in the first
sweep commit's `Base:` trailer on first-parent main, else the commit that added
docs/method/README.md. Arguments: --repo, --base (the ref read; default origin/main, else
HEAD). See also: scripts/method/status.sh, merge_gate.sh.
"""
import argparse
import re
import subprocess
import sys

ROW_FILES = ("docs/bible/stories.md", "docs/method/harness.md")
TRAILERS = ["Story", "Tests", "Play", "Played", "Gate", "Flag"]


def git(repo, *a):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def anchor(repo, ref):
    for h in git(repo, "log", "--first-parent", "--reverse", "--grep=^Sweep ", "--format=%H", ref).split():
        m = re.search(r"^Base:\s*(\S+)", git(repo, "log", "-1", "--format=%B", h), re.M)
        if m:
            return m.group(1)
    added = git(repo, "log", "--diff-filter=A", "--format=%H", ref, "--", "docs/method/README.md").split()
    return added[-1] if added else None


def story_rows(repo, ref):
    """(id, status) for each table row of stories.md and harness.md."""
    for f in ROW_FILES:
        for line in git(repo, "show", f"{ref}:{f}").splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 4 and re.fullmatch(r"[A-Z]-\d+", c[0]):
                yield c[0], c[-2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default=None)
    a = ap.parse_args()
    repo = a.repo
    ref = a.base or ("origin/main" if git(repo, "rev-parse", "-q", "--verify", "origin/main") else "HEAD")
    base = anchor(repo, ref)
    span = f"{base}..{ref}" if base else ref
    subjects = {}
    for h, s in (l.split(" ", 1) for l in git(repo, "log", "--first-parent", "--format=%H %s", ref).splitlines()):
        subjects[h] = s
    drift, n = [], 0
    in_span = set(git(repo, "log", "--first-parent", "--format=%H", span).split())
    for h in in_span:
        m = re.match(r"Land (\S+)", subjects[h])
        if not m:
            continue
        n += 1
        body = git(repo, "log", "-1", "--format=%B", h)
        miss = [t for t in TRAILERS if not re.search(rf"^{t}:\s*\S", body, re.M)]
        if miss:
            drift.append(f"STATUS land_trailer DRIFT {m.group(1)}")
    landed = {m.group(1) for s in subjects.values() if (m := re.match(r"Land (\S+)", s))}
    seen = {m.group(1) for s in subjects.values() if (m := re.match(r"Seen (\S+)", s))}
    for h in in_span:
        m = re.match(r"Seen (\S+)", subjects[h])
        if m and not re.search(r"^Verdict:\s*\S", git(repo, "log", "-1", "--format=%B", h), re.M):
            drift.append(f"STATUS seen_without_verdict DRIFT {m.group(1)}")
    for sid, st in story_rows(repo, ref):
        if st not in ("Tested",) and not st.startswith("Seen"):
            continue
        if base and not git(repo, "log", "--format=%H", span, f"-S{sid}", "--", *ROW_FILES).strip():
            continue  # row unchanged since the anchor: old-method history
        if st == "Tested" and sid not in landed:
            drift.append(f"STATUS tested_without_land DRIFT {sid}")
        if st.startswith("Seen") and sid not in seen:
            drift.append(f"STATUS seen_without_commit DRIFT {sid}")
    for d in drift:
        print(d)
    if drift:
        sys.exit(1)
    print(f"STATUS OK {n} landings checked")


if __name__ == "__main__":
    main()
