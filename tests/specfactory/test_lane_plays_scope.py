# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md paragraph **HARNESS-lane-plays-scope (text of 2026-10-23 read from
#       ~/Projects/om-push/scratch/drafts-2026-10-22/paragraph_lane_plays_scope.md; FINDING-s246-lane-plays-skipped)
# Rule pins: R-990-01@?
"""Proves what HARNESS-lane-plays-scope builds in lane_plays_check (merge_gate_support.py) and lane_plays.toml.

Current interface (main + keep-red): lane_plays_check(candidate, base_ref, *, python_exe, timeout, known_red_path,
lane_map_path, plays_dir, changed, setup, evidence_out) -> (ok: bool, detail: str); nothing ran -> (True, "skipped: ...").

UNSTATED INTERFACE CHOICES made by this file (the builder follows these or stops with a test-defect):
  * `[shared]` table: each KEY is a glob (fnmatch, `**` matches across `/`), each VALUE is a list of lane letters, or
    ["*"] for every lane that has a plays directory. The `[lanes]` table keeps its form.
  * "autoload/** except autoload/net/**": the function itself must not treat a file under autoload/net/ as matching the
    shared `autoload/**` glob (so autoload/net/x.gd runs F only, through F's own glob). The fixture lists plain `autoload/**`.
  * Which lanes ran is observed by marker files: each fake play writes <LP_MARK_DIR>/<lane> when pytest runs it.
  * Fake plays are ordinary `def test_` files (name `S-246.py` in D, `p.py` elsewhere), run by the real function with
    setup=False (no xvfb) and python_exe=sys.executable; known-red path is a fixture file.
  * The merge_gate.sh comment names the shared table by the word `shared` within the lane_plays comment block.
"""
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
sys.path.insert(0, str(SPEC_DIR))

import merge_gate_support as mgs  # noqa: E402

PLAYS = "tests/qa/desktop/plays"
LANES = "ABCDEF"
ALL = set(LANES)
FIXTURE_TOML = """[lanes]
A = ["scenes/tactical_c/**"]
B = ["scenes/galaxy/**"]
C = ["scenes/ground3d/**"]
D = ["scenes/space3d/**"]
E = ["scenes/settlement/**"]
F = ["autoload/net/**", "scenes/lobby/**"]

[shared]
"tests/qa/desktop/plays/*/_play.py" = ["*"]
"tests/qa/desktop/plays/A/play_support.py" = ["*"]
"tests/qa/desktop/daemon_client.py" = ["*"]
"tests/qa/desktop/conftest.py" = ["*"]
"autoload/**" = ["*"]
"scenes/tactical_c/**" = ["A", "C"]
"scenes/main*/**" = ["*"]
"project.godot" = ["*"]
"pipe/**" = ["*"]
"csrc/**" = ["*"]
"""
PLAY = ("import os, pathlib\n"
        "def test_marks():\n"
        "    d = pathlib.Path(os.environ['LP_MARK_DIR'])\n"
        "    d.mkdir(parents=True, exist_ok=True)\n"
        "    (d / %r).write_text('ran')\n")


def _tree(tmp_path, red_lane=None):
    cand = tmp_path / "cand"
    for lane in LANES:
        d = cand / PLAYS / lane
        d.mkdir(parents=True, exist_ok=True)
        body = PLAY % lane
        if lane == red_lane:
            body += "    assert False\n"
        (d / ("S-246.py" if lane == "D" else "p.py")).write_text(body)
    (tmp_path / "map.toml").write_text(FIXTURE_TOML)
    return cand


def _run(tmp_path, monkeypatch, changed, known="", red_lane=None, lane_map=None):
    cand = _tree(tmp_path, red_lane)
    monkeypatch.setenv("LP_MARK_DIR", str(tmp_path / "marks"))
    kr = tmp_path / "known.txt"
    kr.write_text(known)
    ok, detail = mgs.lane_plays_check(cand, "HEAD", python_exe=sys.executable, timeout=120, known_red_path=kr,
                                      lane_map_path=lane_map or tmp_path / "map.toml", changed=changed, setup=False)
    marks = tmp_path / "marks"
    return ok, detail, {p.name for p in marks.iterdir()} if marks.is_dir() else set()


def test_play_file_alone_runs_its_lane_s246_control(tmp_path, monkeypatch):
    """R-990-01 FINDING-s246-lane-plays-skipped positive control: only plays/D/S-246.py changed -> D runs, nothing else."""
    ok, detail, ran = _run(tmp_path, monkeypatch, [f"{PLAYS}/D/S-246.py"])
    assert "skipped" not in detail, detail  # red on main: (a) behaviour wrong, 'skipped: no lane plays touched'
    assert ok and ran == {"D"}, (ok, detail, ran)


def test_shared_helper_in_play_dir_runs_every_lane(tmp_path, monkeypatch):
    """R-990-01: plays/A/play_support.py alone runs every lane."""
    ok, detail, ran = _run(tmp_path, monkeypatch, [f"{PLAYS}/A/play_support.py"])
    assert ok and ran == ALL, (ok, detail, ran)


def test_other_shared_play_helpers_run_every_lane(tmp_path, monkeypatch):
    """R-990-01: _play.py, daemon_client.py and conftest.py each run every lane."""
    for i, f in enumerate([f"{PLAYS}/B/_play.py", "tests/qa/desktop/daemon_client.py", "tests/qa/desktop/conftest.py"]):
        ok, detail, ran = _run(tmp_path / str(i), monkeypatch, [f])
        assert ok and ran == ALL, (f, ok, detail, ran)


def test_sim_change_runs_every_lane(tmp_path, monkeypatch):
    """R-990-01: csrc/unit.c alone runs every lane."""
    ok, detail, ran = _run(tmp_path, monkeypatch, ["csrc/unit.c"])
    assert ok and ran == ALL, (ok, detail, ran)


def test_other_shared_client_paths_run_every_lane(tmp_path, monkeypatch):
    """R-990-01: autoload/x.gd, scenes/main_menu/x.gd, project.godot and pipe/x.c each run every lane."""
    for i, f in enumerate(["autoload/x.gd", "scenes/main_menu/x.gd", "project.godot", "pipe/x.c"]):
        ok, detail, ran = _run(tmp_path / str(i), monkeypatch, [f])
        assert ok and ran == ALL, (f, ok, detail, ran)


def test_autoload_net_runs_lane_f_only(tmp_path, monkeypatch):
    """R-990-01: autoload/net/** is excepted from the shared autoload glob (F only, through F's own glob)."""
    ok, detail, ran = _run(tmp_path, monkeypatch, ["autoload/net/x.gd"])
    assert ok and ran == {"F"}, (ok, detail, ran)


def test_tactical_c_runs_a_and_c_only(tmp_path, monkeypatch):
    """R-990-01: scenes/tactical_c/x.gd runs A and C only (the ground view runs inside tactical_c)."""
    ok, detail, ran = _run(tmp_path, monkeypatch, ["scenes/tactical_c/x.gd"])
    assert ok and ran == {"A", "C"}, (ok, detail, ran)


def test_galaxy_runs_b_only(tmp_path, monkeypatch):
    """R-990-01: scenes/galaxy/x.gd runs B only (control: green on main)."""
    ok, detail, ran = _run(tmp_path, monkeypatch, ["scenes/galaxy/x.gd"])
    assert ok and ran == {"B"}, (ok, detail, ran)


def test_docs_only_diff_is_still_skipped(tmp_path, monkeypatch):
    """R-990-01: a docs-only diff runs no play and returns skipped (control: green on main)."""
    ok, detail, ran = _run(tmp_path, monkeypatch, ["docs/northstar/README.md"])
    assert ok and detail.startswith("skipped") and ran == set(), (ok, detail, ran)


def test_known_red_list_applies_to_the_widened_scope(tmp_path, monkeypatch):
    """R-990-01: a listed red play in a lane run by the sim change stays accepted; an unlisted one rejects."""
    listed = f"{PLAYS}/E/p.py::test_marks"
    ok, detail, ran = _run(tmp_path / "a", monkeypatch, ["csrc/unit.c"], known=listed + "  # reason\n", red_lane="E")
    assert ok and "known red: " + listed in detail and ran == ALL, (ok, detail, ran)
    ok, detail, ran = _run(tmp_path / "b", monkeypatch, ["csrc/unit.c"], known="", red_lane="E")
    assert not ok and "red outside known-red list" in detail and listed in detail, (ok, detail)


def test_stale_known_red_rejects_in_the_widened_scope(tmp_path, monkeypatch):
    """R-990-01: a listed play that now passes still rejects as stale when the sim change runs its lane."""
    listed = f"{PLAYS}/E/p.py::test_marks"
    ok, detail, _ = _run(tmp_path, monkeypatch, ["csrc/unit.c"], known=listed + "\n")
    assert not ok and "stale known-red" in detail, (ok, detail)


def test_real_lane_plays_toml_has_shared_table_and_unchanged_lanes():
    """R-990-01: the real lane_plays.toml keeps [lanes] and gains [shared] with the paragraph's globs."""
    data = tomllib.loads((SPEC_DIR / "lane_plays.toml").read_text())
    assert data["lanes"] == {"A": ["scenes/tactical_c/**"], "B": ["scenes/galaxy/**"], "C": ["scenes/ground3d/**"],
                             "D": ["scenes/space3d/**"], "E": ["scenes/settlement/**"],
                             "F": ["autoload/net/**", "scenes/lobby/**"]}
    shared = data.get("shared", {})  # red on main: (b) no [shared] table
    for g in ("tests/qa/desktop/plays/*/_play.py", "tests/qa/desktop/plays/A/play_support.py",
              "tests/qa/desktop/daemon_client.py", "tests/qa/desktop/conftest.py", "autoload/**", "scenes/tactical_c/**",
              "scenes/main*/**", "project.godot", "pipe/**", "csrc/**"):
        assert g in shared, g
    assert shared["csrc/**"] == ["*"] and sorted(shared["scenes/tactical_c/**"]) == ["A", "C"]


def test_real_toml_drives_the_widened_scope(tmp_path, monkeypatch):
    """R-990-01: with the real lane_plays.toml, csrc/unit.c runs every lane and scenes/galaxy/x.gd only B."""
    real = SPEC_DIR / "lane_plays.toml"
    ok, detail, ran = _run(tmp_path / "a", monkeypatch, ["csrc/unit.c"], lane_map=real)
    assert ok and ran == ALL, (ok, detail, ran)
    ok, detail, ran = _run(tmp_path / "b", monkeypatch, ["scenes/galaxy/x.gd"], lane_map=real)
    assert ok and ran == {"B"}, (ok, detail, ran)


def test_gate_stage_comment_names_the_shared_table():
    """R-990-01: the lane_plays comment block in merge_gate.sh names the shared table."""
    lines = (SPEC_DIR / "merge_gate.sh").read_text().splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("# ----") and "lane_plays" in l)
    assert "shared" in " ".join(lines[i + 1:i + 4]), lines[i:i + 4]
