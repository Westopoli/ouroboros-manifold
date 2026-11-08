# Rule pins: R-207-06, R-207-07, R-097-01, R-207-05, R-190-07
"""Engine rule fixes 2026-11-08, F1, whole fights: a unit never enters a blocked cell, and a walker goes round an obstacle.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F1" and "Test architecture" (whole-run, per tick, the real lab engine, sight on and
off, many units, catalogue layouts). Evidence: docs/reports/2026-11-07-rule-enforcement.md (sweep I1: 14,427 unit-ticks inside a box on L-0039).
The oracle is engine_rules_oracle.py (this directory), which reads engine state after every step and asks the engine's own
om_navmesh_is_cell_blocked; it does not import scripts/skilllab/invariants.py (F0 ships that, and does not exist when these are written).
The single-unit and single-pair geometry is tests/csim/test_E13_R207_06_never_enter_blocked.py.

Rule words (docs/bible/epics/E-13-*.md, as written 2026-11-08):
  E-13 Invariants "A unit never enters a blocked cell."
  R-207-06  never inside a blocked cell at the end of a tick (depth tolerance DRAFT-inv-cell-depth 1 wu, Westley's)
  R-207-07  inside the canvas
  R-097-01 / R-207-05 / R-190-07  "an obstacle is a detour, never a full stop": a walker ordered across a box face arrives on the far side

Measured on the unfixed tree (2026-11-08, seed 1, 100 simulated seconds, deeper than 1 wu inside a blocked cell):
  box layout below  sight off 673 unit-ticks in 8 units, sight on 517 in 7; no side-A walker ever passes the box
  L-0039 sight on 549, sight off 4302; L-0037 (chokepoint) sight on 1655; L-0073 (city) sight on 4145;  L-0050 (no features) 0, a control
"""
import pytest

import engine_rules_oracle as oracle

SEEDED = 1
WIDTH = HEIGHT = 4000.0                  # small_flat
FAR_SIDE_X = 2250.0                      # the box is x 2000..2100 (sight on) or x 1900..2200 (sight off: padded by 1 wu and rounded out to whole cells): past 2250 is the far side


def box_layout():
    """12 walkers (8 Vanguard, 4 Raider) west of a 100 x 800 wu box, 12 Vanguards east of it that hold; the west side attack-moves to
    the east side's centroid, so the straight line runs into the box face (the L-0039 geometry, enlarged and made plain)."""
    a = [{"role": "Vanguard" if i < 8 else "Raider", "x": 1400.0 + 40 * (i % 3), "y": 1850.0 + 40 * (i // 3), "layer": 0} for i in range(12)]
    b = [{"role": "Vanguard", "x": 2800.0 + 40 * (i % 3), "y": 1850.0 + 40 * (i // 3), "layer": 0} for i in range(12)]
    return {"id": "X-f1-box", "landscape": "small_flat", "orders": "hold:B", "predict": "A", "side_a": {"units": a}, "side_b": {"units": b},
            "features": [{"kind": "cover", "x": 2050.0, "y": 2000.0, "boxes": [{"x": 2050.0, "y": 2000.0, "w": 100, "h": 800}]}]}


@pytest.fixture(scope="module", params=["off", "on"])
def box_run(request):
    return request.param, oracle.fight_layout(box_layout(), request.param, 150)


def test_R_207_06_walkers_attack_moving_through_a_box_never_end_a_tick_in_a_blocked_cell(box_run):
    """R-207-06 / E-13 Invariants, per tick, 24 walkers, a 100 x 800 wu box, sight on and off. Red today: 673 (off) / 517 (on) unit-ticks
    deeper than 1 wu inside the box, 7 or 8 units."""
    sight, rec = box_run
    bad = oracle.cell_entries(rec)
    assert not bad, "sight %s: %d unit-ticks inside a blocked cell (%d units), first %s" % (sight, len(bad), oracle.distinct_units(bad), bad[:3])


def test_R_097_01_walkers_ordered_across_a_box_face_arrive_on_the_far_side(box_run):
    """R-097-01 / R-207-05 / R-190-07: 'an obstacle is a detour, never a full stop.' At some tick a living side-A walker stands east of the
    box. Red today: they park at the west face (the fight ends in silence with all 24 alive)."""
    sight, rec = box_run
    past = [tk["n"] for tk in rec.ticks for u in rec.ids if rec.side[u] == 0 and tk["post"][u]["alive"] and tk["post"][u]["x"] > FAR_SIDE_X]
    assert past, "sight %s: no side-A walker ever passed the box in %d ticks" % (sight, len(rec.ticks))


def test_R_207_07_control_nobody_leaves_the_canvas_in_the_box_fights(box_run):
    """R-207-07 control (green today): no living unit ends a tick outside the canvas. Proves the recorder reads positions."""
    sight, rec = box_run
    assert len(rec.ticks) > 100, "scene broken: the fight is %d ticks long" % len(rec.ticks)
    assert not oracle.outside_canvas(rec, WIDTH, HEIGHT)


@pytest.mark.parametrize("name,sight", [("L-0039", "on"), ("L-0039", "off"), ("L-0037", "on"), ("L-0073", "on")])
def test_R_207_06_no_unit_ends_a_tick_in_a_blocked_cell_on_catalogue_layouts(name, sight):
    """R-207-06 on the layouts the spec names: L-0039 (cover boxes), L-0037 (a chokepoint), L-0073 (a city), per tick, 100 simulated
    seconds. Red today: 549 / 4302 / 1655 / 4145 unit-ticks."""
    rec = oracle.played(name, sight)
    bad = oracle.cell_entries(rec)
    assert not bad, "%s sight %s: %d unit-ticks inside a blocked cell (%d units), first %s" % (name, sight, len(bad), oracle.distinct_units(bad), bad[:3])


def test_R_207_06_control_a_layout_with_no_boxes_has_no_unit_in_one():
    """Control (green today): L-0050 has no features, so the oracle must find nothing. It also proves the oracle's cell test is not a
    blanket 'true' and that the fight ran (2000 ticks, many unit-ticks)."""
    rec = oracle.played("L-0050", "on")
    assert oracle.unit_ticks(rec) > 10000
    assert not oracle.cell_touches(rec)
