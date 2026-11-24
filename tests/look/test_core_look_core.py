"""Look-judge rig piece 1 (core). Spec: docs/northstar/plans/cascades/look-judge-rig/spec.md.

Interface these tests fix (builder implements, test writer does not create):
  scripts.look.card.load_card(path) -> dict; raises scripts.look.card.CardError
  scripts.look.state_checks.check_overlap(fight, radius=15.0, max_ticks=3) -> {verdict, numbers, tick}
  scripts.look.state_checks.check_unit_in_wall(fight) -> same shape; walls = fight["walls"] [[x0,y0,x1,y1],..]
  scripts.look.state_checks.check_frozen(fight, max_identical=N) -> same shape
  scripts.look.runner.run_card(card, fight_path) -> [row]; run(cards, fight_path, out_dir) -> rows, writes out_dir/rows.json + out_dir/report.html
  scripts.look.report.render(rows) -> HTML str
Row = {req, check, kind, verdict, numbers, crop, frame, tick}.
Frozen-frame window is Westley's: see tests/look/test_core_park_thresholds.py is not needed; value passed explicitly.
"""
import copy
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
A1 = ROOT / "docs/northstar/story_reviews/westley/look_2026-11-19/A1-stacked-pair-near.fight.json"


def unit(i, x, y, side="A", layer=0):
    return {"id": i, "side": side, "role": "Vanguard", "layer": layer, "x": x, "y": y,
            "hp": 100.0, "alive": True, "facing": 0.0, "fired": False, "target": None}


def fight(pairs_by_tick, extra=None):
    """pairs_by_tick: list of unit-lists, one per tick (tick = index)."""
    d = {"schema": "om-fight-2", "seed": 1, "tick_rate": 20, "snapshot_every": 1,
         "orders": {}, "result": {}, "violations": [],
         "frames": [{"tick": t, "alive": [len(u), 0], "units": u} for t, u in enumerate(pairs_by_tick)]}
    d.update(extra or {})
    return d


def apart(gap, ticks):
    return fight([[unit(1, 100.0, 100.0), unit(2, 100.0 + gap, 100.0)] for _ in range(ticks)])


def write(tmp_path, name, d):
    p = tmp_path / name
    p.write_text(json.dumps(d))
    return p


CARD = """
id = "overlap"
requirements = ["R-097-05"]
words = "units must not stand inside each other"

[[checks]]
kind = "state"
name = "no_stack"
success = "no two same-layer units closer than one radius for more than 3 ticks"
broken_twin = "stacked_pair"
[checks.params]
"DRAFT-radius" = 15.0
"""


def card_file(tmp_path, text=CARD, name="c.toml"):
    p = tmp_path / name
    p.write_text(text)
    return p


# ---------------- card ----------------

def test_card_loads_valid(tmp_path):
    """S-look-judge-rig piece 1: a card with id, requirements, words and a check carrying success and broken_twin loads."""
    from scripts.look.card import load_card
    c = load_card(card_file(tmp_path))
    assert c["id"] == "overlap" and c["requirements"] == ["R-097-05"]
    assert c["checks"][0]["broken_twin"] == "stacked_pair"


def test_card_missing_success_rejected(tmp_path):
    """S-look-judge-rig piece 1: a check with no 'success' text is rejected."""
    from scripts.look.card import load_card, CardError
    bad = CARD.replace('success = "no two same-layer units closer than one radius for more than 3 ticks"\n', "")
    with pytest.raises(CardError):
        load_card(card_file(tmp_path, bad))


def test_card_empty_success_rejected(tmp_path):
    """S-look-judge-rig piece 1: an empty 'success' string is as missing as an absent one."""
    from scripts.look.card import load_card, CardError
    bad = CARD.replace("no two same-layer units closer than one radius for more than 3 ticks", "  ")
    with pytest.raises(CardError):
        load_card(card_file(tmp_path, bad))


def test_card_missing_broken_twin_rejected(tmp_path):
    """S-look-judge-rig piece 1: a check with no broken_twin is rejected."""
    from scripts.look.card import load_card, CardError
    bad = CARD.replace('broken_twin = "stacked_pair"\n', "")
    with pytest.raises(CardError):
        load_card(card_file(tmp_path, bad))


def test_card_missing_file_is_error(tmp_path):
    """S-look-judge-rig piece 1: fail closed, a missing card file raises, never returns an empty card."""
    from scripts.look.card import load_card, CardError
    with pytest.raises((CardError, FileNotFoundError)):
        load_card(tmp_path / "nope.toml")


# ---------------- state check R-097-05 ----------------

def test_overlap_clean_twin_passes():
    """R-097-05: units 30 apart (two radii) for the whole run PASS (positive control)."""
    from scripts.look.state_checks import check_overlap
    assert check_overlap(apart(30.0, 20))["verdict"] == "PASS"


def test_overlap_stacked_pair_fails_after_three_ticks():
    """R-097-05: a pair 0.3 apart for 10 ticks FAILs and names both units."""
    from scripts.look.state_checks import check_overlap
    r = check_overlap(apart(0.3, 10))
    assert r["verdict"] == "FAIL"
    assert {p["a"] for p in r["numbers"]["pairs"]} | {p["b"] for p in r["numbers"]["pairs"]} == {1, 2}


def test_overlap_three_ticks_is_allowed_four_fails():
    """R-097-05: closer than one radius for more than 3 ticks fails; exactly 3 passes."""
    from scripts.look.state_checks import check_overlap
    def mix(n):
        return fight([[unit(1, 0, 0), unit(2, 0.3 if t < n else 30.0, 0)] for t in range(12)])
    assert check_overlap(mix(3))["verdict"] == "PASS"
    assert check_overlap(mix(4))["verdict"] == "FAIL"


def test_overlap_different_layers_do_not_count():
    """R-097-05: same-layer units only; a stacked pair on layers 0 and 1 PASSes."""
    from scripts.look.state_checks import check_overlap
    d = fight([[unit(1, 0, 0, layer=0), unit(2, 0.3, 0, layer=1)] for _ in range(10)])
    assert check_overlap(d)["verdict"] == "PASS"


def test_overlap_dead_units_do_not_count():
    """R-097-05: a dead unit lying under a live one is not an overlap."""
    from scripts.look.state_checks import check_overlap
    dead = unit(2, 0.3, 0); dead["alive"] = False
    d = fight([[unit(1, 0, 0), copy.deepcopy(dead)] for _ in range(10)])
    assert check_overlap(d)["verdict"] == "PASS"


def test_overlap_empty_frames_not_pass():
    """R-097-05: a fight with no frames cannot PASS the check."""
    from scripts.look.state_checks import check_overlap
    assert check_overlap(fight([]))["verdict"] != "PASS"


def test_overlap_reports_gap_between_runs_separately():
    """R-097-05: two 2-tick overlaps separated by a clear tick are not one 5-tick overlap."""
    from scripts.look.state_checks import check_overlap
    xs = [0.3, 0.3, 30.0, 0.3, 0.3, 30.0, 30.0]
    d = fight([[unit(1, 0, 0), unit(2, x, 0)] for x in xs])
    assert check_overlap(d)["verdict"] == "PASS"


def test_overlap_a1_fixture_fails_units_82_120_tick_1396():
    """R-097-05: look_2026-11-19/A1 -- units 82 and 120 stand under one radius, about 0.3 apart, ending at tick 1396."""
    from scripts.look.state_checks import check_overlap
    d = json.loads(A1.read_text())
    r = check_overlap(d)
    assert r["verdict"] == "FAIL"
    p = [x for x in r["numbers"]["pairs"] if {x["a"], x["b"]} == {82, 120}]
    assert len(p) == 1
    assert p[0]["last_tick"] == 1396
    assert p[0]["ticks"] > 3
    assert math.isclose(p[0]["min_dist"], 0.33, abs_tol=0.1)
    assert r["tick"] == 1396 or r["tick"] <= 1396  # row tick lies within the run


# ---------------- planted controls ----------------

def test_control_unit_in_wall_fails_and_clean_twin_passes():
    """S-look-judge-rig piece 1 control set: a unit inside a wall rect FAILs; the same unit outside PASSes."""
    from scripts.look.state_checks import check_unit_in_wall
    walls = {"walls": [[200.0, 200.0, 300.0, 300.0]]}
    bad = fight([[unit(1, 250.0, 250.0)] for _ in range(5)], walls)
    ok = fight([[unit(1, 50.0, 50.0)] for _ in range(5)], walls)
    assert check_unit_in_wall(bad)["verdict"] == "FAIL"
    assert check_unit_in_wall(ok)["verdict"] == "PASS"


def test_control_frozen_frame_fails_and_moving_twin_passes():
    """S-look-judge-rig piece 1 control set: frames with ticks advancing but every unit identical for 10 frames FAIL; moving units PASS."""
    from scripts.look.state_checks import check_frozen
    frozen = fight([[unit(1, 5.0, 5.0)] for _ in range(10)])
    moving = fight([[unit(1, 5.0 + t, 5.0)] for t in range(10)])
    assert check_frozen(frozen, max_identical=5)["verdict"] == "FAIL"
    assert check_frozen(moving, max_identical=5)["verdict"] == "PASS"


def test_controls_built_from_a1_fixture(tmp_path):
    """R-097-05: a control built in tmp from A1 -- pair pulled 40 apart PASSes; pair stacked from tick 0 FAILs."""
    from scripts.look.state_checks import check_overlap
    base = json.loads(A1.read_text())
    clean, stacked = copy.deepcopy(base), copy.deepcopy(base)
    for fr in clean["frames"]:
        for u in fr["units"]:
            if u["id"] == 120:
                a = next(v for v in fr["units"] if v["id"] == 82)
                u["x"], u["y"] = a["x"] + 40.0, a["y"]
    assert check_overlap(clean)["verdict"] != "FAIL" or all(
        {p["a"], p["b"]} != {82, 120} for p in check_overlap(clean)["numbers"]["pairs"])
    for fr in stacked["frames"]:
        for u in fr["units"]:
            if u["id"] == 120:
                a = next(v for v in fr["units"] if v["id"] == 82)
                u["x"], u["y"] = a["x"] + 0.2, a["y"]
    r = check_overlap(stacked)
    assert r["verdict"] == "FAIL"
    assert any({p["a"], p["b"]} == {82, 120} for p in r["numbers"]["pairs"])


# ---------------- runner ----------------

def test_runner_missing_fight_file_fails_closed(tmp_path):
    """S-look-judge-rig piece 1: a missing fight file yields FAIL rows, never PASS and never an exception-free empty list."""
    from scripts.look.card import load_card
    from scripts.look.runner import run_card
    rows = run_card(load_card(card_file(tmp_path)), tmp_path / "missing.fight.json")
    assert rows and all(r["verdict"] == "FAIL" for r in rows)


def test_runner_empty_frames_fails_closed(tmp_path):
    """S-look-judge-rig piece 1: a fight with empty frames yields FAIL, never PASS."""
    from scripts.look.card import load_card
    from scripts.look.runner import run_card
    rows = run_card(load_card(card_file(tmp_path)), write(tmp_path, "e.json", fight([])))
    assert rows and all(r["verdict"] == "FAIL" for r in rows)


def test_runner_garbage_fight_file_fails_closed(tmp_path):
    """S-look-judge-rig piece 1: unparseable JSON yields FAIL rows."""
    from scripts.look.card import load_card
    from scripts.look.runner import run_card
    p = tmp_path / "g.json"; p.write_text("{not json")
    rows = run_card(load_card(card_file(tmp_path)), p)
    assert rows and all(r["verdict"] == "FAIL" for r in rows)


def test_runner_row_shape_and_verdicts(tmp_path):
    """S-look-judge-rig piece 1: clean fight gives one PASS row per check with the row keys; stacked gives FAIL."""
    from scripts.look.card import load_card
    from scripts.look.runner import run_card
    c = load_card(card_file(tmp_path))
    ok = run_card(c, write(tmp_path, "ok.json", apart(30.0, 10)))
    bad = run_card(c, write(tmp_path, "bad.json", apart(0.3, 10)))
    assert set(ok[0]) >= {"req", "check", "kind", "verdict", "numbers", "crop", "frame", "tick"}
    assert ok[0]["req"] == "R-097-05" and ok[0]["check"] == "no_stack" and ok[0]["kind"] == "state"
    assert [r["verdict"] for r in ok] == ["PASS"]
    assert [r["verdict"] for r in bad] == ["FAIL"]


def test_runner_unknown_check_fails_closed(tmp_path):
    """S-look-judge-rig piece 1: a card naming a check the core cannot run yields FAIL, not a skipped PASS."""
    from scripts.look.card import load_card
    from scripts.look.runner import run_card
    t = CARD.replace('name = "no_stack"', 'name = "no_such_check"')
    rows = run_card(load_card(card_file(tmp_path, t)), write(tmp_path, "ok.json", apart(30.0, 10)))
    assert rows and all(r["verdict"] != "PASS" for r in rows)


def test_runner_unsure_counts_as_fail_in_report(tmp_path):
    """S-look-judge-rig piece 1: UNSURE counts as FAIL in the report's totals."""
    from scripts.look.report import render
    rows = [row("R-1", "a", "PASS"), row("R-2", "b", "UNSURE")]
    html = render(rows)
    assert "FAIL: 1" in html and "PASS: 1" in html and "UNSURE" in html


def row(req, check, verdict, tick=0):
    return {"req": req, "check": check, "kind": "state", "verdict": verdict, "numbers": {}, "crop": None, "frame": None, "tick": tick}


# ---------------- report ----------------

def test_report_lists_fail_and_unsure_first():
    """S-look-judge-rig piece 1: the page lists FAIL/UNSURE rows before PASS rows."""
    from scripts.look.report import render
    rows = [row("R-A", "pass_one", "PASS"), row("R-B", "unsure_one", "UNSURE"),
            row("R-C", "pass_two", "PASS"), row("R-D", "fail_one", "FAIL")]
    html = render(rows)
    pos = {n: html.index(n) for n in ("pass_one", "unsure_one", "pass_two", "fail_one")}
    assert max(pos["unsure_one"], pos["fail_one"]) < min(pos["pass_one"], pos["pass_two"])


def test_report_empty_rows_is_not_a_pass_page():
    """S-look-judge-rig piece 1: no rows means nothing was judged; the page must not claim PASS."""
    from scripts.look.report import render
    html = render([])
    assert "FAIL" in html


# ---------------- determinism ----------------

def test_two_runs_byte_identical(tmp_path):
    """S-look-judge-rig piece 1: two runs of the same card and fight give byte-identical rows.json and report.html."""
    from scripts.look.card import load_card
    from scripts.look.runner import run
    c = load_card(card_file(tmp_path))
    f = write(tmp_path, "f.json", apart(0.3, 10))
    run([c], f, tmp_path / "o1")
    run([c], f, tmp_path / "o2")
    for n in ("rows.json", "report.html"):
        assert (tmp_path / "o1" / n).read_bytes() == (tmp_path / "o2" / n).read_bytes()
