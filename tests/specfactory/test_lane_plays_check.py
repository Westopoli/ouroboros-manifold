# spec: piece HARNESS-laneplays -- merge_gate_support.lane_plays_check and the merge_gate.sh stage "lane_plays".
"""Tests for the lane-play gate. RED today because merge_gate_support.lane_plays_check does not exist yet.

Interface the builder implements (merge_gate_support.py):
  lane_plays_check(candidate, base_ref, *, python_exe, timeout, known_red_path=DEFAULT_LANE_KNOWN_RED,
                   lane_map_path=DEFAULT_LANE_MAP, plays_dir="tests/qa/desktop/plays", changed=None, setup=True)
                   -> (ok, detail)
  `changed` (list of paths) overrides the git diff; when None it is changed_files(candidate, base_ref).
Lane map TOML: [lanes] table, lane letter -> list of path globs (** matches any depth). Each play file under
plays_dir/<L>/*.py of a touched lane runs alone: `python -m pytest -q -p no:cacheprovider -rA --color=no <file>` with cwd
candidate and the env inherited (the stage sets xvfb/OM_QA_RENDERER=vulkan/1920x1080 itself, tests do not). Known-red
file: lines 'node_id  # reason', node id = '<plays_dir>/<L>/<file>.py::<test_name>'. Detail text: 'skipped' when no lane is
touched; 'red outside known-red list: <id>'; 'stale known-red, remove from list: <id>'."""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402

PY = sys.executable
PLAYS = "tests/qa/desktop/plays"
STUB = "import os\n\ndef test_play_x():\n    assert os.environ.get('PLAY_X') != 'red'\n"


def _setup(tmp_path, known=""):
    (tmp_path / PLAYS / "C").mkdir(parents=True)
    (tmp_path / PLAYS / "C" / "play_x.py").write_text(STUB)
    (tmp_path / "lanes.toml").write_text('[lanes]\nC = ["scenes/ground3d/**"]\nZ = ["zzz/**"]\n')
    (tmp_path / "known.txt").write_text(known)


def _run(tmp_path, changed, monkeypatch, state="green"):
    monkeypatch.setenv("PLAY_X", state)
    return mgs.lane_plays_check(tmp_path, "HEAD", python_exe=PY, timeout=120, known_red_path=tmp_path / "known.txt",
                                lane_map_path=tmp_path / "lanes.toml", plays_dir=PLAYS, changed=changed, setup=False)


NODE = f"{PLAYS}/C/play_x.py::test_play_x"


def test_no_lane_touched_is_skipped(tmp_path, monkeypatch):
    """HARNESS-laneplays: red because lane_plays_check does not exist yet."""
    _setup(tmp_path)
    ok, detail = _run(tmp_path, ["csrc/foo.c"], monkeypatch, "red")
    assert ok and "skipped" in detail


def test_lane_touched_all_green_ok(tmp_path, monkeypatch):
    """HARNESS-laneplays: red because lane_plays_check does not exist yet."""
    _setup(tmp_path)
    ok, detail = _run(tmp_path, ["scenes/ground3d/a.gd"], monkeypatch, "green")
    assert ok, detail
    assert "skipped" not in detail


def test_unlisted_red_rejects_naming_it(tmp_path, monkeypatch):
    """HARNESS-laneplays: red because lane_plays_check does not exist yet."""
    _setup(tmp_path)
    ok, detail = _run(tmp_path, ["scenes/ground3d/a.gd"], monkeypatch, "red")
    assert not ok and "test_play_x" in detail and "red outside known-red list" in detail


def test_listed_red_is_ok(tmp_path, monkeypatch):
    """HARNESS-laneplays: red because lane_plays_check does not exist yet."""
    _setup(tmp_path, known=f"{NODE}  # TD-X pending\n")
    ok, detail = _run(tmp_path, ["scenes/ground3d/a.gd"], monkeypatch, "red")
    assert ok, detail


def test_listed_red_that_passes_rejects_as_stale(tmp_path, monkeypatch):
    """HARNESS-laneplays: red because lane_plays_check does not exist yet."""
    _setup(tmp_path, known=f"# header\n{NODE}  # TD-X pending\n")
    ok, detail = _run(tmp_path, ["scenes/ground3d/a.gd"], monkeypatch, "green")
    assert not ok and "stale" in detail and "remove from list" in detail and "test_play_x" in detail


def test_diff_to_lane_mapping_reads_the_toml(tmp_path, monkeypatch):
    """HARNESS-laneplays: red because lane_plays_check does not exist yet. Lane Z has no plays dir and is mapped only in
    the TOML: touching zzz/ must not run lane C; rewriting the TOML to map zzz/** to C must make the red play run."""
    _setup(tmp_path)
    ok, detail = _run(tmp_path, ["zzz/a.txt"], monkeypatch, "red")
    assert ok and "skipped" in detail
    (tmp_path / "lanes.toml").write_text('[lanes]\nC = ["zzz/**"]\n')
    ok, detail = _run(tmp_path, ["zzz/a.txt"], monkeypatch, "red")
    assert not ok and "test_play_x" in detail


def test_positive_control_planted_red_is_caught(tmp_path, monkeypatch):
    """HARNESS-laneplays positive control: red because lane_plays_check does not exist yet. A second planted failing
    play next to a listed one is caught by name."""
    _setup(tmp_path, known=f"{NODE}  # TD-X pending\n")
    (tmp_path / PLAYS / "C" / "play_y.py").write_text("def test_play_planted():\n    assert False\n")
    ok, detail = _run(tmp_path, ["scenes/ground3d/a.gd"], monkeypatch, "red")
    assert not ok and "test_play_planted" in detail


def test_shipped_files_exist_and_parse():
    """HARNESS-laneplays: red until the builder reads them; the shipped lane map and known-red list are well formed."""
    import tomllib
    lanes = tomllib.loads((REPO / "scripts/specfactory/lane_plays.toml").read_text())["lanes"]
    assert lanes["C"] == ["scenes/ground3d/**"] and lanes["F"] == ["autoload/net/**", "scenes/lobby/**"]
    assert hasattr(mgs, "lane_plays_check")
    for line in (REPO / "scripts/specfactory/lane_plays_known_red.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            node = line.split("#")[0].strip()
            assert (REPO / node.split("::")[0]).exists(), node
            assert "  # " in line or " # " in line, line
