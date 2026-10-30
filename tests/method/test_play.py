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


def run_play(args, env_drop=(), timeout=1200):
    env = {k: v for k, v in os.environ.items() if k not in env_drop}
    return subprocess.run(["bash", str(PLAY), *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=timeout)


def test_control_build_pipe_exits_zero():
    """Positive control (H-001 Tests): "`scripts/build_pipe_linux.sh` on the test
    tree exits 0 (green today)."; a red below means play.sh is missing, not the build."""
    r = subprocess.run(["bash", str(ROOT / "scripts" / "build_pipe_linux.sh")],
                       cwd=ROOT, capture_output=True, text=True, timeout=1200)
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
    assert (ROOT / "dist" / "linux" / "ouroboros_pipe").exists()


def test_broken_project_godot_exits_nonzero_with_godot_error():
    """H-001 Tests: "A scratch worktree with a broken `project.godot` makes the
    script exit non-zero with the Godot error line in its output.\""""
    scratch = Path(tempfile.mkdtemp(prefix="h001-broken-"))
    try:
        tree = scratch / "tree"
        subprocess.run(["git", "clone", "-q", "--shared", str(ROOT), str(tree)], check=True)
        subprocess.run(["git", "-C", str(tree), "checkout", "-q", "HEAD"], check=True)
        (tree / "project.godot").write_text("config_version=5\n[application\nthis is not valid\n")
        r = run_play(["--tree", str(tree)], env_drop=("DISPLAY",))
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


def test_no_display_exits_nonzero_with_message():
    """H-001 Behaviour 5: "`$DISPLAY` must be set; exit non-zero with `no display`
    otherwise"."""
    r = run_play(["--tree", str(ROOT)], env_drop=("DISPLAY", "WAYLAND_DISPLAY"))
    assert r.returncode != 0, "play.sh exited 0 with no DISPLAY"
    assert "no display" in (r.stdout + r.stderr), r.stdout + r.stderr


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="display-bound; run by the clerk")
def test_real_display_window_under_60s():
    """Display-bound (run by the clerk, not pre_gate). H-001 Tests: "On the real
    display: `scripts/play.sh --tree <worktree>` prints `PLAY window` under 60 s.\""""
    r = run_play(["--tree", str(ROOT)], timeout=1800)
    m = re.search(r"PLAY window (\d+)s", r.stdout)
    assert r.returncode == 0 and m, r.stdout + r.stderr
    assert int(m.group(1)) < 60
    subprocess.run(["pkill", "-f", f"godot.real --path {ROOT}"], check=False)
