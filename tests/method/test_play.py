"""H-001 play main: tests for scripts/play.sh (docs/stories/H-001.md)."""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLAY = ROOT / "scripts" / "play.sh"
SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"


def run_play(args, env_drop=(), timeout=1200, tmpdir=None):
    env = {k: v for k, v in os.environ.items() if k not in env_drop}
    if tmpdir:
        env["TMPDIR"] = str(tmpdir)  # play.sh's own scratch clone lands in the test's scratch dir
    return subprocess.run(["bash", str(PLAY), *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=timeout)


def scratch_clone(base):
    """A shared scratch copy of ROOT at HEAD; play.sh may import and build in it freely."""
    tree = Path(base) / "tree"
    subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(tree)], check=True)
    return tree


def porcelain(tree):
    return subprocess.run(["git", "-C", str(tree), "status", "--porcelain"],
                          capture_output=True, text=True, check=True).stdout


def test_control_build_pipe_exits_zero():
    """Positive control (H-001 Tests): "`scripts/build_pipe_linux.sh` on the test
    tree exits 0 (green today)."; a red below means play.sh is missing, not the build."""
    scratch = Path(tempfile.mkdtemp(prefix="h001-control-"))
    try:
        tree = scratch_clone(scratch)  # a clone: the build never dirties the suite's own tree
        r = subprocess.run(["bash", str(tree / "scripts" / "build_pipe_linux.sh")],
                           cwd=tree, capture_output=True, text=True, timeout=1200)
        assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
        assert (tree / "dist" / "linux" / "ouroboros_pipe").exists()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_broken_project_godot_exits_nonzero_with_godot_error():
    """H-001 Tests: "A scratch worktree with a broken `project.godot` makes the
    script exit non-zero with the Godot error line in its output.\""""
    scratch = Path(tempfile.mkdtemp(prefix="h001-broken-"))
    try:
        tree = scratch / "tree"
        subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(tree)], check=True)
        subprocess.run(["git", "-C", str(tree), "checkout", "-q", "HEAD"], check=True)
        (tree / "project.godot").write_text("config_version=5\n[application\nthis is not valid\n")
        subprocess.run(["git", "-C", str(tree), "-c", "user.name=t", "-c", "user.email=t@t",
                        "commit", "-qam", "broken"], check=True)  # play.sh plays the tree's HEAD
        r = run_play(["--tree", str(tree)], env_drop=("DISPLAY",), tmpdir=scratch)
        out = r.stdout + r.stderr
        assert r.returncode != 0, "play.sh exited 0 on a broken project.godot"
        assert re.search(r"ERROR|project\.godot", out), out[-800:]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_story_dry_run_launch_line_carries_scene_path():
    """H-001 Tests: "With `--story H-001` and a story file whose `Scene:` line names
    `res://scenes/privacy_modal/privacy_modal.tscn`, the launch line printed by
    `--dry-run` carries that path.\""""
    r = run_play(["--tree", str(ROOT), "--story", "H-001", "--dry-run"])
    assert r.returncode == 0, r.stdout + r.stderr
    launch = [l for l in r.stdout.splitlines() if "godot" in l and "--path" in l and "--import" not in l]
    assert launch, r.stdout
    assert SCENE in launch[0], launch[0]


def test_check_dry_run_uses_scratch_xdg_data_home():
    """H-001 round 4, DEC-play-check-scratch-userdir-2026-10-30: under `--check` Godot
    runs with `XDG_DATA_HOME=<scratch>/xdg`, so a stored `user://privacy_accepted` cannot
    skip the boot scene. The dry run prints the env on the tree, build or launch line (a
    dry run makes no scratch clone, so the path is checked to sit under the tree or TMPDIR).
    Positive control: the same dry run without `--check` prints no `XDG_DATA_HOME=`."""
    tmp = Path.home() / "Projects" / "om-push" / "tmp" / "h001-r4"
    tmp.mkdir(parents=True, exist_ok=True)
    chk = run_play(["--tree", str(ROOT), "--story", "H-001", "--check", "--dry-run"], tmpdir=tmp)
    assert chk.returncode == 0, chk.stdout + chk.stderr
    m = re.search(r"XDG_DATA_HOME=(\S+)", chk.stdout)
    assert m, "no XDG_DATA_HOME= in --check dry run:\n" + chk.stdout
    path = m.group(1)
    assert path.endswith("/xdg"), path
    assert path.startswith((str(tmp), str(ROOT))), path
    plain = run_play(["--tree", str(ROOT), "--story", "H-001", "--dry-run"], tmpdir=tmp)
    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert "XDG_DATA_HOME=" not in plain.stdout, plain.stdout


def test_no_display_exits_nonzero_with_message():
    """H-001 Behaviour 5: "`$DISPLAY` must be set; exit non-zero with `no display`
    otherwise"."""
    scratch = Path(tempfile.mkdtemp(prefix="h001-nodisplay-"))
    try:
        r = run_play(["--tree", str(scratch_clone(scratch))], env_drop=("DISPLAY", "WAYLAND_DISPLAY"), tmpdir=scratch)
        assert r.returncode != 0, "play.sh exited 0 with no DISPLAY"
        assert "no display" in (r.stdout + r.stderr), r.stdout + r.stderr
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _stub_home(base):
    """A fake HOME whose .local/bin/godot.real is a stub that writes a marker when run.
    play.sh hardcodes GODOT="$HOME/.local/bin/godot.real", so HOME is the only way to substitute it."""
    home = Path(base) / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    marker = Path(base) / "godot-ran"
    stub = home / ".local" / "bin" / "godot.real"
    stub.write_text('#!/bin/sh\necho "$@" >> "%s"\nexit 0\n' % marker)
    stub.chmod(0o755)
    return home, marker, stub


def test_no_display_runs_no_godot():
    """H-001 Behaviour 5 and DEC-play-display-check-first-2026-10-30: with no DISPLAY,
    play.sh exits non-zero with `no display` AND runs no Godot (the check comes before
    the build and import steps). Godot is a marker-writing stub under a fake HOME."""
    base = Path(tempfile.mkdtemp(prefix="h001-nogodot-"))
    try:
        home, marker, stub = _stub_home(base)
        tree = scratch_clone(base)
        (base / "tmp").mkdir()
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
        env.update(HOME=str(home), TMPDIR=str(base / "tmp"))
        r = subprocess.run(["bash", str(PLAY), "--tree", str(tree)], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=1200)
        assert r.returncode != 0 and "no display" in r.stdout + r.stderr, r.stdout + r.stderr
        assert not marker.exists(), "Godot ran before the display check: " + marker.read_text()
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_stub_godot_control_is_wired():
    """Positive control for test_no_display_runs_no_godot: the fake HOME is what play.sh
    launches (the --dry-run launch line carries the stub path) and the stub writes the marker."""
    base = Path(tempfile.mkdtemp(prefix="h001-stubctl-"))
    try:
        home, marker, stub = _stub_home(base)
        env = {**os.environ, "HOME": str(home), "DISPLAY": os.environ.get("DISPLAY", ":99")}
        r = subprocess.run(["bash", str(PLAY), "--tree", str(ROOT), "--dry-run"], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0 and f"launch: {stub} --path" in r.stdout, r.stdout + r.stderr
        subprocess.run([str(stub), "--headless"], check=True)
        assert marker.exists(), "stub did not write its marker"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_tree_stays_clean_after_any_tree_run():
    """H-001 Tests: "After any `--tree` run, `git -C <tree> status --porcelain` is
    empty (the tree is never dirtied)." Covers the dry runs on the tree itself and a
    full run (stopped at the no-display check, after build and import) on a clone."""
    before = porcelain(ROOT)
    for args in (["--tree", str(ROOT), "--dry-run"],
                 ["--tree", str(ROOT), "--story", "H-001", "--dry-run"]):
        r = run_play(args)
        assert r.returncode == 0, r.stdout + r.stderr
        assert porcelain(ROOT) == before, porcelain(ROOT)
    scratch = Path(tempfile.mkdtemp(prefix="h001-clean-"))
    try:
        tree = scratch_clone(scratch)
        run_play(["--tree", str(tree)], env_drop=("DISPLAY", "WAYLAND_DISPLAY"), tmpdir=scratch)
        assert porcelain(tree) == "", porcelain(tree)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="display-bound; run by the clerk")
def test_real_display_window_under_60s():
    """Display-bound (run by the clerk, not pre_gate). H-001 Tests: "On the real
    display: `scripts/play.sh --tree <worktree>` prints `PLAY window` under 60 s.\""""
    scratch = Path(tempfile.mkdtemp(prefix="h001-window-"))
    try:
        tree = scratch_clone(scratch)
        r = run_play(["--tree", str(tree)], timeout=1800, tmpdir=scratch)
        m = re.search(r"PLAY window (\d+)s", r.stdout)
        assert r.returncode == 0 and m, r.stdout + r.stderr
        assert int(m.group(1)) < 60
    finally:
        subprocess.run(["pkill", "-f", "godot.real --path .*h001-window-"], check=False)
        shutil.rmtree(scratch, ignore_errors=True)


def test_scratch_removed_on_exit_unless_keep():
    """H-001 Tests: "After a `--tree` run without `--keep`, the scratch directory it
    printed no longer exists; with `--keep` it does (positive control)." Stops at the
    no-display check, after build and import."""
    base = Path(tempfile.mkdtemp(prefix="h001-scratchexit-"))
    drop = ("DISPLAY", "WAYLAND_DISPLAY")
    kept = None
    try:
        tree = scratch_clone(base)
        (base / "t1").mkdir()
        r = run_play(["--tree", str(tree)], env_drop=drop, tmpdir=base / "t1")
        m = re.search(r"^scratch: (.+)$", r.stdout, re.M)
        assert m, r.stdout + r.stderr
        assert not Path(m.group(1)).exists(), "scratch left behind without --keep: " + m.group(1)
        (base / "t2").mkdir()
        r = run_play(["--tree", str(tree), "--keep"], env_drop=drop, tmpdir=base / "t2")
        m = re.search(r"^scratch: (.+)$", r.stdout, re.M)
        assert m, r.stdout + r.stderr
        kept = Path(m.group(1))
        assert kept.exists(), "--keep did not keep the scratch directory"
    finally:
        if kept:
            shutil.rmtree(kept, ignore_errors=True)
        shutil.rmtree(base, ignore_errors=True)
