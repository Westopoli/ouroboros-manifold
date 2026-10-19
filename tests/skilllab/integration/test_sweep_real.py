# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L4 (integration/test_sweep_real.py; smoke and sweep commands); rulings 10, 13
"""LAB-REV2-L4 against the real engine.

Quick cases (a second or two each): a hand-built cross-layer 16 v 16 scene (side 0 one layer up, Vanguard with reach one up and one
down, blobs 500 wu apart, both attack-moved to the midpoint) shows the family controls the sweep relies on, read through the
`sweep.controls(...)` predicates so a predicate that disagrees with the engine fails here:
  - vision 0 gives 16 v 16 and no shot (and vision 0.5 on the same scene does shoot: the positive control of that detector);
  - damage-up 0.5 changes the result and not the count (the opening-window firing counts are equal, the margin and survivors move);
  - reach (0, 0) on both sides makes the rows byte-identical across the four vision points.
Numbers measured on the lab branch with a reference build, seed 0, unswapped, 300 ticks for the no-shot cases: vision 0 and 0.5 both
cap with (16, 16) alive, firing unit-seconds (0, 0) against (152.5, 110.75); damage-up 1.0 gives side 0 the win with 7 left
(margin 0.312), damage-up 0.5 with 14 left (margin 0.670), both with an opening window of (12.75, 9.25).

Gated cases (OM_LAB_SLOW=1; they need L3's plays and sweep.py's real builds): the smoke command's rows are the same bytes at 1 and 12
workers and every fight ends side0, side1 or draw; the sweep command writes sweep_<family>.csv and sweep_summary.json. A cap appears
only in control_* kinds (controls cap by design, CONTROL_MAX_TICKS < 12000), and the pinned defect count (non-control caps, draws and
the cells holding them) is recounted from the CSV and must match the entry or summary; non-control caps are pinned at zero.
SATISFIABILITY of the gated cases: the first revision of this file was written before L3's plays existed, so they were unverified.
L3 is on the lab branch now; the fix pass ran them (OM_LAB_SLOW=1) on a scratch copy of the reference sweep.py with approximate real
builds (every baseline the play's own placed scene; the three smoke controls blob/blob, blob 8 and damage_play). Measured, layouts 81
78 192, three replicates, group orders (the flipped default), E1 on:
  - smoke at 1 and 12 workers: the rows are the same bytes (holds). Not every fight ends clean: 7 of the 108 play fights cap outside
    the controls (s3_layer_above 5, s3_types_by_reach 2, all on layout 192; the other layouts are refused; the csv shows 28 because
    the approximate baselines repeat the play's rows four times) and the mirror control caps once in six (seed 0, swapped, 1 v 1 left,
    12000 ticks). With orders_per_unit=True the same run has 1 non-control cap fight (s3_layer_above) and no mirror cap.
    So `set(outcomes) <= {side0, side1, draw}` and `defects.cap_rows == 0` below are RED on the lab branch for an engine reason, not a
    builder one; a ruling on the straggler caps (or on the flip) is owed.
  - sweep damage_up: the null control holds. The positive control (damage-up 0.5 changes the result and not the count) is False
    because s3_layer_above is inert to the knob (identical margins and windows at 1.0 and 0.5; s3_types_by_reach does change: side1 wins
    at 1.0, side0 at 0.5), and the entry ANDs the control over plays. The assertion `positive ok is True` below is red on the real plays
    until the aggregation over plays is ruled (all, any, or one designated play).
  - a 600-tick damage control shows identical margins at both points on the real play, so the damage control runs to elimination.

Capability-gated cases (skipped on a library without OM_TP_FIRING_ARC_DEG or a usable om_roster_set_cone): the arc null control
(parameter pushed at 360 against never set) and the cone null control (range 0 against no cone) read byte-identical rows on the real
engine. They skip today (E0 and E2 are not built) and are unverified for satisfiability until those land.
"""
import csv
import dataclasses
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import __main__ as cli, engine, fight, plays, rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")
V1 = "OM_TP_VISION_UP_1"


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def scene(vision=0.5, damage_up=None, reach=(1, 1), max_ticks=300):
    g0 = Group(side=0, unit="VR", count=16, formation="blob", x=1000.0, y=1000.0, facing_deg=0.0, layer=1, order="attack_move",
               params={"radius": 90.0})
    g1 = Group(side=1, unit="VR", count=16, formation="blob", x=1500.0, y=1000.0, facing_deg=180.0, layer=0, order="attack_move",
               params={"radius": 90.0})
    settings = {V1: vision, "OM_TP_VISION_DOWN_1": vision}
    if damage_up is not None:
        settings["OM_TP_DAMAGE_UP_1"] = damage_up
    return Setup(groups=(g0, g1), unit_types={"VR": {"base": "Vanguard", "reach": reach}}, settings=settings, max_ticks=max_ticks,
                 point=(1250.0, 1000.0))


def fought(library, setup, seed=0, swap=False):
    return fight.fight(setup, seed, swap, engine=library)


# ---- vision 0 gives 16 v 16 and no shot ---------------------------------------------------------------------------------------

def test_vision_zero_gives_16_v_16_and_no_shot(library):
    r = fought(library, scene(vision=0.0))
    assert r.heads == (16, 16) and r.survivors == (16, 16)
    assert r.firing_unit_seconds == (0.0, 0.0) and all(a0 == 0 and a1 == 0 for _t, a0, a1 in r.firing)
    assert r.first_contact_tick == -1 and r.outcome == "cap"          # a capped fight is the expected end of this control only


def test_positive_control_vision_half_on_the_same_scene_does_shoot(library):
    r = fought(library, scene(vision=0.5))
    assert r.firing_unit_seconds[0] > 0 and r.firing_unit_seconds[1] > 0 and r.first_contact_tick >= 0


def test_the_sweep_predicate_agrees_with_the_engine_on_both_cases(library):
    check = sweep.controls("vision")["positive"].check
    assert check([[fought(library, scene(vision=0.0))]]) is True
    assert check([[fought(library, scene(vision=0.5))]]) is False


# ---- reach (0, 0) on both sides: byte-identical across the vision points ---------------------------------------------------------

def test_reach_zero_rows_are_byte_identical_across_the_four_vision_points(library):
    points = [p for p in sweep.grid("vision")]
    got = [[fought(library, scene(vision=p.value, reach=(0, 0)))] for p in points]
    flat = [rows_mod.fight_row(rs[0]) for rs in got]
    assert len(flat) == 4 and all(r == flat[0] for r in flat)
    assert all(rs[0].firing_unit_seconds == (0.0, 0.0) for rs in got)
    assert sweep.controls("vision")["null"].check(got) is True


def test_positive_control_the_null_detector_fires_on_rows_that_do_differ(library):
    differing = [[fought(library, scene(vision=0.0, reach=(0, 0)))], [fought(library, scene(vision=0.5, reach=(1, 1)))]]
    assert sweep.controls("vision")["null"].check(differing) is False


# ---- damage-up 0.5 changes the result and not the count --------------------------------------------------------------------------

def test_damage_up_half_changes_the_result_and_not_the_count(library):
    base = fought(library, scene(damage_up=1.0, max_ticks=12000))
    half = fought(library, scene(damage_up=0.5, max_ticks=12000))
    assert base.firing_window == half.firing_window and base.weighted_window == half.weighted_window       # the count
    assert base.firing[:12] == half.firing[:12]
    assert (base.outcome, base.margin, base.survivors) != (half.outcome, half.margin, half.survivors)       # the result
    assert half.margin > base.margin          # side 1 fires up at side 0: half the damage helps side 0
    assert sweep.controls("damage_up")["positive"].check([[base], [half]]) is True


def test_positive_control_the_damage_detector_fires_on_two_identical_runs(library):
    a = fought(library, scene(damage_up=1.0, max_ticks=12000))
    b = fought(library, scene(damage_up=1.0, max_ticks=12000))
    assert sweep.controls("damage_up")["positive"].check([[a], [b]]) is False


# ---- arc and cone null controls (gated on the library) ------------------------------------------------------------------------------

def test_the_arc_null_control_reads_360_pushed_against_never_set_as_byte_identical_rows(library):
    if not sweep.detect(library).arc:
        pytest.skip("the library has no OM_TP_FIRING_ARC_DEG (E0 not built): unverified for satisfiability until it lands")
    ctl = sweep.controls("arc")["null"]
    got = []
    for p in sorted(ctl.points, key=lambda p: -len(p.settings)):
        setup = scene(vision=0.5)
        setup = dataclasses.replace(setup, settings={**setup.settings, **p.settings}, **p.setup)
        got.append([fought(library, setup)])
    assert ctl.check(got) is True
    assert got[0][0].firing_unit_seconds[0] > 0                 # positive control: the scene does shoot, so identical rows mean something


def test_the_cone_null_control_reads_range_zero_against_no_cone_as_byte_identical_rows(library):
    if not sweep.detect(library).cone:
        pytest.skip("the library has no usable om_roster_set_cone (E2 not built): unverified for satisfiability until it lands")
    ctl = sweep.controls("cone")["null"]
    got = []
    for p in sorted(ctl.points, key=lambda p: -len(p.setup)):
        got.append([fought(library, dataclasses.replace(scene(vision=0.5), **p.setup))])
    assert ctl.check(got) is True
    assert got[0][0].firing_unit_seconds[0] > 0


# ---- capabilities: arc and cone are skipped with a reason when the library lacks them ------------------------------------------------

def test_detect_matches_the_header_and_the_symbol(library):
    caps = sweep.detect(library)
    assert caps.arc == ("OM_TP_FIRING_ARC_DEG" in engine._load_param_ids())
    assert isinstance(caps.cone, bool)
    if caps.cone:
        assert hasattr(library._lib, "om_roster_set_cone")


def test_the_arc_family_is_skipped_with_a_recorded_reason_on_a_library_without_the_parameter(tmp_path, library):
    if sweep.detect(library).arc:
        pytest.skip("the library has OM_TP_FIRING_ARC_DEG; the skip path is covered with fakes in test_sweep.py")
    entry = sweep.run_family("arc", tmp_path, builds=None, layouts={}, plays=())
    assert "OM_TP_FIRING_ARC_DEG" in entry["skipped"] and entry["csv"] is None and not list(tmp_path.glob("sweep_arc*.csv"))


def test_the_cone_family_is_skipped_with_a_recorded_reason_on_a_library_without_a_usable_cone(tmp_path, library):
    if sweep.detect(library).cone:
        pytest.skip("the library can set a cone; the skip path is covered with fakes in test_sweep.py")
    entry = sweep.run_family("cone", tmp_path, builds=None, layouts={}, plays=())
    assert "om_roster_set_cone" in entry["skipped"] and entry["csv"] is None


# ---- states: on for sweep and smoke, off for the controls command ------------------------------------------------------------------------

def test_the_controls_command_plays_have_states_off(library):
    """Harness spec rev 2: Setup.states is opt-in; the `controls` command and the speed guards leave it off."""
    for build in (plays.blob_play(16), plays.damage_play(16)):
        assert build(16, False).states is False and build(8, True).states is False


def test_a_default_setup_has_the_flipped_orders_default_and_states_off():
    s = Setup(groups=(), unit_types={})
    assert (s.states, s.orders_per_unit) == (False, False)


# ---- gated: the smoke and sweep commands -----------------------------------------------------------------------------------------------------

def _read(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _defects_of(rows):
    """The pinned definition of the defect count (test_sweep.py header), recounted from the CSV rows."""
    cell = lambda r: (r["play"], r["layout"], r["kind"], r["knob_value"], r["baseline"], r["enemy_heads"])
    bad = [r for r in rows if r["outcome"] in ("cap", "draw") and not r["kind"].startswith("control_")]
    return {"cap_rows": sum(r["outcome"] == "cap" for r in bad), "draw_rows": sum(r["outcome"] == "draw" for r in rows),
            "cells": len({cell(r) for r in bad})}


@SLOW
def test_smoke_rows_are_the_same_bytes_at_1_and_12_workers_and_every_fight_ends_clean(tmp_path):
    assert cli.main(["smoke", "--out", str(tmp_path / "w1"), "--workers", "1"]) == 0
    assert cli.main(["smoke", "--out", str(tmp_path / "w12"), "--workers", "12"]) == 0
    assert (tmp_path / "w1" / "smoke.csv").read_bytes() == (tmp_path / "w12" / "smoke.csv").read_bytes()
    a = json.loads((tmp_path / "w1" / "smoke_summary.json").read_text())
    b = json.loads((tmp_path / "w12" / "smoke_summary.json").read_text())
    assert a["rows_sha256"] == b["rows_sha256"]
    assert set(a["outcomes"]) <= {"side0", "side1", "draw"}, a["outcomes"]          # no cap: a capped fight is a lab defect
    smoke_rows = _read(tmp_path / "w1" / "smoke.csv")
    assert a["defects"] == _defects_of(smoke_rows) == b["defects"] and a["defects"]["cap_rows"] == 0
    assert {r["prefight"] for r in _read(tmp_path / "w1" / "smoke.csv") if r["family"] != "controls"} == {"ok"}
    assert isinstance(a["refused"], list) and set(a["prefight"]) <= {"ok", "no_fit", "unroutable", "no_reach"}
    layouts = {r["layout"] for r in _read(tmp_path / "w1" / "smoke.csv") if r["family"] == "vision"}
    assert layouts <= {"81", "78", "192"}
    assert {r["play"] for r in _read(tmp_path / "w1" / "smoke.csv") if r["family"] == "controls"} == {"mirror", "numbers", "planted"}


@SLOW
def test_the_sweep_command_writes_the_family_csv_and_the_summary(tmp_path):
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path), "--workers", "12"]) == 0
    rows = _read(tmp_path / "sweep_damage_up.csv")
    assert rows and {r["family"] for r in rows} == {"damage_up"} and {"grid"} <= {r["kind"] for r in rows}
    summary = json.loads((tmp_path / "sweep_summary.json").read_text())
    entry = summary["families"]["damage_up"]
    assert entry["skipped"] is None and entry["csv"] == "sweep_damage_up.csv"
    assert entry["controls"]["positive"]["ok"] is True and entry["controls"]["null"]["ok"] is True
    assert {r["outcome"] for r in rows} <= {"side0", "side1", "draw", "cap"}
    assert {r["kind"] for r in rows if r["outcome"] == "cap"} <= {"control_positive", "control_null"}      # a cap is allowed in a control only
    assert entry["defects"] == _defects_of(rows) and entry["defects"]["cap_rows"] == 0
