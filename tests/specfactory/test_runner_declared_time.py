"""A87: scripts/run_godot_tests.sh lets a test declare the time it needs.

Declaration (pinned): a line `# test-timeout: N` anywhere in the test script (N a positive integer,
the same unit as --quit-after, i.e. frames). Rules pinned here:
  - no declaration: the runner passes --quit-after 300 (default unchanged);
  - declaration below 300 is clamped up to 300 (a test cannot shorten the default);
  - declaration above 300 is passed through as --quit-after N;
  - an explicit TIMEOUT_SEC in the environment still wins over any declaration.
The real godot is replaced by a fake on PATH that records --quit-after and prints the summary line
only if the budget covers the script's `# fake-needs: N` line (a planted slow test).
Spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md::A87.
"""
import os
import re
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RUNNER = REPO / "scripts" / "run_godot_tests.sh"

FAKE_GODOT = r'''#!/usr/bin/env bash
script=""; quit=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --script) script="$2"; shift 2;;
    --quit-after) quit="$2"; shift 2;;
    *) shift;;
  esac
done
echo "FAKE quit-after=$quit"
path="${script#res://}"
needs=$(grep -oP '^# fake-needs: \K[0-9]+' "$path" || echo 0)
if [[ "$quit" -ge "$needs" ]]; then echo "PASS: 1  FAIL: 0"; fi
exit 0
'''


def _run(tmp_path, body, env_extra=None):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    fake = bindir / "godot"
    fake.write_text(FAKE_GODOT)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    script = tmp_path / "t.gd"
    script.write_text(body)
    env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")
    env.pop("TIMEOUT_SEC", None)
    env.update(env_extra or {})
    proc = subprocess.run(["bash", str(RUNNER), str(script)], capture_output=True, text=True, env=env)
    m = re.search(r"FAKE quit-after=(\d+)", proc.stdout)
    return proc, int(m.group(1)) if m else None


def test_declared_time_is_used(tmp_path):
    proc, quit_after = _run(tmp_path, "# test-timeout: 5000\nextends SceneTree\n")
    assert quit_after == 5000, proc.stdout


def test_undeclared_gets_default_300(tmp_path):
    proc, quit_after = _run(tmp_path, "extends SceneTree\n")
    assert quit_after == 300, proc.stdout


def test_declared_below_default_is_clamped_to_300(tmp_path):
    proc, quit_after = _run(tmp_path, "# test-timeout: 10\nextends SceneTree\n")
    assert quit_after == 300, proc.stdout


def test_env_timeout_wins_over_declaration(tmp_path):
    proc, quit_after = _run(tmp_path, "# test-timeout: 5000\n", {"TIMEOUT_SEC": "777"})
    assert quit_after == 777, proc.stdout


def test_positive_control_slow_script_aborts_at_default_and_passes_when_declared(tmp_path):
    slow = "# fake-needs: 2000\nextends SceneTree\n"
    proc, _ = _run(tmp_path, slow)
    assert "no summary: aborted" in proc.stdout and proc.returncode != 0
    proc, _ = _run(tmp_path, "# test-timeout: 2000\n" + slow)
    assert "no summary" not in proc.stdout and proc.returncode == 0, proc.stdout


def test_slow_replay_tests_declare_their_time():
    # Red until the A87 unit adds the declaration lines (test-defect, ledger row; the tests
    # branch does not edit these files).
    for name in ("test_chronicle_scene_open.gd", "test_time_jump_replay.gd"):
        text = (REPO / "tests" / name).read_text()
        m = re.search(r"^# test-timeout: (\d+)\s*$", text, re.M)
        assert m, f"{name} has no `# test-timeout: N` line"
        assert int(m.group(1)) > 300, name
