# spec: Architect ruling 2026-10-21 (piece HARNESS-gate-base-after-lock): merge_gate.sh stage 0 "base".
"""Proves the new stage 0 `base` of scripts/specfactory/merge_gate.sh, run right after argument parsing:

  * "git fetch origin in the candidate, main_sha = origin/main; if main_sha is not an ancestor of HEAD, print
    `GATE base REJECT candidate lacks origin/main <main_sha>; merge origin/main inside the lock and rerun`
    and exit non-zero before make; otherwise print `GATE base OK <main_sha>`"  (tests 1, 3, 4)
  * "MERGE_GATE_STOP_AFTER=base: exit 0 right after the base line"  (tests 2, 3)
  * "--revert: the base stage runs before the --revert exit, so a revert of a stale candidate is rejected" (test 4)

Fixture (no build, no lock, no real stage): a bare origin and a candidate clone under
~/Projects/om-push/tmp-gatebase/<unique per run>/wt-cand, both holding one file and no Makefile. Run against a
script WITHOUT the base stage, `make` fails at once ("GATE make HARNESS ... COMPILE ERROR", exit 3), so the first
GATE line is make's and the script ends by itself within a second: no kill is needed (subprocess timeout 120 s
is only a backstop). Since HARNESS-gate-tiers the first GATE line is `GATE tier <name>` and `base` is the first stage
line after it (TD-HARNESS-gate-tiers-1); `_run` checks the tier line and returns the stage lines after it.
The script's own lock is not involved: merge_gate.sh holds none; the clerk's flock does.
"""
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "merge_gate.sh"
FIXTURE_ROOT = Path.home() / "Projects" / "om-push" / "tmp-gatebase"
RUN_TIMEOUT_S = 120
SHA_RE = r"[0-9a-f]{40}"


def _git(cwd, *args):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        "-c", "protocol.file.allow=always", *args],
                       cwd=str(cwd), capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _commit(repo, name):
    (Path(repo) / name).write_text(name + "\n")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", name)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def fx():
    """origin (bare, main at M1), pusher clone, candidate clone `wt-cand` on branch feat = M1 + one commit."""
    root = FIXTURE_ROOT / uuid.uuid4().hex[:12]
    root.mkdir(parents=True)
    try:
        origin, pusher, cand = root / "origin.git", root / "pusher", root / "wt-cand"
        _git(root, "init", "-q", "--bare", "-b", "main", str(origin))
        _git(root, "clone", "-q", str(origin), str(pusher))
        _git(pusher, "checkout", "-q", "-B", "main")
        m1 = _commit(pusher, "m1.txt")
        _git(pusher, "push", "-q", "origin", "main")
        _git(root, "clone", "-q", str(origin), str(cand))
        _git(cand, "checkout", "-q", "-b", "feat")
        _commit(cand, "feat.txt")

        def push_new_main():
            return (_commit(pusher, "m2.txt"), _git(pusher, "push", "-q", "origin", "main"))[0]
        yield {"cand": cand, "m1": m1, "push_new_main": push_new_main}
    finally:
        shutil.rmtree(root)


def _run(cand, *flags, stop_after=None):
    env = {"PATH": os.environ["PATH"], "HOME": str(Path.home())}
    if stop_after:
        env["MERGE_GATE_STOP_AFTER"] = stop_after
    r = subprocess.run(["bash", str(SCRIPT), *flags, str(cand), "origin/main", "HARNESS-gate-base-after-lock"],
                       capture_output=True, text=True, env=env, timeout=RUN_TIMEOUT_S)
    gate = [ln for ln in r.stdout.splitlines() if ln.startswith("GATE ") and not ln.startswith("GATE row ")]
    # TD-HARNESS-gate-tiers-1: `GATE tier <name>` is printed once and first (layered gate spec section 4, HARNESS-gate-tiers),
    # so `base` is the first stage line after it. The tier line is checked here and dropped from the list the tests read.
    assert gate and gate[0].startswith("GATE tier "), f"first stage line was {gate[:1]!r}, wanted `GATE tier <name>`"
    return r.returncode, gate[1:], r.stdout + r.stderr


def test_1_candidate_behind_new_main_is_rejected_before_make(fx):
    """Proves: a candidate lacking origin/main (pushed while the clerk waited) prints the REJECT line naming the
    later sha and exits non-zero before make."""
    later = fx["push_new_main"]()
    rc, gate, out = _run(fx["cand"])
    assert gate and gate[0].startswith(f"GATE base REJECT candidate lacks origin/main {later}"), \
        f"first stage line was {gate[:1]!r}, wanted a base REJECT naming {later}"
    assert rc != 0, out
    assert not any(ln.startswith("GATE make") for ln in gate), "make ran after a base REJECT"


def test_2_candidate_merged_with_new_main_passes_and_stops(fx):
    """Proves: a candidate merged with the later main prints `GATE base OK <later sha>`; with
    MERGE_GATE_STOP_AFTER=base the script exits 0 right after that line."""
    later = fx["push_new_main"]()
    _git(fx["cand"], "fetch", "-q", "origin")
    _git(fx["cand"], "merge", "-q", "--no-edit", "origin/main")
    rc, gate, out = _run(fx["cand"], stop_after="base")
    assert gate == [g for g in gate if g.startswith("GATE base")] and gate, out
    assert re.match(rf"GATE base OK {later}\b", gate[0]), f"first stage line was {gate[0]!r}, wanted base OK {later}"
    assert rc == 0, out
    assert len(gate) == 1, "stage ran past the base line"


def test_3_idle_control_main_unchanged(fx):
    """Proves: with main unmoved during the wait, the OK line carries the same sha as origin/main (the control
    that test 1 is red for the stale-main reason, not for a broken fixture)."""
    rc, gate, out = _run(fx["cand"], stop_after="base")
    assert gate and re.match(rf"GATE base OK {fx['m1']}\b", gate[0]), f"first stage line was {gate[:1]!r}"
    assert rc == 0 and len(gate) == 1, out


def test_4_revert_of_a_stale_candidate_is_rejected(fx):
    """Proves: the base stage runs before the --revert exit, so --revert on a stale candidate is also a
    base REJECT, non-zero, with no make."""
    later = fx["push_new_main"]()
    rc, gate, out = _run(fx["cand"], "--revert")
    assert gate and gate[0].startswith(f"GATE base REJECT candidate lacks origin/main {later}"), \
        f"first stage line was {gate[:1]!r}, wanted a base REJECT naming {later}"
    assert rc != 0 and not any(ln.startswith("GATE make") for ln in gate), out
