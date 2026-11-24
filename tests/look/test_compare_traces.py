"""Look-judge rig piece 5, compare: scripts/look/compare.py (docs/northstar/plans/cascades/look-judge-rig/spec.md).

Spec piece 5, quoted: "runs/loads an approved trace and today's trace, computes the measures (per-unit path shape and length ratio; arrival-time spread;
formation spread over time; nearest-neighbour spacing distribution; stops, reversals and jitter via `scripts/qa/rts_detectors.py`; time overlapped; shots
fired and kill order), checks each against tolerance `DRAFT-feel-<measure>` (values in `scripts/look/tolerances.toml`, all marked DRAFT, Westley's), emits
PASS/FAIL rows and a side-by-side page data file. Calibration: approved vs itself gives zero difference; approved vs a planted movement break (units stopped
short, the 2026-11-18 give-up bug) FAILs."  Shared vocabulary: "A missing frame, timeout, crash or backend disagreement is FAIL or UNSURE, never PASS."

Interface these tests pin (the spec names the file, not the calls):
  compare.load_tolerances(path=None) -> {"DRAFT-feel-<measure>": float}   (path None = scripts/look/tolerances.toml)
  compare.compare(approved, today, tolerances=None) -> dict   approved/today: an om-fight-2 dict or a path to one; never raises on bad input
    result["verdict"]            "PASS" | "FAIL"  (FAIL if any row FAILs)
    result["rows"]               one per measure: {"measure", "verdict", "approved", "today", "difference", "tolerance"}
                                 difference = abs(today - approved) of the two scalars; PASS iff difference <= tolerance
                                 path_length_ratio: approved is 1.0, today is the worst unit's (today path length / approved path length)
    result["page"]               {"camera": {...one camera for both sides...}, "panels": [one per FAILing measure:
                                 {"measure", "ticks": [...], "approved": [...], "today": [...], "approved_value", "today_value", "tolerance"}]}
  Movement fixtures: units A-side only, every unit walks along its own row to x = orders.point[0] (units end on their rows, not on one pixel), snapshot_every 1.
"""
import copy
import importlib
import json
import math
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
A1 = ROOT / "docs/northstar/story_reviews/westley/look_2026-11-19/A1-stacked-pair-near.fight.json"
TOL_FILE = ROOT / "scripts/look/tolerances.toml"

MEASURES = [
    "path_length_ratio", "path_shape", "arrival_spread", "formation_spread", "nn_spacing",
    "stops", "reversals", "jitter", "time_overlapped", "shots_fired", "kill_order",
]
HUGE = 1e9
TINY = 1e-9


def _compare():
    return importlib.import_module("scripts.look.compare")


# ---------------------------------------------------------------- synthetic fights

def fight(unit_paths, orders_point, fired=None, dead_at=None, ticks=300):
    """unit_paths: {id: fn(tick)->(x, y)}. fired: {(id, tick)}. dead_at: {id: tick}."""
    fired = fired or set()
    dead_at = dead_at or {}
    frames = []
    for t in range(ticks + 1):
        units = []
        for uid, fn in unit_paths.items():
            x, y = fn(t)
            alive = not (uid in dead_at and t >= dead_at[uid])
            units.append({"id": uid, "side": "A", "role": "Vanguard", "layer": 0, "x": x, "y": y, "hp": 100.0 if alive else 0.0,
                          "alive": alive, "facing": 0.0, "fired": (uid, t) in fired, "target": None})
        n = sum(u["alive"] for u in units)
        frames.append({"tick": t, "alive": [n, 0], "units": units})
    return {"schema": "om-fight-2", "seed": 1, "snapshot_every": 1, "tick_rate": 20, "ranges": {"Vanguard": 300.0},
            "orders": {"mode": "both_same_point", "point": list(orders_point), "attacker": None},
            "result": {"end": "window", "ticks": ticks, "winner": "-"}, "violations": [], "frames": frames}


def walker(uid, y, start_x=0.0, speed=5.0, delay=0, stop_at=None, jitter=0.0):
    """Walks +x along row y to x=1000 at `speed` wu/tick; optional delay, early stop at x=stop_at, y jitter."""
    def fn(t):
        x = min(1000.0, start_x + speed * max(0, t - delay))
        if stop_at is not None:
            x = min(x, stop_at)
        return (x, y + (jitter if t % 2 else 0.0))
    return fn


POINT = (1000.0, 200.0)
ROWS = [100.0, 140.0, 180.0, 220.0, 260.0, 300.0]


def baseline():
    return fight({i + 1: walker(i + 1, y) for i, y in enumerate(ROWS)}, POINT)


def broken():
    """The 2026-11-18 give-up bug: every unit gives up at x=400 of 1000, far from its point, and stands there."""
    return fight({i + 1: walker(i + 1, y, stop_at=400.0) for i, y in enumerate(ROWS)}, POINT)


def shifted():
    """Same walk, each unit starts 1..6 ticks late and stands 2 wu off its row: a small feel change."""
    return fight({i + 1: walker(i + 1, y + 2.0, delay=i + 1) for i, y in enumerate(ROWS)}, POINT)


def tolerances(**overrides):
    tol = {f"DRAFT-feel-{m}": HUGE for m in MEASURES}
    for m, v in overrides.items():
        tol[f"DRAFT-feel-{m}"] = v
    return tol


def row(result, measure):
    found = [r for r in result["rows"] if r["measure"] == measure]
    assert len(found) == 1, f"expected exactly one row for {measure}, rows: {[r['measure'] for r in result['rows']]}"
    return found[0]


# ---------------------------------------------------------------- positive controls (green today)

def test_control_fixtures_are_valid_and_the_detectors_see_the_break():
    """Spec piece 5 positive control: the synthetic fixtures are well formed and the existing rts_detectors flag the planted break and not the baseline,
    so a red below means compare.py is missing, not that the fixtures are broken."""
    from scripts.qa import rts_detectors as det

    def to_trace(f):
        out = []
        for fr in f["frames"]:
            out.append({"tick": fr["tick"], "dt": 0.05, "commands": [],
                        "units": {u["id"]: {"x": u["x"], "y": u["y"], "vx": 0.0, "vy": 0.0, "facing": u["facing"],
                                            "tx": POINT[0], "ty": u["y"], "target_active": True} for u in fr["units"]}})
        return out
    assert len(det.stuck(to_trace(broken()))) == len(ROWS)
    assert det.stuck(to_trace(baseline())) == []
    for f in (baseline(), broken(), shifted()):
        assert f["schema"] == "om-fight-2" and len(f["frames"]) == 301
    a1 = json.loads(A1.read_text())
    assert a1["schema"] == "om-fight-2" and a1["frames"][0]["units"][0].keys() >= {"id", "side", "x", "y", "layer", "alive", "fired", "target"}


# ---------------------------------------------------------------- tolerances file

def test_tolerances_file_names_every_measure_marked_draft_and_westleys():
    """Spec piece 5: "tolerance `DRAFT-feel-<measure>` (values in `scripts/look/tolerances.toml`, all marked DRAFT, Westley's)". Asserts names and the
    DRAFT/Westley marking only; values must be positive and finite, nothing more (Westley owns every number)."""
    assert TOL_FILE.is_file(), "scripts/look/tolerances.toml does not exist"
    text = TOL_FILE.read_text()
    assert "DRAFT" in text and "Westley" in text
    data = tomllib.loads(text)
    flat = {}
    for k, v in data.items():
        if isinstance(v, dict):
            flat.update(v)
        else:
            flat[k] = v
    for m in MEASURES:
        name = f"DRAFT-feel-{m}"
        assert name in flat, f"{name} missing from tolerances.toml"
        assert isinstance(flat[name], (int, float)) and math.isfinite(flat[name]) and flat[name] > 0
    assert [k for k in flat if not k.startswith("DRAFT-feel-")] == [], "every value must be a DRAFT-feel-* name"


def test_load_tolerances_returns_every_draft_name():
    """Spec piece 5: tolerances are loaded by name from scripts/look/tolerances.toml."""
    tol = _compare().load_tolerances()
    assert set(tol) >= {f"DRAFT-feel-{m}" for m in MEASURES}
    assert all(math.isfinite(v) and v > 0 for v in tol.values())


# ---------------------------------------------------------------- calibration: self and planted break

def test_approved_against_itself_is_zero_difference_and_pass():
    """Spec piece 5 calibration: "approved vs itself gives zero difference"; every measure has a row, all PASS."""
    res = _compare().compare(baseline(), baseline())
    assert res["verdict"] == "PASS"
    assert sorted(r["measure"] for r in res["rows"]) == sorted(MEASURES)
    for r in res["rows"]:
        assert r["difference"] == 0, r
        assert r["verdict"] == "PASS", r
    assert res["page"]["panels"] == []


def test_approved_against_itself_on_the_real_a1_fight_is_zero_difference():
    """Spec piece 5 calibration on a real om-fight-2 file (A1, 250 units, 201 frames), given as paths: difference 0 on every measure, PASS."""
    res = _compare().compare(A1, A1)
    assert res["verdict"] == "PASS"
    assert all(r["difference"] == 0 for r in res["rows"])


@pytest.mark.parametrize("measure", ["path_length_ratio", "arrival_spread", "stops"])
def test_planted_movement_break_fails_the_movement_measures(measure):
    """Spec piece 5 calibration: "approved vs a planted movement break (units stopped short, the 2026-11-18 give-up bug) FAILs", on path length ratio,
    arrival-time spread and stops, with the shipped tolerances from tolerances.toml."""
    res = _compare().compare(baseline(), broken())
    assert res["verdict"] == "FAIL"
    r = row(res, measure)
    assert r["verdict"] == "FAIL", r
    assert r["difference"] > r["tolerance"]


def test_planted_break_path_length_ratio_numbers():
    """Spec piece 5, path length ratio: units that stop at 400 of 1000 walked 0.4 of the approved length; the row carries approved 1.0 and today 0.4."""
    r = row(_compare().compare(baseline(), broken()), "path_length_ratio")
    assert r["approved"] == pytest.approx(1.0)
    assert r["today"] == pytest.approx(0.4, abs=0.02)


# ---------------------------------------------------------------- within tolerance

def test_shifted_trace_within_tolerance_passes_and_differs():
    """Spec piece 5: a shifted-but-within-tolerance trace PASSes. Tolerances are set generously by the test (the numbers are Westley's), so this proves
    the comparison is a tolerance test: the difference is nonzero on the measures the shift touches yet every row PASSes."""
    res = _compare().compare(baseline(), shifted(), tolerances=tolerances())
    assert res["verdict"] == "PASS"
    assert all(r["verdict"] == "PASS" for r in res["rows"])
    assert row(res, "arrival_spread")["difference"] > 0
    assert res["page"]["panels"] == []


# ---------------------------------------------------------------- one measure out of tolerance

def test_one_measure_out_of_tolerance_fails_naming_it_with_both_numbers():
    """Spec piece 5: one measure out of tolerance gives FAIL naming that measure with approved and today's numbers. Only arrival_spread is tight."""
    res = _compare().compare(baseline(), shifted(), tolerances=tolerances(arrival_spread=TINY))
    assert res["verdict"] == "FAIL"
    failed = [r for r in res["rows"] if r["verdict"] == "FAIL"]
    assert [r["measure"] for r in failed] == ["arrival_spread"]
    r = failed[0]
    assert isinstance(r["approved"], (int, float)) and isinstance(r["today"], (int, float))
    assert r["approved"] != r["today"]
    assert r["difference"] == pytest.approx(abs(r["today"] - r["approved"]))
    assert r["tolerance"] == TINY


def test_time_overlapped_out_of_tolerance_fails_only_that_measure():
    """Spec piece 5, time overlapped: units 1 and 2 stand on the same point for 100 ticks today and never overlap in the approved trace."""
    today = fight({1: walker(1, 100.0), 2: (lambda t: (min(1000.0, 5.0 * t), 100.0 if t > 100 else 100.0)), **{i + 1: walker(i + 1, y)
                   for i, y in enumerate(ROWS) if i > 1}}, POINT)
    approved = baseline()
    res = _compare().compare(approved, today, tolerances=tolerances(time_overlapped=TINY))
    r = row(res, "time_overlapped")
    assert r["verdict"] == "FAIL" and r["approved"] == 0 and r["today"] > 0
    assert [x["measure"] for x in res["rows"] if x["verdict"] == "FAIL"] == ["time_overlapped"]


def test_shots_fired_out_of_tolerance_fails_only_that_measure():
    """Spec piece 5, shots fired and kill order: approved fires nothing; today unit 3 fires on 20 ticks."""
    today = fight({i + 1: walker(i + 1, y) for i, y in enumerate(ROWS)}, POINT, fired={(3, t) for t in range(100, 120)})
    res = _compare().compare(baseline(), today, tolerances=tolerances(shots_fired=TINY))
    r = row(res, "shots_fired")
    assert r["verdict"] == "FAIL" and r["approved"] == 0 and r["today"] == 20
    assert [x["measure"] for x in res["rows"] if x["verdict"] == "FAIL"] == ["shots_fired"]


def test_kill_order_change_fails_kill_order():
    """Spec piece 5, kill order: same two deaths in swapped order is a different fight; kill_order difference counts the order disagreement."""
    approved = fight({i + 1: walker(i + 1, y) for i, y in enumerate(ROWS)}, POINT, dead_at={1: 100, 2: 150})
    today = fight({i + 1: walker(i + 1, y) for i, y in enumerate(ROWS)}, POINT, dead_at={1: 150, 2: 100})
    res = _compare().compare(approved, today, tolerances=tolerances(kill_order=TINY))
    assert row(res, "kill_order")["verdict"] == "FAIL"
    assert row(_compare().compare(approved, approved), "kill_order")["difference"] == 0


def test_jitter_and_reversals_are_measured_via_detectors():
    """Spec piece 5, stops/reversals/jitter: a unit that flips 6 wu sideways every tick adds jitter against a smooth approved walk."""
    today = fight({1: walker(1, 100.0, jitter=6.0), **{i + 1: walker(i + 1, y) for i, y in enumerate(ROWS) if i > 0}}, POINT)
    res = _compare().compare(baseline(), today, tolerances=tolerances(jitter=TINY))
    r = row(res, "jitter")
    assert r["verdict"] == "FAIL" and r["today"] > r["approved"]


# ---------------------------------------------------------------- missing, empty, malformed

@pytest.mark.parametrize("bad", ["missing_path", "none", "empty_frames", "empty_dict"])
def test_missing_or_empty_today_trace_is_fail_never_pass(bad, tmp_path):
    """Shared vocabulary: "A missing frame, timeout, crash ... is FAIL or UNSURE, never PASS." A missing or empty trace gives FAIL, no exception."""
    today = {"missing_path": tmp_path / "nope.fight.json", "none": None, "empty_frames": {**baseline(), "frames": []}, "empty_dict": {}}[bad]
    res = _compare().compare(baseline(), today)
    assert res["verdict"] == "FAIL"
    assert any(r["verdict"] == "FAIL" for r in res["rows"]) or res.get("error")


def test_missing_approved_trace_is_fail_too(tmp_path):
    """Same rule, other side: no approved trace to compare against is FAIL, never a silent PASS."""
    assert _compare().compare(tmp_path / "nope.json", baseline())["verdict"] == "FAIL"
    assert _compare().compare(None, None)["verdict"] == "FAIL"


def test_truncated_today_trace_is_fail():
    """Shared vocabulary, missing frame: today stops at tick 100 of 300 while approved ran to 300; with the shipped tolerances this FAILs."""
    short = baseline()
    short["frames"] = short["frames"][:101]
    assert _compare().compare(baseline(), short)["verdict"] == "FAIL"


# ---------------------------------------------------------------- side-by-side page data

def test_fail_result_carries_side_by_side_page_data():
    """Spec piece 5: "emits ... a side-by-side page data file". Same camera, same ticks for both sides, and the out-of-tolerance numbers."""
    res = _compare().compare(baseline(), broken())
    page = res["page"]
    assert isinstance(page["camera"], dict) and page["camera"]
    failing = {r["measure"] for r in res["rows"] if r["verdict"] == "FAIL"}
    assert {p["measure"] for p in page["panels"]} == failing and failing
    for p in page["panels"]:
        assert p["ticks"] and len(p["ticks"]) == len(p["approved"]) == len(p["today"])
        r = row(res, p["measure"])
        assert p["approved_value"] == r["approved"] and p["today_value"] == r["today"] and p["tolerance"] == r["tolerance"]
    json.dumps(res)


def test_page_camera_covers_both_traces():
    """Spec piece 5, side by side with the same camera: the one camera's box contains every unit position of both traces."""
    res = _compare().compare(baseline(), broken())
    cam = res["page"]["camera"]
    lo_x, hi_x = min(cam["min_x"], cam["max_x"]), max(cam["min_x"], cam["max_x"])
    lo_y, hi_y = min(cam["min_y"], cam["max_y"]), max(cam["min_y"], cam["max_y"])
    for f in (baseline(), broken()):
        for fr in f["frames"]:
            for u in fr["units"]:
                assert lo_x <= u["x"] <= hi_x and lo_y <= u["y"] <= hi_y


def test_compare_is_deterministic_and_does_not_mutate_inputs():
    """Determinism contract: same inputs give a byte-identical result; the input traces are left as they were."""
    a, b = baseline(), broken()
    a0, b0 = copy.deepcopy(a), copy.deepcopy(b)
    r1 = json.dumps(_compare().compare(a, b), sort_keys=True)
    r2 = json.dumps(_compare().compare(a, b), sort_keys=True)
    assert r1 == r2 and a == a0 and b == b0
