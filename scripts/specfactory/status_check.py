#!/usr/bin/env python3
"""status_check.py: the trailer schema of docs/method/story_loop.md, checked from git.

Four trailer checks plus the sweep-due line (check_sweep_due), one `STATUS <check> DRIFT <id>` line per failure (the merge gate's status
stage matches `^STATUS [a-z_]* DRIFT`), exit 1 when any, else `STATUS OK <n> landings
checked` and exit 0:
  land_trailer          a first-parent `Land <id>` commit after the anchor lacks any of
                        Story, Tests, Play, Played, Gate, Flag
  tested_without_land   a story marked Tested in stories.md or harness.md has no
                        `Land <id>` commit on main
  seen_without_verdict  a `Seen <id>` commit has no Verdict: trailer
  seen_without_commit   a story marked Seen has no `Seen <id>` commit
Every check looks only at history after the anchor: a story counts only if a commit after
it changed its own row (a diff of stories.md and harness.md from the anchor to ref has an added or
removed line starting `| <id> |`; a mention of the id inside another row does not count);
stories marked by the old method before it are history. Anchor: the sha in the first
sweep commit's `Base:` trailer on first-parent main, else the commit that added
docs/method/README.md. Arguments: --repo, --base (the ref read; default origin/main, else
HEAD). See also: scripts/method/status.sh, merge_gate.sh.
"""
import argparse
import datetime
import re
import subprocess
import sys

SWEEPS = "docs/northstar/plans/push/sweeps.md"
# DRAFT-slow-tier-batch, DRAFT-slow-tier-hours, DRAFT-slow-tier-drift-mult (tests/specfactory/test_gate_tiers.py:75).
BATCH, HOURS, MULT = 3, 2, 2
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


def check_sweep_due(repo, ref):
    """The `STATUS sweep` line: a sweep of main is due after more than DRAFT-slow-tier-batch landings, or when
    the anchor is older than DRAFT-slow-tier-hours with a landing since; DRIFT at DRAFT-slow-tier-drift-mult
    times either. Anchor: the last PASS row of sweeps.md, else the BASE row; a REJECT row is never the anchor.
    Restores the check H-002 dropped (docs/method/gate.md:21, clerk.md:15 step 8). Returns (line, is_drift)."""
    anchor_row = None
    for line in git(repo, "show", f"{ref}:{SWEEPS}").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 3 and c[2].split(" ")[0] in ("PASS", "BASE"):
            if anchor_row is None or c[2].startswith("PASS") or not anchor_row[2].startswith("PASS"):
                anchor_row = c
    if anchor_row is None:
        return "STATUS sweep OK no PASS or BASE row in sweeps.md", False
    when, sha = anchor_row[0], anchor_row[1]
    n = sum(1 for h in git(repo, "log", "--first-parent", "--format=%s", f"{sha}..{ref}").splitlines()
            if h.startswith("Land "))
    if n == 0:
        return f"STATUS sweep OK 0 landings since {sha[:12]}", False
    try:
        t = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc)
        age = (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600
    except ValueError:
        age = 0.0
    why = f"{n} landings and {age:.1f} h since {sha[:12]}"
    if n > BATCH * MULT or age > HOURS * MULT:
        return f"STATUS sweep DRIFT {why}", True
    if n > BATCH or age > HOURS:
        return f"STATUS sweep WARN {why}", False
    return f"STATUS sweep OK {why}", False


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
    changed = git(repo, "diff", "--unified=0", base, ref, "--", *ROW_FILES).splitlines() if base else []
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
        if base and not any(l[:1] in "+-" and l[1:].startswith(f"| {sid} |") for l in changed):
            continue  # row unchanged since the anchor: old-method history
        if st == "Tested" and sid not in landed:
            drift.append(f"STATUS tested_without_land DRIFT {sid}")
        if st.startswith("Seen") and sid not in seen:
            drift.append(f"STATUS seen_without_commit DRIFT {sid}")
    line, sweep_drift = check_sweep_due(repo, ref)
    if sweep_drift:
        drift.append(line)
    for d in drift:
        print(d)
    if not sweep_drift:
        print(line)
    if drift:
        sys.exit(1)
    print(f"STATUS OK {n} landings checked")


if __name__ == "__main__":
    main()
