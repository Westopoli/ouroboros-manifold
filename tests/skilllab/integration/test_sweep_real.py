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
78 192, three replicates, E1 on:
  - smoke at 1 and 12 workers: the rows are the same bytes (holds). Under GROUP orders not every fight ends clean: 7 of the 108 play
    fights cap outside the controls (s3_layer_above 5, s3_types_by_reach 2, all on layout 192; the other layouts are refused; the csv
    shows 28 because the approximate baselines repeat the play's rows four times) and the mirror control caps once in six (seed 0,
    swapped, 1 v 1 left, 12000 ticks): ledger FINDING-group-orders-cap, for the E1 gate (decisions 23). With orders_per_unit=True (the
    Setup default, which stays True until E1 is in the landing AND this smoke caps zero under group orders) the same run has 1
    non-control cap fight (s3_layer_above) and no mirror cap. That one cap is traced before the lab landing. The assertion below that
    no row outside control_* kinds is a cap (read from the csv rows; defects.cap_rows is the trace, not a substitute) is therefore RED
    on the lab branch for an engine reason, not a builder one, and stays red until the cap is traced (decisions 23).
  - sweep damage_up: the null control holds. The positive control is ONE designated fight, s3_types_by_reach (decisions 22): side1
    wins at damage-up 1.0, side0 at 0.5, so `positive ok is True` below does not depend on any other play. s3_layer_above reads
    identical margins and windows at 1.0 and 0.5; that is not an exemption, it is ledger FINDING-damage-up-layer-above (unexplained,
    to be traced), and no assertion in this file or in test_sweep.py is made on that play for damage-up.
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

# ---- reach (0, 0) on both sides: byte-identical across the vision points ---------------------------------------------------------

# ---- damage-up 0.5 changes the result and not the count --------------------------------------------------------------------------

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

# ---- states: on for sweep and smoke, off for the controls command ------------------------------------------------------------------------

# ---- gated: the smoke and sweep commands -----------------------------------------------------------------------------------------------------

def _read(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _defects_of(rows):
    """The pinned definition of the defect count (test_sweep.py header), recounted from the CSV rows."""
    cell = lambda r: (r["play"], r["layout"], r["kind"], r["knob_value"], r["baseline"], r["enemy_heads"])
    live = [r for r in rows if not r["kind"].startswith("control_")]
    blind = [r for r in live if r["outcome"] == "cap" and r.get("blind_post") == "1"]      # decision 43 item 5 (TD-LAB-REV2-FIX-blind-keys)
    bad = [r for r in live if r["outcome"] == "draw" or (r["outcome"] == "cap" and r.get("blind_post") != "1")]
    return {"cap_rows": sum(r["outcome"] == "cap" for r in bad), "blind_post_rows": len(blind),
            "draw_rows": sum(r["outcome"] == "draw" for r in rows), "cells": len({cell(r) for r in bad})}

