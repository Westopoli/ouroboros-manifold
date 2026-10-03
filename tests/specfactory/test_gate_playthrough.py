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
