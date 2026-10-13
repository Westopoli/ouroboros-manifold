"""ALG-66 Group move (docs/bible/algorithms.md; E-13 R-095-01/R-095-02, S-095): "For a selection of 2+ living units
with FORMATION_MOVE_ENABLED: centroid c; scattered if any unit is farther than MAGIC_BOX_SPREAD_RADIUS = 450 from c;
each unit's slot = click + (unit - c), or the click point if scattered or the slot cell is unwalkable; the group is
registered and terminated when the centroid arrives or every unit is within ARRIVAL_TOLERANCE_MULT = 1.5 *
UNIT_COLLISION_RADIUS = 15 of its slot."

The numbers 450, 1.5 and 15 are typed from the text (tolerance 22.5 wu). Slots are read back with
om_unit_get_destination. The "slowest-unit pace is not implemented (Q-095-01)" clause of ALG-66 is stale (R-095-01 is
built: test_core_group_pace.py); see SL-C3-03. FORMATION_MOVE_ENABLED has no switch in the C (always on); noted there.
Positive control per mechanism: test_control_* feeds the same function an input on the other side of the rule.
"""
import ctypes
import math

import pytest

from conftest import OMFeature

VANGUARD = 2
PLAYER = 0
SPREAD = 450.0
TOL = 1.5 * 15.0


def _world(lib):
    w = lib.om_world_new(1, 1)
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _group(lib, w, pts, click):
    ids = [lib.om_unit_spawn(w, VANGUARD, PLAYER, x, y, 0) for x, y in pts]
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    gid = lib.om_command_group_move(w, arr, len(ids), click[0], click[1])
    assert gid != 0 and lib.om_group_is_active(w, gid) == 1
    return ids, gid


def _centroid(pts):
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def test_ALG_66_slot_is_click_plus_offset_from_the_centroid(lib):
    pts = [(0.0, 0.0), (30.0, 0.0), (0.0, 60.0)]
    click = (5000.0, 5000.0)
    w = _world(lib)
    ids, _ = _group(lib, w, pts, click)
    cx, cy = _centroid(pts)
    for u, (x, y) in zip(ids, pts):
        assert lib.om_unit_get_destination(w, u) == pytest.approx((click[0] + (x - cx), click[1] + (y - cy)))


def test_ALG_66_scattered_when_any_unit_is_farther_than_450_from_the_centroid_all_go_to_the_click(lib):
    pts = [(0.0, 0.0), (1000.0, 0.0), (0.0, 100.0)]
    cx, cy = _centroid(pts)
    assert max(math.hypot(x - cx, y - cy) for x, y in pts) > SPREAD
    click = (5000.0, 5000.0)
    w = _world(lib)
    ids, _ = _group(lib, w, pts, click)
    for u in ids:
        assert lib.om_unit_get_destination(w, u) == pytest.approx(click)


def test_control_ALG_66_exactly_450_from_the_centroid_is_not_scattered(lib):
    pts = [(0.0, 0.0), (900.0, 0.0)]  # each exactly 450 from the centroid: "farther than" is strict
    click = (5000.0, 5000.0)
    w = _world(lib)
    ids, _ = _group(lib, w, pts, click)
    assert lib.om_unit_get_destination(w, ids[0]) == pytest.approx((click[0] - 450.0, click[1]))
    assert lib.om_unit_get_destination(w, ids[1]) == pytest.approx((click[0] + 450.0, click[1]))


def test_ALG_66_a_slot_cell_that_is_unwalkable_falls_back_to_the_click_point(lib):
    pts = [(0.0, 0.0), (30.0, 0.0), (0.0, 60.0)]
    click = (5000.0, 5000.0)
    cx, cy = _centroid(pts)
    w = _world(lib)
    ids = [lib.om_unit_spawn(w, VANGUARD, PLAYER, x, y, 0) for x, y in pts]
    blocked_slot = (click[0] + (pts[0][0] - cx), click[1] + (pts[0][1] - cy))
    lib.om_map_add_obstacle(w, blocked_slot[0], blocked_slot[1], 20.0)
    arr = (ctypes.c_uint32 * 3)(*ids)
    assert lib.om_command_group_move(w, arr, 3, click[0], click[1]) != 0
    assert lib.om_unit_get_destination(w, ids[0]) == pytest.approx(click)  # its own slot is blocked
    assert lib.om_unit_get_destination(w, ids[1]) == pytest.approx((click[0] + (pts[1][0] - cx), click[1] + (pts[1][1] - cy)))


def _run_until_group_ends(lib, w, ids, gid, slots, click):
    """Returns (ended_step, trail) where trail[i] = (all_within_tol, centroid_within_tol) after step i+1."""
    trail = []
    for step in range(1, 200):
        lib.om_world_step(w)
        pos = [lib.om_unit_get_pos(w, u) for u in ids]
        all_within = all(math.hypot(p[0] - s[0], p[1] - s[1]) <= TOL for p, s in zip(pos, slots))
        cx, cy = _centroid(pos)
        trail.append((all_within, math.hypot(cx - click[0], cy - click[1]) <= TOL))
        if lib.om_group_is_active(w, gid) == 0:
            return step, trail
    pytest.fail("group never ended")


def test_ALG_66_group_ends_when_the_centroid_arrives_or_every_unit_is_within_22_5_of_its_slot(lib):
    pts = [(0.0, 0.0), (30.0, 0.0), (0.0, 60.0)]
    click = (100.0, 0.0)
    w = _world(lib)
    ids, gid = _group(lib, w, pts, click)
    slots = [lib.om_unit_get_destination(w, u) for u in ids]
    ended, trail = _run_until_group_ends(lib, w, ids, gid, slots, click)
    assert any(trail[-1]), "ended with neither arrival condition true"
    assert not any(any(t) for t in trail[:-1]), "an arrival condition held on an earlier tick and the group stayed active"


def test_control_ALG_66_a_group_far_from_its_click_is_still_active_after_a_few_ticks(lib):
    pts = [(0.0, 0.0), (30.0, 0.0), (0.0, 60.0)]
    w = _world(lib)
    ids, gid = _group(lib, w, pts, (5000.0, 5000.0))
    for _ in range(10):
        lib.om_world_step(w)
    assert lib.om_group_is_active(w, gid) == 1
