"""Slope mouth at lower walking speeds (SPEC.md 5.9 "Mounting is never blocked by bodies", 5.10
"Slope mouths", LL_MOUTH_RADIUS 40).

Bug under test (found in E3, no fighting needed): on the `ramp` preset, 10 walking raiders in a 5-wide box
(spacing 31) at (900, 1000) on layer 1, ordered to a plateau point beyond the slope's top, with the lab's
default spawn_jitter 10, do not all climb at low speed. At speed 150 all 10 reach layer 2 on every seed;
at speed 80 only 1 to 10 do and at speed 40 only 3 to 10 do. Two units a body width apart at the slope
entry (whose centre, (1975, 1000), lies on a flow-field cell boundary at y = 1000) each wait for the
other. This is the sibling of tests/test_slope_mouth.py, which uses speed 150 and spawn_jitter 0 and is
green; here the speeds and the jitter are the variables.

Geometry: ramp x1 40, sl in (300, 600), sw 200, g 1, h 1. Bottom edge centre (1975, 1000), top edge centre
(1975 + sl, 1000) on the plateau (layer 2). Plateau goal (1975 + sl + 60, 1000). Walkers are `raider` copies
with movement_kind walk and the speed under test. One inert enemy raider on layer 5 at (3900, 150) so the
run has both sides (a side with no units loses at once, SPEC 5.11); same-layer-only fire keeps it inert.
Attackers are unit indices 0..9, the enemy is index 10.

Conventions:
- Overlap = same-effective-layer alive pairs (neither on a slope) closer than 29, as in test_bodies.py.
- When all units have climbed and nothing else happens, the lab ends by stalemate at stalemate_ticks (3000)
  even on success, so "finishes on time" is not read from the run length; test 2 asserts positions by tick
  1500 instead.

Expected today: test 1 red at speeds 40 and 80, green at 150 (positive control); test 2 red; tests 3 and 4
are gated on every unit having climbed, so they are red wherever the climb fails and otherwise guard
hard bodies off the mouth and the clearing of the mouth overlap.

SPEC gaps filled here:
- "Overlap inside the mouth may exceed 0" is an allowance, not a requirement (SPEC 5.10: bodies inside the
  mouth neither block nor are pushed), so test 4 asserts only the clearing, and prints the maximum.
- The slope's bottom edge centre and top edge centre are derived from the preset geometry in the module
  docstring above, not read from the library.
"""
import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, grp, make_scenario, unit_trace

R = 15.0
OVERLAP_BELOW = 2 * R - 1.0           # 29
N = 10
SEEDS = range(10)
BOTTOM = (1975.0, 1000.0)
MOUTH_FAR = 60.0                      # "away from the mouth": farther than this from the edge centre
MAX_TICKS = 3000


# ---- helpers -----------------------------------------------------------------------------------

def _ramp(sl):
    return {"preset": "ramp", "x1": 40, "sl": float(sl), "sw": 200.0, "g": 1, "h": 1}


def _top(sl):
    return (1975.0 + sl, 1000.0)


def _scn(speed, sl, order):
    """Ten walkers, default spawn_jitter (10, not overridden), an inert enemy on layer 5."""
    groups = [grp("A", "walker", 900.0, 1000.0, 1, count=N, formation="box", cols=5, spacing=31.0,
                  order=order, goal=[1975.0 + sl + 60.0, 1000.0]),
              grp("B", "raider", 3900.0, 150.0, 5)]
    scn = make_scenario(groups, terrain=_ramp(sl),
                        run={"max_ticks": MAX_TICKS, "stalemate_ticks": MAX_TICKS})
    return add_type(scn, "walker", "raider", movement_kind="walk", speed=float(speed))


def _run(speed, sl, seed, order="move", trace=True):
    return runmod.run(_scn(speed, sl, order), seed=seed, trace=trace)


def _pairs(res, units):
    """(d, valid) over the given unit indices: d[t, i, j] xy distance; valid[t, i, j] for i < j,
    both alive, same effective layer, neither on a slope."""
    tr = res.trace[:, units]
    x, y = tr["x"].astype(np.float64), tr["y"].astype(np.float64)
    ok = tr["alive"].astype(bool) & ((tr["flags"] & 4) == 0)
    layer = tr["layer"].astype(int)
    d = np.hypot(x[:, :, None] - x[:, None, :], y[:, :, None] - y[:, None, :])
    valid = ok[:, :, None] & ok[:, None, :] & (layer[:, :, None] == layer[:, None, :])
    n = len(units)
    valid &= np.triu(np.ones((n, n), dtype=bool), k=1)[None, :, :]
    return d, valid


def _dist_to(res, units, point):
    tr = res.trace[:, units]
    return np.hypot(tr["x"].astype(np.float64) - point[0], tr["y"].astype(np.float64) - point[1])


def _first_mount(res, i):
    on = np.flatnonzero(unit_trace(res, i).on_slope)
    return int(on[0]) if len(on) else None


def _last_dismount(res):
    """Last tick (+1) any attacker has trace flag bit2 (on a slope); None if none ever mounted."""
    on = np.flatnonzero((res.trace["flags"][:, :N] & 4 > 0).any(axis=1))
    return int(on.max()) + 1 if len(on) else None


def _all_climbed(res):
    return [i for i in range(N) if not (res.unit[i]["alive"] and res.unit[i]["layer"] == 2
                                        and res.unit[i]["transitions"] >= 1)]


# ---- test 1: all ten climb, every seed, every speed --------------------------------------------

@pytest.mark.parametrize("order", ["attack_move", "move"])
@pytest.mark.parametrize("sl", [300, 600])
@pytest.mark.parametrize("speed", [40, 80, 150])
def test_all_ten_walkers_climb_at_every_speed_and_seed(speed, sl, order):
    """SPEC 5.9 / 5.10 slope mouths (red today at speeds 40 and 80, 150 is the positive control that the
    scenario, the helpers and the climb are sound): for seeds 0..9 every one of the 10 attackers ends
    alive on layer 2 with at least one layer change."""
    bad = {}
    for seed in SEEDS:
        res = _run(speed, sl, seed, order, trace=False)
        stuck = _all_climbed(res)
        if stuck:
            bad[seed] = len(stuck)
    assert not bad, "seed -> number of attackers not on layer 2 (speed %s, sl %s, %s): %s" % (
        speed, sl, order, bad)


# ---- test 2: the climb is not just late, it is done by tick 1500 -------------------------------

def test_every_attacker_is_on_layer_two_by_tick_1500_at_speed_40():
    """SPEC 5.9 (red today where a pair deadlocks at the entry): speed 40, sl 600, seed 0. The slope is 600
    long, 300 ticks at speed 40 (R-004-07); ten walkers one at a time through the mouth have all landed
    well before tick 1500. Asserted on the trace at tick 1500, not on run length (a successful run still
    ends by stalemate at 3000)."""
    res = _run(40, 600, 0, "move")
    t = 1500
    assert len(res.trace) > t
    lay = res.trace["layer"][t, :N].astype(int)
    alive = res.trace["alive"][t, :N].astype(bool)
    on_slope = (res.trace["flags"][t, :N] & 4) > 0
    off = [i for i in range(N) if not (alive[i] and lay[i] == 2 and not on_slope[i])]
    assert not off, "attackers not on layer 2 (off the slope) at tick %d: %s (layers %s)" % (
        t, off, lay[:N].tolist())


# ---- test 3: hard bodies still hold away from the mouths ---------------------------------------

@pytest.mark.parametrize("speed", [40, 80, 150])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_hard_bodies_hold_on_layer_one_away_from_the_slope_mouth(speed, seed):
    """SPEC 5.10 (guard: the mouth exemption must not become general overlap): on layer 1, for pairs both
    farther than 60 from the bottom edge centre, no two units are closer than 29 after tick 20 (spawn
    jitter and the box's 31 spacing are resolved by then). sl 300, move order. Not gated on the climb:
    this is the layer-1 guard and holds, and must keep holding, whether or not units mount."""
    res = _run(speed, 300, seed, "move")
    units = list(range(N))
    d, valid = _pairs(res, units)
    lay = res.trace[:, units]["layer"].astype(int)
    far = _dist_to(res, units, BOTTOM) > MOUTH_FAR
    ok = valid & ((lay == 1)[:, :, None] & (lay == 1)[:, None, :]) \
        & far[:, :, None] & far[:, None, :]
    bad = (d < OVERLAP_BELOW) & ok
    bad[:21] = False
    ticks = np.flatnonzero(bad.any(axis=(1, 2)))
    assert len(ticks) == 0, "layer-1 overlap away from the mouth at ticks %s" % ticks[:5]


@pytest.mark.parametrize("speed", [40, 80, 150])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_hard_bodies_hold_on_layer_two_away_from_the_top_edge_after_the_climb(speed, seed):
    """SPEC 5.10 (red today wherever someone never climbs; the climb is asserted first so a no-climb run
    cannot pass vacuously): on layer 2, for pairs both farther than 60 from the top edge centre, no two
    off-slope units are closer than 29 from 60 ticks after the last dismount (the last tick any attacker
    has trace flag bit2). sl 300, move order."""
    res = _run(speed, 300, seed, "move")
    stuck = _all_climbed(res)
    assert not stuck, "attackers that never climbed: %s" % stuck
    last = _last_dismount(res)
    units = list(range(N))
    d, valid = _pairs(res, units)
    lay = res.trace[:, units]["layer"].astype(int)
    far = _dist_to(res, units, _top(300)) > MOUTH_FAR
    ok = valid & ((lay == 2)[:, :, None] & (lay == 2)[:, None, :]) \
        & far[:, :, None] & far[:, None, :]
    bad = (d < OVERLAP_BELOW) & ok
    start = last + 60
    assert start < len(bad)
    ticks = start + np.flatnonzero(bad[start:].any(axis=(1, 2)))
    assert len(ticks) == 0, "layer-2 overlap away from the top edge at ticks %s (last dismount %d)" % (
        ticks[:5], last)


# ---- test 4: overlap inside the mouth is allowed and clears ------------------------------------

@pytest.mark.parametrize("speed", [40, 80])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_overlap_inside_the_mouth_is_allowed_and_clears(speed, seed):
    """SPEC 5.10 slope mouths (red today wherever someone never mounts: the climb is asserted first):
    pairs on layer 1 both within 40 of the bottom edge centre may overlap (inside the mouth bodies neither
    block nor are pushed; the maximum is printed, not required to exceed 0), but the overlapping-pair
    count is 0 from 100 ticks after the last unit's first mount. sl 300, move order."""
    res = _run(speed, 300, seed, "move")
    stuck = _all_climbed(res)
    assert not stuck, "attackers that never climbed: %s" % stuck
    mounts = [_first_mount(res, i) for i in range(N)]
    assert all(m is not None for m in mounts)
    last_mount = max(mounts)
    units = list(range(N))
    d, valid = _pairs(res, units)
    lay = res.trace[:, units]["layer"].astype(int)
    near = _dist_to(res, units, BOTTOM) <= 40.0
    ok = valid & ((lay == 1)[:, :, None] & (lay == 1)[:, None, :]) \
        & near[:, :, None] & near[:, None, :]
    count = ((d < OVERLAP_BELOW) & ok).sum(axis=(1, 2))
    print("max mouth overlap pairs (speed %s, seed %s): %d" % (speed, seed, count.max()))
    start = last_mount + 100
    assert start < len(count)
    assert (count[start:] == 0).all(), "mouth overlap persists after tick %d: ticks %s" % (
        start, start + np.flatnonzero(count[start:] > 0)[:5])
