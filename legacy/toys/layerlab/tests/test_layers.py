"""Rung R1 tests 3, 6, 7, 8 and 9 (SPEC.md section 10): cross-layer negative control, the halfway
rule, the terrain-forced auto-transition ruling, slopes and walkers, and area damage by layer.

Conventions used throughout:
- `spawn_jitter` is 0 where timing or geometry is read off the trace, so distances are exact.
- A changing unit's window is read from the trace (flag bit0), not assumed: `c0` is its first
  changing tick and `c1` its last. Assertions keep a margin of 1 to 2 ticks around each boundary
  the SPEC leaves open to a one-tick reading (which tick of a window an event lands on). Windows
  where something must fire are at least 18 ticks long, longer than the 16 to 17 tick period of
  a raider (interval 0.8 s).
- "A fires" is trace flag bit1 of that unit (it fires only at its one possible target).
"""
import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, any_in, fire_ticks, grp, make_scenario, table9, unit_trace
from layerlab.ffi import WIN_STALEMATE

END = 10 ** 6


# ---- test 3: negative control, and the twins that show the detector can fail ------------------

def _pair(layer_a, layer_b, rules=None, dist=100.0):
    return make_scenario(
        [grp("A", "raider", 1900.0, 1000.0, layer_a), grp("B", "raider", 1900.0 + dist, 1000.0, layer_b)],
        rules=rules, run={"max_ticks": 700})


def test_negative_control_layers_5_and_1_never_engage():
    """Q-008-01 / R-005-05 (SPEC test 3): A on layer 5 and B on layer 1, both hold, default rules
    (cross-layer fire off, vision four layers apart is 0): STALEMATE, no damage, no shots, and no
    side ever sees the other (first_contact_tick -1)."""
    res = runmod.run(_pair(5, 1), seed=0)
    assert res.winner == WIN_STALEMATE
    assert res.damage_dealt == (0.0, 0.0)
    assert res.shots == (0, 0)
    assert res.first_contact_tick == -1


def test_negative_control_twin_adjacent_layers_with_cross_fire_on_do_damage():
    """Q-008-01 (positive twin of test 3): A on layer 3 and B on layer 4 (adjacent, so the
    default vision tables allow sight), cross-layer range and damage tables on for offsets
    -1, 0, +1: both sides see, fire and do damage, so the stalemate above is a real result of
    the layer gap and not a dead detector."""
    on = table9(m1=1, z=1, p1=1)
    res = runmod.run(_pair(3, 4, rules={"range_mult": on, "dmg_mult": on}), seed=0)
    assert res.first_contact_tick >= 0
    assert res.shots[0] > 0 and res.shots[1] > 0
    assert res.damage_dealt[0] > 0 and res.damage_dealt[1] > 0
    assert res.winner != WIN_STALEMATE


def test_negative_control_vision_gate_is_what_blocks_when_tables_are_on():
    """R-005-05 / Q-008-01: with the cross-layer fire tables on but vision zeroed (vis_factor
    only for the same layer), adjacent-layer units still never see each other: STALEMATE, no
    shots, first_contact_tick -1 (negative). Positive control: the same scenario with the
    default vision table has contact and damage."""
    on = table9(m1=1, z=1, p1=1)
    blind = {"range_mult": on, "dmg_mult": on, "vis_factor": table9(z=1)}
    res = runmod.run(_pair(3, 4, rules=blind), seed=0)
    assert res.winner == WIN_STALEMATE and res.shots == (0, 0) and res.first_contact_tick == -1
    seeing = runmod.run(_pair(3, 4, rules={"range_mult": on, "dmg_mult": on}), seed=0)
    assert seeing.first_contact_tick >= 0 and seeing.shots[0] > 0


def test_negative_control_fire_table_gate_is_what_blocks_when_vision_allows():
    """Q-008-01: adjacent layers with the default tables (vision allows sight, cross-layer fire
    off): contact is made (first_contact_tick >= 0) yet nothing fires, no damage, STALEMATE.
    So first_contact_tick tracks vision and damage tracks the fire tables, independently."""
    res = runmod.run(_pair(3, 4), seed=0)
    assert res.first_contact_tick >= 0
    assert res.shots == (0, 0) and res.damage_dealt == (0.0, 0.0)
    assert res.winner == WIN_STALEMATE


# ---- test 6: the halfway rule from both sides --------------------------------------------------

T0 = 30  # tick at which the flyer's transfer is ordered; before it, shooters have shot at it


def _flyer2(scn):
    """A raider-stat flyer with a 2.0 s transfer (40 ticks, halfway at tick 20) and long range."""
    return add_type(scn, "flyer2", "raider", transition_s=2.0, range=400.0, hp=2000.0)


def _halfway(mode, cross):
    """A: flyer2 on layer 3 at (2000,1000), timed transfer to layer 4 ordered at tick T0.
    B1: raider on layer 3 at (2100,1000). B2: raider on layer 4 at (2100,1060). All hold.
    cross False: default tables (same-layer fire only). cross True: fire tables on for offsets
    -1, 0, +1 so only the halfway rule can keep an off-layer shooter silent."""
    rules = {"halfway_mode": mode, "spawn_jitter": 0.0}
    if cross:
        t = table9(m1=1, z=1, p1=1)
        rules.update(range_mult=t, dmg_mult=t)
    scn = make_scenario(
        [grp("A", "flyer2", 2000.0, 1000.0, 3, transfer_layer=4, transfer_tick=T0),
         grp("B", "raider", 2100.0, 1000.0, 3),
         grp("B", "raider", 2100.0, 1060.0, 4)],
        rules=rules, run={"max_ticks": 140, "stalemate_ticks": 6000})
    _flyer2(scn)
    res = runmod.run(scn, seed=0, trace=True)
    ch = np.flatnonzero(unit_trace(res, 0).changing)
    assert len(ch) > 0, "the flyer never entered a timed transfer (bit0 never set)"
    assert (np.diff(ch) == 1).all(), "changing window is not one contiguous run"
    c0, c1 = int(ch[0]), int(ch[-1])
    assert T0 <= c0 <= T0 + 1, "transfer ordered at tick %d began at tick %d" % (T0, c0)
    assert 39 <= c1 - c0 + 1 <= 41, "R-004-01: a 2.0 s transfer lasts 40 ticks, got %d" % (c1 - c0 + 1)
    return fire_ticks(res, 1), fire_ticks(res, 2), c0, c1


def test_halfway_rule_old_layer_until_half_new_layer_from_half():
    """R-004-02 / Q-004-02 (halfway_mode 1, the rule): during a 40-tick transfer layer 3 to 4,
    the layer-3 attacker fires at the flyer only before the halfway tick (c0+20) and not after;
    the layer-4 attacker only from the halfway tick on. Positive: each shoots in its half
    (and the layer-3 one before the transfer began). Negative: neither shoots in the other's."""
    b1, b2, c0, c1 = _halfway(mode=1, cross=False)
    assert any_in(b1, 0, c0 - 2)          # same-layer shooter was firing before the change
    assert any_in(b1, c0, c0 + 19)        # old layer may attack until halfway
    assert not any_in(b1, c0 + 21, END)   # and not after (flyer is on 4 from half; default tables)
    assert not any_in(b2, 0, c0 + 18)     # new layer may not attack before halfway
    assert any_in(b2, c0 + 20, END)       # and may from halfway on


def test_halfway_rule_holds_even_when_cross_layer_fire_is_on():
    """R-004-02 / Q-004-02 (halfway_mode 1) with cross-layer fire tables on for offsets -1, 0,
    +1, so range and damage alone would let an off-layer shooter fire: SPEC 5.4 still limits a
    changing target to attackers on its effective layer (off = 4). The layer-4 attacker fired
    down at the layer-3 flyer before the change (positive control that cross-layer fire is
    live) yet is silent in the first half; the layer-3 attacker is silent in the second half and
    fires up at it again once the transfer is complete."""
    b1, b2, c0, c1 = _halfway(mode=1, cross=True)
    assert any_in(b2, 0, c0 - 2)              # cross-layer fire is live before the change
    assert not any_in(b2, c0 + 2, c0 + 18)    # but not in the first half of the change
    assert any_in(b2, c0 + 20, c1)            # same layer from halfway
    assert any_in(b1, 0, c0 - 2) and any_in(b1, c0, c0 + 19)
    assert not any_in(b1, c0 + 21, c1 - 1)    # second half: old-layer shooter excluded
    assert any_in(b1, c1 + 2, END)            # after completion: ordinary cross-layer fire again


def test_halfway_mode_both_lets_either_endpoint_layer_fire_throughout():
    """R-004-02 / Q-004-02 reading 'both' (halfway_mode 0, SPEC 5.4): attackers on either
    endpoint layer of the change may fire at it as if on its layer for the whole transfer. The
    layer-4 attacker fires in the first half and the layer-3 one in the second (positive);
    outside the transfer the default same-layer-only tables apply again (negative): the layer-4
    attacker is silent before it, the layer-3 one after it."""
    b1, b2, c0, c1 = _halfway(mode=0, cross=False)
    assert any_in(b1, 0, c0 - 2) and not any_in(b2, 0, c0 - 2)
    assert any_in(b2, c0 + 2, c0 + 19)
    assert any_in(b1, c0 + 21, c1 - 1)
    assert not any_in(b1, c1 + 2, END)
    assert any_in(b2, c1 + 2, END)


def test_halfway_mode_untargetable_silences_both_during_the_change():
    """R-004-02 / Q-004-02 reading 'untargetable' (halfway_mode 2): nobody may target a changing
    unit, so neither attacker fires between the start and the end of the transfer (negative);
    the layer-3 attacker fired before it and the layer-4 one fires after it (positive)."""
    b1, b2, c0, c1 = _halfway(mode=2, cross=False)
    assert any_in(b1, 0, c0 - 2)
    assert not any_in(b1, c0 + 2, c1 - 1) and not any_in(b2, c0 + 2, c1 - 1)
    assert any_in(b2, c1 + 2, END)
    assert not any_in(b1, c1 + 2, END)


def _self_fire(dist, transfer=True):
    """A: flyer2 on layer 3 (transfer to layer 5 at tick T0 if `transfer`), target B: a bastion on
    layer 3 `dist` east of it. Fire tables are on for offsets -2..+2, so vision is the only gate
    after the flyer reaches layer 5: it then sees layer 3 at 800 * 0.2 * 1.3 = 208."""
    t = table9(m2=1, m1=1, z=1, p1=1, p2=1)
    kw = {"transfer_layer": 5, "transfer_tick": T0} if transfer else {}
    scn = make_scenario(
        [grp("A", "flyer2", 2000.0, 1000.0, 3, **kw), grp("B", "bastion", 2000.0 + dist, 1000.0, 3)],
        rules={"spawn_jitter": 0.0, "range_mult": t, "dmg_mult": t},
        run={"max_ticks": 140, "stalemate_ticks": 6000})
    _flyer2(scn)
    res = runmod.run(scn, seed=0, trace=True)
    return res, fire_ticks(res, 0)


def test_changing_unit_keeps_firing_at_a_target_it_still_sees():
    """R-004-02 (the transitioning unit itself may attack): a flyer in a 3 to 5 transfer, target
    150 away on layer 3 and still inside its two-layer sight (208) after the halfway point.
    Positive: it fires in the first half, in the second half while still changing, and after the
    transfer completes."""
    res, fires = _self_fire(150.0)
    ch = np.flatnonzero(unit_trace(res, 0).changing)
    c0, c1 = int(ch[0]), int(ch[-1])
    assert any_in(fires, c0, c0 + 19)
    assert any_in(fires, c0 + 21, c1 - 1)
    assert any_in(fires, c1 + 2, END)


def test_changing_unit_stops_firing_when_the_transition_takes_its_sight_away():
    """R-004-02 (stops attacking a target the moment the transition takes its sight of that
    target away): same flyer, target 300 away on layer 3, outside the 208 it sees from layer 5.
    It fires in the first half (positive) and never again from the halfway point (negative),
    although the fire tables allow the shot and the target is in range. Control: the same
    scenario with no transfer keeps firing through the same later window."""
    res, fires = _self_fire(300.0)
    ch = np.flatnonzero(unit_trace(res, 0).changing)
    c0 = int(ch[0])
    assert any_in(fires, c0, c0 + 19)
    assert not any_in(fires, c0 + 21, END)
    _, control = _self_fire(300.0, transfer=False)
    assert any_in(control, T0 + 21, END)


# ---- test 7: terrain-forced auto-transition (Q-001-03 ruling, Q-001-04) ------------------------

STRIP_LO, STRIP_HI = 1910.0, 2090.0      # core of the 4-cell strip at x 1900..2100 (edges excluded)
BAND_LO, BAND_HI = 310.0, 1690.0         # core of the wall's blocked rows, y 300..1700


def _mover(terrain, *, rules=None, start=(1000.0, 1000.0), goal=(3000.0, 1000.0), layer=1,
           kind="fly", max_ticks=800, order="move", mtype="raider"):
    """One mover (A) with a MOVE order, and an enemy parked on layer 5 in a far corner so the run
    has both sides but nothing engages. Returns (scn, result-with-trace)."""
    r = {"spawn_jitter": 0.0}
    r.update(rules or {})
    scn = make_scenario(
        [grp("A", "mover", start[0], start[1], layer, order=order, goal=list(goal)),
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain=terrain, rules=r, run={"max_ticks": max_ticks, "stalemate_ticks": 6000})
    add_type(scn, "mover", mtype, movement_kind=kind)
    return scn, runmod.run(scn, seed=0, trace=True)


def _arrival_tick(ut, goal, tol=30.0):
    d = np.hypot(ut.x - goal[0], ut.y - goal[1])
    hit = np.flatnonzero(d <= tol)
    return int(hit[0]) if len(hit) else None


def test_barrier_auto_transition_crosses_on_the_nearest_open_layer():
    """Q-001-03 ruling / R-001-05, Q-001-05 reading a2 (SPEC test 7): a `barrier` with h = 2 (layers 1 and 2
    blocked across the whole map), a flying raider on layer 1 ordered across to a point on layer 1,
    auto_transition 1: it crosses the strip on layer 3 (the nearest open layer), having been in a timed
    transfer that began before it reached the strip, and ends on the layer it was ordered on, layer 1
    (two changes). R-001-01 invariant: no tick has it on layer 1 or 2 inside the strip. (Superseded
    expectation: it used to end on layer 3, 'the nearest open layer of the barrier'; that is now only the
    goal layer when the goal itself is blocked on layers 1 and 2, see test_routing.py.)"""
    scn, res = _mover({"preset": "barrier", "h": 2})
    ut = unit_trace(res, 0)
    assert res.unit[0]["layer"] == 1
    assert res.unit[0]["transitions"] == 2
    assert np.hypot(res.unit[0]["x"] - 3000.0, res.unit[0]["y"] - 1000.0) <= 30.0
    first_change = int(np.flatnonzero(ut.changing)[0])
    assert ut.x[first_change] < 1900.0
    inside = (ut.x >= STRIP_LO) & (ut.x <= STRIP_HI)
    assert inside.any()
    assert (ut.layer[inside] >= 3).all()


def test_barrier_without_auto_transition_stops_at_the_near_edge():
    """Q-001-03 / R-001-05 control (SPEC test 7, auto_transition 0): same barrier and order, but
    the unit never changes layer: it stands at the strip's near edge on layer 1 (x just under
    1900), transitions 0, and the changing flag is never set (negative case of the test above)."""
    scn, res = _mover({"preset": "barrier", "h": 2}, rules={"auto_transition": 0})
    ut = unit_trace(res, 0)
    assert res.unit[0]["layer"] == 1 and res.unit[0]["transitions"] == 0
    assert 1850.0 <= res.unit[0]["x"] < 1900.0
    assert not ut.changing.any()


WALL = {"preset": "wall", "h": 2}


def _in_wall_core(ut):
    return (ut.x >= STRIP_LO) & (ut.x <= STRIP_HI) & (ut.y >= BAND_LO) & (ut.y <= BAND_HI)


def test_wall_zero_change_penalty_takes_the_shorter_route_over_the_wall():
    """Q-001-04 reading (b) (forced_change_penalty 0, SPEC test 7): a `wall` with open ends 300
    units from the map edges, h = 2; a layer-1 flyer ordered across the middle. The detour costs
    about 580 units more than the straight line, more than the two timed transfers (2 * 1.0 s * 150 =
    300 units), so the shortest route by time goes over: the unit changes layer (transitions
    >= 1), crosses the wall's blocked rows on a layer above 2, and arrives sooner than the
    detour does (compared in the next test). The crossover itself is in test_routing.py."""
    scn, res = _mover(WALL, rules={"forced_change_penalty": 0})
    ut = unit_trace(res, 0)
    over = _in_wall_core(ut)
    assert over.any(), "unit never crossed the wall's blocked rows: it took the detour"
    assert (ut.layer[over] >= 3).all()
    assert res.unit[0]["transitions"] >= 1


def test_wall_large_change_penalty_takes_the_detour_through_the_open_end():
    """Q-001-04 reading (a), the earlier reading, kept as a knob (forced_change_penalty 100000, set
    explicitly; the default is now 0; SPEC test 7): the same
    wall and order: a detour on the current layer always beats a change, so the unit stays on
    layer 1 (transitions 0), passes the strip only through an open end (y under 300 or from 1700
    up), and arrives later than the penalty-0 unit (negative case of the test above)."""
    _, det = _mover(WALL, rules={"forced_change_penalty": 100000})
    _, short = _mover(WALL, rules={"forced_change_penalty": 0})
    ut = unit_trace(det, 0)
    assert det.unit[0]["layer"] == 1 and det.unit[0]["transitions"] == 0
    assert not ut.changing.any()
    in_strip = (ut.x >= STRIP_LO) & (ut.x <= STRIP_HI)
    assert in_strip.any(), "detour unit never passed the strip"
    assert ((ut.y[in_strip] < 299.0) | (ut.y[in_strip] >= 1701.0)).all()
    assert not _in_wall_core(ut).any()
    a_det = _arrival_tick(ut, (3000.0, 1000.0))
    a_short = _arrival_tick(unit_trace(short, 0), (3000.0, 1000.0))
    assert a_det is not None and a_short is not None
    assert a_short < a_det


def test_destination_blocked_on_every_layer_stops_as_close_as_it_can_on_its_layer():
    """Q-001-03 / R-001-05 second clause (SPEC test 7): a `block` with h = 5 (all five layers
    blocked inside x 1750..2250, y 750..1250) and an order to its centre: the unit stops
    outside the footprint, as close as it can get on its own layer, with no layer change."""
    scn, res = _mover({"preset": "block", "h": 5}, goal=(2000.0, 1000.0))
    ut = unit_trace(res, 0)
    u = res.unit[0]
    assert u["layer"] == 1 and u["transitions"] == 0 and not ut.changing.any()
    outside = (u["x"] < 1750.0) or (u["x"] >= 2250.0) or (u["y"] < 750.0) or (u["y"] >= 1250.0)
    assert outside
    dist = float(np.hypot(u["x"] - 2000.0, u["y"] - 1000.0))
    assert 250.0 <= dist <= 350.0, "stopped %.0f from the destination" % dist


def test_destination_open_on_another_layer_auto_transitions():
    """Q-001-03 / R-001-05 first clause (positive control for the test above): the same `block`
    with h = 2 and the same destination: layer 3 is open there, so the unit changes layer and
    reaches the destination on layer 3."""
    scn, res = _mover({"preset": "block", "h": 2}, goal=(2000.0, 1000.0))
    u = res.unit[0]
    assert u["layer"] == 3 and u["transitions"] >= 1
    assert np.hypot(u["x"] - 2000.0, u["y"] - 1000.0) <= 30.0


# ---- test 8: slopes and walkers (R-001-06, R-001-07, R-004-06 to R-004-08) ---------------------

def _climb(base_type, sl, *, h=1, g=1, start_x=1800.0, kind="walk", max_ticks=900):
    """A walker (or flyer) `base_type` starting on layer g at (start_x, 1000), MOVE to (3200, 1000)
    on the plateau, over a `ramp` with slope length `sl`. An enemy parked on layer 5 far away."""
    scn = make_scenario(
        [grp("A", "climber", start_x, 1000.0, g, order="move", goal=[3200.0, 1000.0]),
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain={"preset": "ramp", "h": h, "sl": sl, "g": g},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": max_ticks, "stalemate_ticks": 6000})
    add_type(scn, "climber", base_type, movement_kind=kind)
    return scn


@pytest.mark.parametrize("base_type,sl,ticks", [
    ("raider", 600.0, 80), ("bastion", 600.0, 300), ("raider", 150.0, 20), ("bastion", 150.0, 75)])
def test_slope_traversal_time_is_length_over_speed(base_type, sl, ticks):
    """R-004-07 (SPEC test 8): a walker takes slope length / its own speed from mounting to
    dismounting, whatever its transition time: Raider (150) 80 ticks on a 600 slope and 20 on a
    150 slope, Bastion (40) 300 and 75, each within 1 tick. The on-slope window (trace bit2) is
    one contiguous run, and the walker finishes on the plateau layer."""
    res = runmod.run(_climb(base_type, sl), seed=0, trace=True)
    ut = unit_trace(res, 0)
    on = np.flatnonzero(ut.on_slope)
    assert len(on) > 0, "walker never mounted the slope"
    assert (np.diff(on) == 1).all()
    assert abs(len(on) - ticks) <= 1, "%d ticks on the slope, expected %d" % (len(on), ticks)
    assert res.unit[0]["layer"] == 2


def test_slope_eligibility_flips_at_the_midline():
    """R-004-06 (SPEC test 8, with Q-008-03 tables on for offsets -1, 0, +1 so range and damage
    would let either shooter fire): two long-range shooters, one on layer 1 and one on layer 2,
    with fire_requires_vision off to isolate eligibility, and a walker climbing a 600 slope. Below
    the midline only the layer-1 shooter fires at it; at and above, only the layer-2 one. Positive
    controls: each fires at the walker while it is off the slope on its own side, and the layer-2
    shooter fired at the layer-1 walker before it mounted (cross-layer fire is live)."""
    t = table9(m1=1, z=1, p1=1)
    scn = make_scenario(
        [grp("A", "climber", 1500.0, 1000.0, 1, order="move", goal=[3200.0, 1000.0]),
         grp("B", "sniper", 1900.0, 1500.0, 1),
         grp("B", "sniper", 2600.0, 1500.0, 2)],
        terrain={"preset": "ramp", "h": 1, "sl": 600.0},
        rules={"spawn_jitter": 0.0, "fire_requires_vision": 0, "range_mult": t, "dmg_mult": t},
        run={"max_ticks": 400, "stalemate_ticks": 6000})
    add_type(scn, "climber", "raider", movement_kind="walk")
    add_type(scn, "sniper", "raider", range=1500.0, dmg=0.05)
    res = runmod.run(scn, seed=0, trace=True)
    ut = unit_trace(res, 0)
    on = np.flatnonzero(ut.on_slope)
    assert len(on) > 0
    s0, s1 = int(on[0]), int(on[-1])
    m = s0 + int(np.flatnonzero(ut.layer[s0:s1 + 1] == 2)[0])   # first tick counted as upper layer
    assert abs((m - s0) - 40) <= 1, "midline reached after %d ticks, expected 40" % (m - s0)
    low, up = fire_ticks(res, 1), fire_ticks(res, 2)
    # lower-layer shooter: fires below the midline, silent at and above it, fires again once off the slope
    assert any_in(low, s0, m - 2)
    assert not any_in(low, m + 1, s1)
    assert any_in(low, s1 + 2, END)
    # upper-layer shooter: silent below the midline (despite having fired before mounting), fires at and above it
    assert any_in(up, 0, s0 - 2)
    assert not any_in(up, s0 + 1, m - 2)
    assert any_in(up, m + 1, s1)


def _turn_back(b_x0, b_goal):
    """A: walker raider (ATTACK_MOVE) starting at (1950, 1000) on layer 1 with the plateau goal
    (3200, 1000), mounting the 600-long slope at tick ~7 and climbing 7.5 units a tick. B: a
    pre_revealed decoy flyer on layer 2 moving along y = 1400 at 7.5 a tick, hp huge and damage
    negligible, out of A's range of 200. A chases B's position, so when B's xy crosses the slope's
    foot at x = 2000 the walker's goal flips from the plateau to the ground. B at x_0 = 2200
    crosses at tick ~27 (the walker is at t = 0.25); at x_0 = 2500 at tick ~67 (t = 0.75)."""
    t = table9(m1=1, z=1, p1=1)
    scn = make_scenario(
        [grp("A", "climber", 1950.0, 1000.0, 1, order="attack_move", goal=[3200.0, 1000.0]),
         grp("B", "decoy", b_x0, 1400.0, 2, order="move", goal=list(b_goal), pre_revealed=1)],
        terrain={"preset": "ramp", "h": 1, "sl": 600.0},
        rules={"spawn_jitter": 0.0, "range_mult": t, "dmg_mult": t},
        run={"max_ticks": 400, "stalemate_ticks": 6000})
    add_type(scn, "climber", "raider", movement_kind="walk")
    add_type(scn, "decoy", "raider", hp=1.0e6, dmg=0.01, speed=150.0)
    res = runmod.run(scn, seed=0, trace=True)
    return res, unit_trace(res, 0)


def test_turn_back_before_the_midline_has_not_changed_layer():
    """R-004-08 (SPEC test 8): a walker part-way up the slope whose goal reverses before the
    midline (here: its chase target's xy moves from the plateau to the ground at t = 0.25) turns
    back, dismounts at the bottom and ends on layer 1 with transitions 0; it never counted as
    layer 2 on the slope. Mechanism: ATTACK_MOVE chase of a pre_revealed mover, since the lab has
    no commands during a run (SPEC 13); see the report for the SPEC reading this relies on."""
    res, ut = _turn_back(2200.0, (800.0, 1400.0))
    assert ut.on_slope.any(), "walker never mounted the slope"
    assert res.unit[0]["transitions"] == 0
    assert res.unit[0]["layer"] == 1 and not ut.on_slope[-1]
    assert not (ut.layer == 2).any()


def test_turn_back_after_the_midline_has_changed_twice():
    """R-004-08 (SPEC test 8): the same reversal after the midline (B crosses the slope's foot at
    t = 0.75): the walker was counted as layer 2 on the slope, turns back, and ends on layer 1
    with transitions 2 (a unit that crosses the midline and comes back has changed twice)."""
    res, ut = _turn_back(2500.0, (800.0, 1400.0))
    assert (ut.layer[ut.on_slope] == 2).any()
    assert res.unit[0]["transitions"] == 2
    assert res.unit[0]["layer"] == 1 and not ut.on_slope[-1]


def test_no_reversal_walker_climbs_through_with_one_change():
    """R-004-08 control (positive case for the two turn-back tests): the same chase with the
    decoy staying on the plateau: the walker never turns back, ends on layer 2 on the plateau
    with transitions 1."""
    res, ut = _turn_back(2200.0, (3000.0, 1400.0))
    assert res.unit[0]["transitions"] == 1 and res.unit[0]["layer"] == 2
    assert res.unit[0]["x"] > 2600.0 and not ut.on_slope[-1]


def test_walker_at_a_barrier_with_no_slope_never_crosses_but_a_flyer_does():
    """R-001-07 (SPEC test 8): a walking raider ordered across a `barrier` (h = 2, no slope) with
    auto_transition on stands at the near edge on layer 1 with transitions 0 and never changes
    layer in place (negative). Positive control: the identical scenario with a flying raider
    crosses and, ordered to a point on layer 1, arrives back on layer 1 (Q-001-05 reading a2)."""
    _, walk = _mover({"preset": "barrier", "h": 2}, kind="walk")
    wu, ut = walk.unit[0], unit_trace(walk, 0)
    assert wu["layer"] == 1 and wu["transitions"] == 0 and wu["x"] < 1900.0
    assert not ut.changing.any() and not ut.on_slope.any()
    _, fly = _mover({"preset": "barrier", "h": 2}, kind="fly")
    assert fly.unit[0]["layer"] == 1 and fly.unit[0]["x"] > 2800.0 and fly.unit[0]["transitions"] == 2


def test_flyer_ignores_the_slope_and_crosses_by_timed_transfer():
    """R-001-07 / Q-004-04 (SPEC test 8): over a `ramp` (h = 1), a flying raider ordered from the
    ground to the plateau crosses by a timed transfer (changing flag set) and never rides the
    slope (bit2 never set); it arrives on layer 2. Positive control: a walking raider on the same
    order rides the slope (bit2 set) and its changing flag is set only while on the slope (it
    makes no timed transfer in place)."""
    fly = runmod.run(_climb("raider", 600.0, kind="fly", start_x=1500.0, max_ticks=700), seed=0, trace=True)
    walk = runmod.run(_climb("raider", 600.0, kind="walk", start_x=1500.0, max_ticks=700), seed=0, trace=True)
    f, w = unit_trace(fly, 0), unit_trace(walk, 0)
    assert f.changing.any() and not f.on_slope.any()
    assert fly.unit[0]["layer"] == 2 and fly.unit[0]["transitions"] >= 1
    assert w.on_slope.any()
    assert not (w.changing & ~w.on_slope).any()
    assert walk.unit[0]["layer"] == 2


def test_two_layer_slope_crosses_over_at_a_quarter_and_three_quarters():
    """R-001-06 / Q-004-05 reading (a3) (SPEC test 8): a `ramp` with h = 2 and g = 1 gives a slope
    from layer 1 to layer 3 (n = 2): cross-overs at t = 0.25 and 0.75. A walker (speed 150, 600
    long, 80 ticks) is on layer 1 for the first 20 on-slope ticks, layer 2 for the next 40 and
    layer 3 for the last 20 (each boundary within 1 tick), sets the changing flag throughout,
    and ends on layer 3 with transitions 2."""
    res = runmod.run(_climb("raider", 600.0, h=2), seed=0, trace=True)
    ut = unit_trace(res, 0)
    on = np.flatnonzero(ut.on_slope)
    assert abs(len(on) - 80) <= 1
    layers = ut.layer[on]
    first2 = int(np.flatnonzero(layers == 2)[0])
    first3 = int(np.flatnonzero(layers == 3)[0])
    assert layers[0] == 1
    assert abs(first2 - 20) <= 1, "layer 2 from slope tick %d, expected 20 (t = 0.25)" % first2
    assert abs(first3 - 60) <= 1, "layer 3 from slope tick %d, expected 60 (t = 0.75)" % first3
    assert set(np.unique(layers)) == {1, 2, 3}
    assert ut.changing[on].all()
    assert res.unit[0]["layer"] == 3 and res.unit[0]["transitions"] == 2


# ---- test 9: area damage by layer (Q-008-03, SPEC 5.5) -----------------------------------------

SIEGE_ON_LINE = 17.5 * 1.5   # bombard dmg x category_mult[siege][line] = 26.25 per same-layer hit


def _cluster(aoe, cross_fire=False):
    """A: bombard on layer 3 at (1000,1000). B: three vanguards 250 east of it, holding: one on
    layer 3 (the only one in direct targeting reach, id 1), one on layer 4 and one on layer 2,
    each 60 units from the first (inside the 150 splash radius)."""
    rules = {"spawn_jitter": 0.0, "aoe_layer_mult": aoe}
    if cross_fire:
        t = table9(m1=1, z=1, p1=1)
        rules.update(range_mult=t, dmg_mult=t)
    scn = make_scenario(
        [grp("A", "bombard", 1000.0, 1000.0, 3),
         grp("B", "vanguard", 1250.0, 1000.0, 3),
         grp("B", "vanguard", 1250.0, 1060.0, 4),
         grp("B", "vanguard", 1250.0, 940.0, 2)],
        rules=rules, run={"max_ticks": 130, "stalemate_ticks": 6000})
    return runmod.run(scn, seed=0)


def test_area_damage_hits_only_the_same_layer_when_off_layer_multiplier_is_zero():
    """Q-008-03 / SPEC 5.5 (SPEC test 9; may already pass on R0, which has same-layer area): a
    bombard shells a 3-unit cluster, aoe_layer_mult zero everywhere except the same layer. The
    same-layer unit takes the full 26.25 per shell; the neighbours on layers 4 and 2, inside the
    splash radius, take nothing."""
    res = _cluster(table9(z=1))
    n = res.shots[0]
    assert n >= 1
    hp = [u["hp"] for u in res.unit]
    assert hp[1] == pytest.approx(500.0 - n * SIEGE_ON_LINE)
    assert hp[2] == 500.0 and hp[3] == 500.0


def test_area_damage_reaches_off_layer_neighbours_when_the_multiplier_is_set():
    """Q-008-03 / SPEC 5.5 (positive twin of the test above): aoe_layer_mult 0.5 for one layer
    above and below (fire tables on for those offsets so targeting is unchanged: the same-layer
    unit is still the nearest target): the neighbours on layers 4 and 2 each take half of a
    shell, 13.125, per shell, and the same-layer unit still the full 26.25."""
    res = _cluster(table9(m1=0.5, z=1, p1=0.5), cross_fire=True)
    n = res.shots[0]
    assert n >= 1
    hp = [u["hp"] for u in res.unit]
    assert hp[1] == pytest.approx(500.0 - n * SIEGE_ON_LINE)
    assert hp[2] == pytest.approx(500.0 - n * SIEGE_ON_LINE * 0.5)
    assert hp[3] == pytest.approx(500.0 - n * SIEGE_ON_LINE * 0.5)


def _volley(n_bombards, cap):
    """n rapid bombards (interval 0.05 s: all fire on tick 0) against one 5000-hp vanguard, one tick.
    Returns (shots_by_A, damage taken by the target)."""
    scn = make_scenario(
        [grp("A", "rapid", 1000.0, 1000.0, 3, count=n_bombards),
         grp("B", "dummy", 1250.0, 1000.0, 3)],
        rules={"spawn_jitter": 0.0, "aoe_cap_mult": cap}, run={"max_ticks": 1, "stalemate_ticks": 6000})
    add_type(scn, "rapid", "bombard", interval_s=0.05)
    add_type(scn, "dummy", "vanguard", hp=5000.0)
    res = runmod.run(scn, seed=0)
    assert res.ticks == 1
    return res.shots[0], 5000.0 - res.unit[n_bombards]["hp"]


@pytest.mark.parametrize("n,cap,expected", [
    (4, 4.0, 4 * SIEGE_ON_LINE),     # four shells: exactly at the default cap, no clamp, nothing lost
    (5, 4.0, 4.0 * SIEGE_ON_LINE),   # five shells: clamped to 4.0 x one hit
    (4, 2.0, 2.0 * SIEGE_ON_LINE),   # positive control: the clamp bites at a lower cap
    (2, 4.0, 2 * SIEGE_ON_LINE),     # negative control: below the cap the hits simply add
])
def test_area_per_target_cap_holds_with_simultaneous_bombards(n, cap, expected):
    """SPEC 5.5 aoe_cap_mult (SPEC test 9): n bombards fire on the same tick at one target; the
    summed area damage it takes that tick is min(n, cap) hits of 26.25. Four bombards at the
    default 4.0 deal at most 4.0 x one hit; five are clamped to it; at cap 2.0 four are clamped
    to two hits; two bombards are not clamped at all."""
    shots, taken = _volley(n, cap)
    assert shots == n, "expected all %d bombards to fire on tick 0, got %d shots" % (n, shots)
    assert taken == pytest.approx(expected)
