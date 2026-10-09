# spec: CLAUDE.md "merge gate": every landing is checked against a scripted playthrough.
"""Positive control for the merge gate's playthrough stage: it must fail when the
flow breaks. The suite under test is a planted tmp test file (target=), so no game
code is edited; the real desktop suite is exercised by running the stage itself."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402

PY = sys.executable


def _run(tmp_path, body, known=""):
    (tmp_path / "test_flow_planted.py").write_text(body)
    kr = tmp_path / "known_red.txt"
    kr.write_text(known)
    return mgs.playthrough_check(tmp_path, "HEAD", python_exe=PY, timeout=120, known_red_path=kr,
                                 target="test_flow_planted.py", force=True, setup=False)


def test_broken_flow_fails_stage(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_planted_break():\n    assert False\n")
    assert not ok and "test_s_planted_break" in detail


def test_green_flow_passes_stage(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_planted_ok():\n    assert True\n")
    assert ok, detail


def test_known_red_tolerated_and_now_green_reported(tmp_path):
    ok, _ = _run(tmp_path, "def test_s_known():\n    assert False\n", known="test_s_known\n")
    assert ok
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert True\n", known="test_s_known\n")
    assert ok and "now green, remove from list: test_s_known" in detail


def test_empty_suite_fails_stage(tmp_path):
    ok, _ = _run(tmp_path, "")
    assert not ok


def test_trigger_rules():
    t = mgs.playthrough_trigger
    assert t(["csrc/x.c"]) and t(["autoload/a.gd"]) and t(["project.godot"]) and t(["tests/qa/desktop/t.py"])
    assert not t(["scenes/mockups/a.tscn"]) and not t(["docs/x.md"])
    assert t(["scenes/mockups/a.tscn", "scenes/hud.tscn"])


def test_known_red_file_is_empty():
    lines = [l.strip() for l in mgs.DEFAULT_KNOWN_RED.read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    assert lines == []


def test_missing_suite_fails_stage(tmp_path):
    ok, detail = mgs.playthrough_check(tmp_path, "HEAD", python_exe=PY, timeout=60,
                                       target="tests/qa/desktop", force=True, setup=False)
    assert not ok and "suite missing" in detail


def test_build_failure_rejects_and_suite_not_run(tmp_path, monkeypatch):
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "make").write_text("#!/bin/sh\necho planted build break >&2\nexit 1\n")
    (stub / "make").chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub}:/usr/bin:/bin")
    cand = tmp_path / "cand"
    cand.mkdir()
    (cand / "test_flow_planted.py").write_text("def test_s_ran():\n    open('RAN', 'w')\n")
    ok, detail = mgs.playthrough_check(cand, "HEAD", python_exe=PY, timeout=60,
                                       target="test_flow_planted.py", force=True, setup=True)
    assert not ok and detail.startswith("playthrough setup failed: build") and "planted build break" in detail
    assert not (cand / "RAN").exists()


# --- HARNESS-playsplit: the playthrough stage ignores tests/qa/desktop/plays/**; lane_plays owns the plays ---

def _desktop_tree(tmp_path, spine_body, play_body, extra_body=None):
    d = tmp_path / "tests/qa/desktop"
    (d / "plays/A").mkdir(parents=True)
    (d / "test_flow_spine.py").write_text(spine_body)
    (d / "plays/A/test_S_001.py").write_text(play_body)
    if extra_body is not None:
        (d / "test_other_desktop.py").write_text(extra_body)
    kr = tmp_path / "known_red.txt"
    kr.write_text("")
    return kr


def _check(tmp_path, kr):
    return mgs.playthrough_check(tmp_path, "HEAD", python_exe=PY, timeout=120, known_red_path=kr,
                                 target="tests/qa/desktop", force=True, setup=False)


def test_playthrough_command_ignores_plays_dir(tmp_path, monkeypatch):
    """HARNESS-playsplit. Red now: playthrough_check builds `pytest ... tests/qa/desktop` with no
    --ignore, so the flow spine and the play are both collected."""
    kr = _desktop_tree(tmp_path, "def test_flow_spine_ok():\n    pass\n", "def test_S_001_play():\n    pass\n")
    seen = []
    real = mgs.subprocess.run

    def spy(cmd, *a, **k):
        if isinstance(cmd, list) and "pytest" in cmd:
            seen.append(list(cmd))
        return real(cmd, *a, **k)
    monkeypatch.setattr(mgs.subprocess, "run", spy)
    ok, detail = _check(tmp_path, kr)
    assert ok, detail
    assert len(seen) == 1
    cmd = seen[0]
    assert "tests/qa/desktop" in cmd
    ign = [a for a in cmd if a.startswith("--ignore") and a.rstrip("/").endswith("tests/qa/desktop/plays")]
    assert ign, f"no --ignore of tests/qa/desktop/plays in {cmd}"
    assert "1 passed" in detail, detail  # the spine only, not the play


def test_red_play_does_not_reject_playthrough(tmp_path):
    """HARNESS-playsplit. Red now: a red play under plays/ is collected by the playthrough stage
    and rejects it (ok=False), though only the lane_plays list may carry it."""
    kr = _desktop_tree(tmp_path, "def test_flow_spine_ok():\n    pass\n",
                       "def test_S_001_play():\n    assert False\n")
    ok, detail = _check(tmp_path, kr)
    assert ok, detail
    assert "test_S_001_play" not in detail


def test_red_desktop_test_outside_plays_still_rejects(tmp_path):
    """HARNESS-playsplit positive control: a red desktop test outside plays/ still rejects.
    Green now and must stay green after the split."""
    kr = _desktop_tree(tmp_path, "def test_flow_spine_ok():\n    pass\n",
                       "def test_S_001_play():\n    pass\n",
                       extra_body="def test_other_broken():\n    assert False\n")
    ok, detail = _check(tmp_path, kr)
    assert not ok and "test_other_broken" in detail
