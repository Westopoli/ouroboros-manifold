# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 (arm M "overlap pairs"; "Readings per configuration") and section 4 (measure row)
"""LI2, overlapping pairs (the look rig's rule, copied), the four readings label, the whole measure row, DRAFT constants, and purity.

Spec 3 arm M: "overlap pairs (two living units closer than the engine's body distance, per tick, max and total; same measure as the L-0080 overlap files)".
Brief: "reuse scripts.look.state_checks.check_overlap semantics from the look rig: radius 15 wu max 3 ticks; copy the rule, do not import the rig".
The rule (look-judge-rig scripts/look/state_checks.py `check_overlap`): two living units on the same layer closer than the radius (strictly) in consecutive frames; a pair is
listed when its run is longer than max_ticks (strictly); a run is counted in FRAMES (the rig names them ticks; on an every-2-ticks file 4 frames are 8 ticks); the listed
run is the longest, with its last frame's tick and its own minimum distance (3 decimals); a pair is (lower id, higher id); verdict FAIL when any pair is listed.
Added by this piece, from the same predicate: `max_per_frame` (most pairs closer than the radius in one frame) and `total_pair_frames` (sum over frames), runs of any length.

Readings (spec 3, written without a threshold): "all pass; parts pass and whole fails; a part fails and the whole crosses; all fail. A part 'passes' when ...; no part is read
where he stated no direction (marked 'no stated direction'). The reading is a label on the row, not a gate."

Controls (green today): the planted overlap document is a valid lab file; the lab has no function named verdict or gate for a reading."""
import copy
import inspect
import json
import re
import subprocess
from pathlib import Path

import pytest

import measures_fixtures as fx

NM = fx.NOT_MEASURED
ROOT = Path(__file__).resolve().parents[3]
PY = "/home/westopoli/Projects/ouroboros-manifold/.venv/bin/python"


def _overlap_doc():
    """12 frames, ticks 0, 10 ... 110; unit 1 and 2 etc. as pairs; the second unit of a pair is at (dist, y) from the first, which stands at (0, y).
    P1 (1,2): d 10 at frames 2-6 (5 frames), min 4.0 at frame 4.  P2 (3,4): d 12 at frames 3-5 (3 frames: not over the limit).  P3 (5,6): d 3 but on different layers.
    P4 (7,8): d exactly 15.0 all fight (not closer than the radius).  P5 (9,10): d 10 at frames 0-2, unit 10 dead from frame 3 (3 frames; a dead unit does not extend it).
    P6 (11,12): d 10 at frames 1-2 and 4-5 (runs of 2 and 2).  P7 (13,14): d 10 with min 1.0 at frames 0-3 (run 4), 20 at frame 4, d 10 with min 2.5 at frames 5-10 (run 6), 20 at 11.
    Per frame the overlapping pairs: 2 3 4 3 3 4 2 1 1 1 1 0; max 4, total 25."""
    dist = {
        1: [30, 30, 10, 10, 4.0, 10, 10, 30, 30, 30, 30, 30],
        3: [30, 30, 30, 12, 12, 12, 30, 30, 30, 30, 30, 30],
        5: [3.0] * 12,
        7: [15.0] * 12,
        9: [10.0] * 12,
        11: [30, 10, 10, 30, 10, 10, 30, 30, 30, 30, 30, 30],
        13: [1.0, 10, 10, 10, 20, 10, 10, 2.5, 10, 10, 10, 20],
    }
    roster = [(i, "A" if i % 2 else "B", "Vanguard") for i in range(1, 15)]
    ticks = [10 * i for i in range(12)]

    def pos(u, t):
        i = t // 10
        first = u if u % 2 else u - 1
        y = 100.0 * first
        if u % 2:
            return (0.0, y)
        return (dist[first][i], y)
    return fx.make_doc(roster, ticks, pos=pos, alive=lambda u, t: not (u == 10 and t >= 30), layer=lambda u, t: 1 if u == 6 else 0,
                       res=fx.result("A", [7, 6], 110, "silence"))


def test_control_overlap_document_is_a_valid_lab_file():
    from scripts.skilllab.arena import snapshot
    assert snapshot.validate(_overlap_doc()) == []


def test_overlap_lists_the_planted_pairs_and_only_those():
    """P1 (5 frames) and P7 (its longest run, 6 frames, min over THAT run 2.5, last frame tick 100 here) are listed; every control is not."""
    r = fx.m().overlap_pairs(_overlap_doc())
    assert r["verdict"] == "FAIL"
    assert (r["radius"], r["max_ticks"]) == (fx.m().DRAFT_OVERLAP_RADIUS_15, fx.m().DRAFT_OVERLAP_MAX_TICKS_3) == (15, 3)
    assert r["pairs"] == [{"a": 1, "b": 2, "ticks": 5, "last_tick": 60, "min_dist": 4.0},
                          {"a": 13, "b": 14, "ticks": 6, "last_tick": 100, "min_dist": 2.5}]


def test_overlap_per_frame_maximum_and_total():
    r = fx.m().overlap_pairs(_overlap_doc())
    assert (r["max_per_frame"], r["total_pair_frames"]) == (4, 25)


def test_overlap_pass_when_nothing_is_listed():
    """A document with only the control pairs passes, with no pairs; the same pairs listed would fail it."""
    doc = _overlap_doc()
    keep = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    for f in doc["frames"]:
        f["units"] = [u for u in f["units"] if u["id"] in keep]
    r = fx.m().overlap_pairs(doc)
    assert (r["verdict"], r["pairs"]) == ("PASS", [])


def test_overlap_radius_and_limit_are_parameters():
    """A radius of 40 makes the d 30 rows overlap everywhere; max_ticks 5 drops P1 (5 frames is not over 5) and keeps P7."""
    r = fx.m().overlap_pairs(_overlap_doc(), radius=15, max_ticks=5)
    assert [(p["a"], p["b"]) for p in r["pairs"]] == [(13, 14)]
    wide = fx.m().overlap_pairs(_overlap_doc(), radius=40, max_ticks=3)
    assert {(p["a"], p["b"]) for p in wide["pairs"]} >= {(1, 2), (13, 14)}


def test_the_rule_is_copied_not_imported_from_the_look_rig():
    """Brief: copy the rule, do not import the rig. A fresh interpreter imports the module and finds neither scripts.look nor the compiled engine bindings loaded."""
    code = ("import sys; import scripts.skilllab.arena.isolation_measures as m; "
            "bad = [k for k in sys.modules if k == 'scripts.look' or k.startswith('scripts.look.') or k == 'scripts.skilllab.engine']; "
            "assert not bad, bad")
    out = subprocess.run([PY, "-c", code], cwd=str(ROOT), capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-600:]


# --- the four readings -------------------------------------------------------------------------------------------------------------------------------------------

ALL_PASS = "all pass"
PARTS_PASS_WHOLE_FAILS = "parts pass and whole fails"
PART_FAILS_WHOLE_CROSSES = "a part fails and the whole crosses"
ALL_FAIL = "all fail"
NO_DIR = "no stated direction"


@pytest.mark.parametrize("parts,whole,label", [
    (["pass", "pass", "pass"], "pass", ALL_PASS),
    (["pass"], "pass", ALL_PASS),
    (["pass", "pass"], "fail", PARTS_PASS_WHOLE_FAILS),
    (["pass", "fail"], "pass", PART_FAILS_WHOLE_CROSSES),
    (["fail", "fail"], "pass", PART_FAILS_WHOLE_CROSSES),
    (["fail", "fail"], "fail", ALL_FAIL),
    (["fail"], "fail", ALL_FAIL),
    (["pass", NO_DIR], "pass", ALL_PASS),              # no part is read where he stated no direction
    (["pass", NO_DIR], "fail", PARTS_PASS_WHOLE_FAILS),
    (["fail", NO_DIR], "pass", PART_FAILS_WHOLE_CROSSES),
    (["pass", "pass"], NO_DIR, NO_DIR),                # no stated direction for the whole: nothing to read
])
def test_reading_label_for_each_documented_case(parts, whole, label):
    assert fx.m().reading(parts, whole) == label


def test_reading_takes_no_threshold_and_rejects_words_it_does_not_know():
    """Flags are signals (spec 1.3, 'only a signal, not a conclusion'): the function has two parameters, parts and whole, and no pass mark or default."""
    sig = inspect.signature(fx.m().reading)
    assert list(sig.parameters) == ["parts", "whole"]
    with pytest.raises(ValueError):
        fx.m().reading(["pass", "maybe"], "pass")


# --- the measure row, constants, purity ---------------------------------------------------------------------------------------------------------------------------

ROW_KEYS = {"result", "survivors", "margin_survivors", "margin_hp_share", "first_contact_tick", "units_firing", "predictions", "never_fired",
            "orders_ended_short", "idle_units", "spread", "overlap"}


def test_measure_fight_is_every_measure_by_name_and_equals_the_separate_calls():
    """One call, one row: each key equals what the named function returns on the same document. spread is asked at the given ticks."""
    doc = _overlap_doc()
    mod = fx.m()
    row = mod.measure_fight(doc, spread_ticks=[0, 50])
    assert set(row) == ROW_KEYS
    same = {"result": mod.result_of(doc), "survivors": mod.survivors(doc), "margin_survivors": mod.margin_survivors(doc),
            "margin_hp_share": mod.margin_hp_share(doc), "first_contact_tick": mod.first_contact_tick(doc), "units_firing": mod.units_firing(doc),
            "predictions": mod.predictions(doc), "never_fired": mod.never_fired(doc), "orders_ended_short": mod.orders_ended_short(doc),
            "idle_units": mod.idle_units(doc), "spread": mod.spread_at(doc, [0, 50]), "overlap": mod.overlap_pairs(doc)}
    assert json.dumps(row, sort_keys=True) == json.dumps(same, sort_keys=True)


def test_measure_fight_is_deterministic_and_leaves_the_document_alone():
    doc = _overlap_doc()
    before = copy.deepcopy(doc)
    a = json.dumps(fx.m().measure_fight(doc, spread_ticks=[0]), sort_keys=True)
    b = json.dumps(fx.m().measure_fight(doc, spread_ticks=[0]), sort_keys=True)
    assert a == b and doc == before


def test_every_draft_constant_is_named_and_carries_its_draft_comment():
    """Spec 7: 'thresholds are Westley's, each a named constant with a DRAFT- comment'. Each DRAFT_ constant is assigned on a line that has a `DRAFT-` comment."""
    mod = fx.m()
    src = Path(mod.__file__).read_text().splitlines()
    names = [n for n in dir(mod) if n.startswith("DRAFT_")]
    assert {"DRAFT_OPENING_WINDOW_40", "DRAFT_STUCK_TICKS", "DRAFT_IDLE_TICKS_200", "DRAFT_IDLE_FRONT_BEHIND", "DRAFT_ARRIVED_WU_75", "DRAFT_STILL_WU_PER_TICK",
            "DRAFT_STILL_SLACK_WU", "DRAFT_OVERLAP_RADIUS_15", "DRAFT_OVERLAP_MAX_TICKS_3"} <= set(names)
    for n in names:
        line = next((l for l in src if re.match(r"\s*%s\s*=" % n, l)), None)
        assert line is not None and "DRAFT-" in line, "%s has no assignment line with a DRAFT- comment" % n
