# spec: docs/stories/H-067.md (part 3, the import outputs are committed once)
"""H-067 part 3: after `scripts/setup_editor.sh` a fresh clone has a clean `git status`.

Story H-067, Tests line proved here: "`tests/qa/test_editor_import_clean.py` (new): a fresh clone after `scripts/setup_editor.sh` has an empty
`git status --short`; skipped with a visible reason when `godot.real` is missing; never run during a sweep; positive control: a tree with one script's
`.uid` removed reports it."
Story Change part 3: "Commit the import outputs once ... After this commit a first open or `--import` leaves `git status` clean."

How "never run during a sweep" is done (the repo has two idioms, both used here): the import test carries `@pytest.mark.slow` (as
tests/method/test_token_report.py does) and is skipped unless `OM_EDITOR_IMPORT=1` is set (as tests/csim/scale/conftest.py gates `OM_SCALE=1`). No
sweep or gate stage sets it, so the test is always collected, always skipped with a visible reason there, and run on purpose with
`OM_EDITOR_IMPORT=1 ~/Projects/agora/.venv/bin/python -m pytest tests/qa/test_editor_import_clean.py` (it builds the pipe, copies the godotsteam cache
and imports the whole project: minutes). The positive control is cheap (one local git clone, no Godot, no build) and runs everywhere, acceptance
stage included, so a red import test is never a broken `git status` reader.

The fresh clone is `git clone` of this checkout's committed HEAD, so the branch under test must have committed `scripts/setup_editor.sh` and the
import outputs of part 3. Red today for the missing-feature reason: `scripts/setup_editor.sh` does not exist, and the tree has 222 dirty entries after
an import (47 modified `.import`, 175 untracked `.uid`; story "Why" item 2; dumped on this worktree 2026-11-02 after `godot.real --headless --import`).
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SETUP = "scripts/setup_editor.sh"
GODOT = shutil.which("godot.real") or ("/home/westopoli/.local/bin/godot.real" if os.access("/home/westopoli/.local/bin/godot.real", os.X_OK) else None)
OPT_IN = os.environ.get("OM_EDITOR_IMPORT") == "1"


def git(args, cwd, timeout=300):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=timeout)


def status_short(tree):
    r = git(["status", "--short"], tree)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


def fresh_clone():
    d = Path(tempfile.mkdtemp(prefix="h067-clone-"))
    r = git(["clone", "-q", str(ROOT), str(d / "tree")], d)
    assert r.returncode == 0, r.stderr
    return d, d / "tree"


# ---------------------------------------------------------------- positive control (green today, runs everywhere)

def test_control_a_removed_uid_is_reported():
    """Positive control (H-067 Tests: "a tree with one script's `.uid` removed reports it"): on a scratch clone, which starts clean, deleting one
    tracked script `.uid` sidecar makes `git status --short` report exactly that path. Proves the clean-status reader sees a missing sidecar, so an
    empty status in the import test means the tree is clean, not that the reader is blind."""
    d, tree = fresh_clone()
    try:
        assert status_short(tree) == [], "a fresh clone must start clean"
        uids = git(["ls-files", "*.gd.uid"], tree).stdout.split()
        assert uids, "no tracked .gd.uid in the clone; the control needs one"
        (tree / uids[0]).unlink()
        assert status_short(tree) == [" D " + uids[0]], status_short(tree)
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- the story (opt-in, never in a sweep)

@pytest.mark.slow
@pytest.mark.skipif(GODOT is None, reason="godot.real is missing (not on PATH, not at ~/.local/bin/godot.real): the editor import cannot run")
@pytest.mark.skipif(not OPT_IN, reason="never run during a sweep: set OM_EDITOR_IMPORT=1 to run the fresh-clone import (minutes: builds the pipe, imports the project)")
def test_fresh_clone_after_setup_editor_has_empty_git_status():
    """H-067 Tests: "a fresh clone after `scripts/setup_editor.sh` has an empty `git status --short`". Change part 3: "After this commit a first
    open or `--import` leaves `git status` clean." Clones the committed HEAD, runs the clone's `scripts/setup_editor.sh` (real build, real cache or
    fetch, real `godot.real --headless --import`), asserts it ended `EDITOR READY`, then asserts `git status --short` is empty. The pipe, dist/,
    .godot/ and the godotsteam libraries are git-ignored, so only the import's own sidecars and `.import` rewrites can show."""
    d, tree = fresh_clone()
    try:
        script = tree / SETUP
        assert script.is_file(), f"H-067: {SETUP} is not in the committed HEAD of {ROOT}"
        r = subprocess.run(["bash", str(script)], cwd=str(tree), capture_output=True, text=True, timeout=1800)
        lines = (r.stdout + r.stderr).splitlines()
        assert f"EDITOR READY {tree}" in lines, "H-067: setup did not end EDITOR READY: %s" % lines[-5:]
        dirty = status_short(tree)
        assert dirty == [], "H-067: %d dirty entries after setup_editor.sh on a fresh clone; first: %s" % (len(dirty), dirty[:5])
    finally:
        shutil.rmtree(d, ignore_errors=True)
