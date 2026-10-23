"""Hard-body movement (SPEC.md section 5.10, "Units are hard bodies"; README 5: "units cannot overlap").

The rule under test: a step (full, then x, then y) is rejected when its destination lies closer than
r_i + r_j to another alive unit on the same effective layer (neither on a slope), unless the unit is
already that close and the step does not bring it nearer; then 8 separation passes per tick resolve
what is left. Body radius is 15 for every type, so two bodies touch at 30 and "overlapping" below
29 (r_i + r_j - 1.0).

Conventions:
- `overlapping pairs` = per tick, the number of alive, same-effective-layer pairs (neither on a
  slope) whose xy distance is below 29. Counted from the trace (positions are stored as float32).
- `spawn_jitter` is 0 wherever distances matter, so spawn geometry is exact.
- Units given a MOVE order do not fire; "dummy" units (hp 1e6, dmg 0.01) hold so that nothing dies
  and no body disappears from a count.
- Corridor geometry: preset `lane` with `ch` = 1 and `wt` = 20 on the default 80 x 40 grid of 50
  unit cells: the strip is columns 30..49 (x in [1500, 2500)) and the one-cell channel is row 20
  (y in [1000, 1050), centre line y = 1025). `h` = 1 blocks layer 1, so layer-1 walkers must use
  the channel.
- Column placement is along the facing: unit i of a facing-0 column sits at x_0 + (i - (n-1)/2) *
  spacing, so the highest index is the front. Every column here stays exactly on y = 1025, so a
  channel one cell wide holds it single file.

Expected today (soft bodies, only 1 separation pass): the "no overlap", queue, reach-bound and
head-on tests are red; the different-layer control, the slope guard, determinism, regression and
metric-sanity tests are guards that pass on both builds (see each docstring).

SPEC gaps filled here (so the Doer and Architect see them):
- Throughput of a one-body-wide corridor: with every gap at least 29 (body 30 minus the 1.0
  tolerance) and speed 150 (7.5 per tick), the last of 10 exits at least 9 * 29 / 7.5 = 34.8 ticks
  after the first. Asserted as >= 33 (one tick of crossing-detection slack each side).
- A cell 50 wide is wider than a body (30), so two bodies could in principle pass abreast inside a
  1-cell channel if pushed off the centre line. The tests keep every channel unit exactly on the
  centre line (dy = 0), where the SPEC gives pure x pushes; behavior off the centre line is not
  pinned. The "wider channel exits sooner" twin therefore starts from a 5-wide box, not a column
  (a column on the centre line never uses the extra width, so it would not differ).
- A MOVE order to a point cannot be satisfied by more than one unit (arrival is within 22.5 and
  bodies are 30 wide). The tests treat "stands blocked behind another body" as legal, and the
  queue test measures exits past the strip, not arrival.
- SPEC says nothing about a unit standing exactly on a slope's bottom edge centre: the walker could
  not get within the 25 mount radius. The slope test therefore stands the layer-1 body 15 east of
  the edge centre, where the walker can still mount from the west.
"""
import time

import numpy as np

import layerlab.run as runmod
from conftest import LAB, add_type, grp, make_scenario, unit_trace
from layerlab import scenario
from layerlab.ffi import WIN_A, WIN_B, WIN_CAP, WIN_STALEMATE

R = 15.0
OVERLAP_BELOW = 2 * R - 1.0       # 29: closer than this counts as overlapping
TOUCH = 2 * R                     # 30
STRIP_L, STRIP_R = 1500.0, 2500.0  # x range of the lane strip (wt 20, cx 40, cell 50)
MID_Y = 1025.0                    # centre line of the 1-cell channel
SPEED_PER_TICK = 150.0 * 0.05     # 7.5


# ---- helpers -----------------------------------------------------------------------------------

def _pair_arrays(res):
    """(d, valid) for the trace: d[t, i, j] xy distance, valid[t, i, j] True for i < j pairs that are
    both alive, on the same effective layer, and neither on a slope (SPEC 5.10)."""
    tr = res.trace
    x, y = tr["x"].astype(np.float64), tr["y"].astype(np.float64)
    alive = tr["alive"].astype(bool)
    layer = tr["layer"].astype(int)
    slope = (tr["flags"] & 4) != 0
    d = np.hypot(x[:, :, None] - x[:, None, :], y[:, :, None] - y[:, None, :])
    ok = alive & ~slope
    valid = ok[:, :, None] & ok[:, None, :] & (layer[:, :, None] == layer[:, None, :])
    n = x.shape[1]
    valid &= np.triu(np.ones((n, n), dtype=bool), k=1)[None, :, :]
    return d, valid


def overlapping_pairs(res, below=OVERLAP_BELOW):
    """Per tick, the number of same-layer alive pairs whose distance is below `below` (29)."""
    d, valid = _pair_arrays(res)
    return ((d < below) & valid).sum(axis=(1, 2))


def overlap_total(res):
    """Per tick, the summed penetration depth (30 - d) over the pairs closer than 30."""
    d, valid = _pair_arrays(res)
    return np.where(valid & (d < TOUCH), TOUCH - d, 0.0).sum(axis=(1, 2))


def _first_tick(mask_t):
    """First tick index where the bool array is True, or -1."""
    hit = np.flatnonzero(mask_t)
    return int(hit[0]) if len(hit) else -1


def _walker(scn, name="walker", base="raider"):
    return add_type(scn, name, base, movement_kind="walk")


def _post(scn):
    """A dummy that never dies and never hurts: hp 1e6, dmg 0.01."""
    return add_type(scn, "post", "raider", hp=1.0e6, dmg=0.01, movement_kind="walk")


# ---- test 1: open field, no overlap ------------------------------------------------------------

def _open_field(spacing, order, goal=None, n=20, ticks=300):
    kw = {"order": order}
    if goal is not None:
        kw["goal"] = list(goal)
    scn = make_scenario(
        [grp("A", "raider", 1000.0, 1000.0, 3, count=n, formation="box", cols=5, spacing=spacing, **kw),
         grp("B", "raider", 3900.0, 150.0, 5)],      # a parked enemy so the run has both sides
        rules={"spawn_jitter": 0.0}, run={"max_ticks": ticks, "stalemate_ticks": 6000})
    return runmod.run(scn, seed=0, trace=True)


def test_open_field_twenty_raiders_ordered_to_one_point_never_overlap():
    """SPEC 5.10 hard bodies, README 5 (positive): 20 raiders in a 5-wide box (spacing 37.5, all
    clear of each other) given a MOVE order to one point 600 away on flat ground: after the first 5
    ticks the maximum overlapping pairs over the whole run is 0. Red today because the soft build
    lets the whole group converge on the goal point. Guard against the cheap fix (never move): the
    front unit does reach the goal (within 1.5 body radii)."""
    res = _open_field(37.5, "move", goal=(1600.0, 1000.0))
    op = overlapping_pairs(res)
    assert op[5:].max() == 0, "max overlapping pairs %d, first at tick %d" % (op[5:].max(), 5 + _first_tick(op[5:] > 0))
    tr = res.trace
    n = 20
    dist_goal = np.hypot(tr["x"][:, :n].astype(float) - 1600.0, tr["y"][:, :n].astype(float) - 1000.0)
    assert dist_goal.min() <= 1.5 * R + 1.0, "nobody reached the goal: the group stood still"


def test_open_field_metric_sanity_spawn_overlap_is_counted():
    """Positive control for the detector: units spawned 20 apart (hold, no motion) are overlapping
    pairs at tick 0 under the same helper (so a 0 elsewhere is a real 0). Guard: passes today."""
    res = _open_field(20.0, "hold")
    assert overlapping_pairs(res)[0] > 0 or overlap_total(res)[0] > 0
    assert overlap_total(res)[0] > 0


def test_existing_overlap_is_resolved_within_20_ticks_and_never_made_worse():
    """SPEC 5.10 (an overlap that exists is never made worse and can be resolved; 8 separation
    passes per tick): 20 units spawned overlapping (box spacing 20, hold orders so only separation
    acts). The summed penetration never increases from one tick to the next (1e-3 slack for float32
    trace) and there are no overlapping pairs from tick 20 on. May already pass today with the
    one-pass separation; it guards the new build."""
    res = _open_field(20.0, "hold")
    tot = overlap_total(res)
    assert tot[0] > 0, "fixture: nothing overlaps at spawn"
    assert (np.diff(tot) <= 1e-3).all(), "total overlap grew at tick %d" % (1 + _first_tick(np.diff(tot) > 1e-3))
    op = overlapping_pairs(res)
    assert op[20:].max() == 0, "still overlapping at tick %d" % (20 + _first_tick(op[20:] > 0))


def test_existing_overlap_is_never_made_worse_while_moving():
    """Same rule with a MOVE order (the step rule, not just separation, is in play): units spawned
    20 apart and sent 600 away. The overlap present at spawn is gone within 20 ticks and, after the
    first 5 ticks, no pair is ever below 29 again."""
    res = _open_field(20.0, "move", goal=(1600.0, 1000.0))
    op = overlapping_pairs(res)
    assert op[20:].max() == 0, "overlap at tick %d" % (20 + _first_tick(op[20:] > 0))


# ---- test 2: the corridor queue ----------------------------------------------------------------

def _corridor(ch, *, start="column", spacing=37.5, n=10, ticks=1200, jitter=0.0, goal_x=2900.0,
              extra=()):
    kw = dict(formation="column", spacing=spacing) if start == "column" else dict(
        formation="box", cols=5, spacing=spacing)
    scn = make_scenario(
        [grp("A", "walker", 1000.0, MID_Y, 1, count=n, order="move", goal=[goal_x, MID_Y], **kw),
         *extra,
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain={"preset": "lane", "ch": ch, "wt": 20, "h": 1},
        rules={"spawn_jitter": jitter}, run={"max_ticks": ticks, "stalemate_ticks": 6000})
    _walker(scn)
    _post(scn)
    return scn


def _exit_entry(res, n=10):
    """Per A unit (index 0..n-1): first tick with x >= strip start and first tick with x > strip
    end, or -1."""
    x = res.trace["x"][:, :n].astype(float)
    ent = np.array([_first_tick(x[:, i] >= STRIP_L) for i in range(n)])
    ext = np.array([_first_tick(x[:, i] > STRIP_R) for i in range(n)])
    return ent, ext


def test_corridor_ten_walkers_queue_without_overlap_and_all_exit_in_order():
    """SPEC 5.10 ("a column of units in a corridor one body wide therefore queues"), `lane` ch 1,
    wt 20, h 1: ten walking raiders in a column on layer 1 left of the strip, MOVE to a point 400
    beyond its right end. Positive: at no tick are two units closer than 29 (red today: the soft
    build lets the column pile up at the goal); no unit is ever outside the channel cells while its
    x is inside the strip (the existing blocked-cell rule); all ten are beyond the strip within 1200
    ticks; arrival order equals entry order (a queue, strictly: entry ticks are at least 3 apart
    for bodies 30 apart at 7.5 a tick)."""
    res = runmod.run(_corridor(1), seed=0, trace=True)
    op = overlapping_pairs(res)
    assert op.max() == 0, "overlapping pairs %d first at tick %d" % (op.max(), _first_tick(op > 0))
    tr = res.trace
    x, y = tr["x"][:, :10].astype(float), tr["y"][:, :10].astype(float)
    inside = (x >= STRIP_L) & (x < STRIP_R)
    assert inside.any(), "nobody entered the strip"
    assert ((y[inside] >= 1000.0) & (y[inside] < 1050.0)).all(), "a unit stood outside the channel cells"
    ent, ext = _exit_entry(res)
    assert (ent >= 0).all() and (ext >= 0).all(), "not every unit got through: entered %s exited %s" % (ent, ext)
    assert list(np.argsort(ent, kind="stable")) == list(np.argsort(ext, kind="stable")), \
        "exit order %s differs from entry order %s" % (np.argsort(ext, kind="stable"), np.argsort(ent, kind="stable"))
    assert list(np.argsort(ent, kind="stable")) == list(range(9, -1, -1)), "front of the column enters first"


def _span(res):
    _, ext = _exit_entry(res)
    assert (ext >= 0).all(), "not every unit exited: %s" % ext
    return int(ext.max() - ext.min())


def test_corridor_throughput_is_bounded_by_body_size():
    """SPEC 5.10 / README 6.2 choke: ten walkers from a 5-wide box (spacing 37.5, so they arrive at
    the channel mouth together) cannot leave a one-body-wide corridor faster than single file: from
    the first exit to the last is bounded by body size. The channel cell is 50 wide and a body 30
    across, so the 20 units of lateral room let a column stagger: consecutive bodies then sit
    sqrt(30^2 - 20^2) = 22.4 apart along x (they still never touch: minimum pair distance 30.0), so
    9 gaps * 22.4 / 7.5 = 26.8 ticks is the floor (asserted >= 25). A strict single file would need
    9 * 29 / 7.5 = 34.8 ticks; that was this test's first bound and ignored the stagger (test defect
    found by the sidestep builder: measured 31). Red with the soft build: exits within about 18 ticks."""
    span = _span(runmod.run(_corridor(1, start="box"), seed=0, trace=True))
    assert span >= 25, "first to last exit took %d ticks, a staggered column of 10 bodies needs >= 26.8" % span


def test_corridor_overlapping_column_still_leaves_single_file():
    """Throughput bound from an overlapping start: ten walkers spawned 15 apart in a column (centre
    line, dy = 0) are pushed apart to body spacing and leave at least 33 ticks apart first to last.
    Guard: the soft build's one separation pass also gets there (35 ticks), so this passes today."""
    span = _span(runmod.run(_corridor(1, spacing=15.0), seed=0, trace=True))
    assert span >= 33, "first to last exit took %d ticks" % span


def test_corridor_wider_channel_lets_a_crowd_out_sooner():
    """Negative twin of the throughput bound: the same ten walkers (5-wide box, spacing 37.5, so
    the width matters) leave an 8-cell channel (rows 16..23, 400 wide) sooner than a 1-cell one:
    the last unit's exit tick is smaller with ch 8 than with ch 1 (a unit that never exits counts as
    the end of the run). Positive control that the 1-cell result is the choke and not slow
    walkers."""
    last = {}
    for ch in (1, 8):
        res = runmod.run(_corridor(ch, start="box", spacing=37.5), seed=0, trace=True)
        _, ext = _exit_entry(res)
        last[ch] = 1200 if (ext < 0).any() else int(ext.max())
    assert last[8] < last[1], "ch 8 finished at tick %d, ch 1 at tick %d" % (last[8], last[1])
    assert last[8] < 1200, "even the 8-cell channel did not clear"


# ---- test 3: reach bound -----------------------------------------------------------------------

def _within_200(res, defender, n_att):
    tr = res.trace
    x, y = tr["x"].astype(float), tr["y"].astype(float)
    alive = tr["alive"].astype(bool)
    d = np.hypot(x[:, :n_att] - x[:, [defender]], y[:, :n_att] - y[:, [defender]])
    return ((d <= 200.0) & alive[:, :n_att]).sum(axis=1)


def test_reach_bound_one_cell_corridor_holds_at_most_seven_within_200():
    """SPEC 5.10 (the number of units that can be within reach of a point is bounded by the space
    around it), README 6.2: a defender (dummy) holds at (2450, 1025) inside the 1-cell corridor; 20
    attackers (walkers, column spacing 37.5, MOVE onto the defender's point) pile up behind it. At
    every tick at most 7 attackers are within 200 of the defender (200 / 30 = 6.67 bodies fit in a
    200-long, one-body-wide corridor). Red today: the soft build stacks 15 or more on the point."""
    scn = make_scenario(
        [grp("A", "walker", 1000.0, MID_Y, 1, count=20, formation="column", spacing=37.5,
             order="move", goal=[2450.0, MID_Y]),
         grp("B", "post", 2450.0, MID_Y, 1)],
        terrain={"preset": "lane", "ch": 1, "wt": 20, "h": 1},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 700, "stalemate_ticks": 6000})
    _walker(scn)
    _post(scn)
    res = runmod.run(scn, seed=0, trace=True)
    near = _within_200(res, 20, 20)
    assert near.max() >= 2, "fixture: the attackers never reached the defender (max within 200: %d)" % near.max()
    assert near.max() <= 7, "%d attackers within 200 of the defender at tick %d" % (near.max(), int(near.argmax()))


def test_reach_open_arena_twenty_attackers_all_get_within_200():
    """Positive twin of the reach bound: with room (flat arena, same 20 attackers and the same
    MOVE-onto-the-defender order) more than 10 attackers are within 200 of the defender at some tick
    (about 150 bodies fit in a 200-radius disc, so all 20 should). Guard: passes today and stays
    green; it shows the corridor's 7 is the corridor and not a general cap."""
    scn = make_scenario(
        [grp("A", "walker", 800.0, 1000.0, 1, count=20, formation="box", cols=5, spacing=37.5,
             order="move", goal=[1400.0, 1000.0]),
         grp("B", "post", 1400.0, 1000.0, 1)],
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 400, "stalemate_ticks": 6000})
    _walker(scn)
    _post(scn)
    res = runmod.run(scn, seed=0, trace=True)
    assert _within_200(res, 20, 20).max() > 10


# ---- test 4: enemies are bodies, other layers are not ------------------------------------------

def test_opposing_lines_on_one_layer_never_overlap_after_tick_5():
    """SPEC 5.10 (any alive unit on the same effective layer, either side): five raiders on a MOVE
    order walk at five dummy holders on the same layer. After the first 5 ticks no pair of any
    sides is below 29 (the mover stops against the holder). Red today: the soft build walks
    straight through. Guard: the movers did advance (closest approach of an A unit to the line
    centre x = 1600 is under 120), so standing still does not pass."""
    scn = make_scenario(
        [grp("A", "raider", 1000.0, 1000.0, 3, count=5, formation="line", spacing=37.5,
             order="move", goal=[2400.0, 1000.0]),
         grp("B", "post", 1600.0, 1000.0, 3, count=5, formation="line", spacing=37.5, facing=180.0)],
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 300, "stalemate_ticks": 6000})
    _post(scn)
    res = runmod.run(scn, seed=0, trace=True)
    op = overlapping_pairs(res)
    assert op[5:].max() == 0, "overlapping pairs %d first at tick %d" % (op[5:].max(), 5 + _first_tick(op[5:] > 0))
    ax = res.trace["x"][:, :5].astype(float)
    assert 1600.0 - ax.max() < 120.0, "movers never closed on the holders (front at x=%.0f)" % ax.max()


def _two_unit_pass(layer_a, layer_b):
    scn = make_scenario(
        [grp("A", "raider", 1000.0, 1000.0, layer_a, order="move", goal=[2000.0, 1000.0]),
         grp("B", "raider", 2000.0, 1000.0, layer_b, order="move", goal=[1000.0, 1000.0])],
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 300, "stalemate_ticks": 6000})
    res = runmod.run(scn, seed=0, trace=True)
    a, b = unit_trace(res, 0), unit_trace(res, 1)
    return np.hypot(a.x - b.x, a.y - b.y)


def test_units_on_different_layers_pass_through_each_other():
    """SPEC 5.10 (blocking and separation only apply on the same effective layer), positive control:
    a layer-3 unit and a layer-4 unit walking through each other's xy (head on, 150 a second each)
    come within 10 of each other at some tick. Guard: passes today and must stay green."""
    assert _two_unit_pass(3, 4).min() < 10.0


def test_same_layer_head_on_pair_stops_at_body_contact():
    """Negative twin of the layer pass-through: the identical head-on pair on ONE layer never gets
    closer than 29 at any tick. Red today (they pass through at distance ~0)."""
    assert _two_unit_pass(3, 3).min() >= OVERLAP_BELOW


# ---- test 5: a unit on a slope is neither blocked nor pushed -----------------------------------

def test_walker_on_a_slope_is_not_blocked_by_bodies_on_its_layers():
    """SPEC 5.10 ("neither on a slope") and 5.9 (no separation push on a slope): a walking raider
    climbs the 600 `ramp` slope (MOVE to the plateau) with a dummy standing on layer 1 at (1990,
    1000), 15 east of the bottom edge centre (the walker mounts from the west, 17.5 from the
    centre, and is placed 15 from that body), and a dummy on layer 2 at (2425, 1000) under the
    slope's upper part (the walker is counted layer 2 there). It is on the slope for 80 ticks (+-1)
    at its own speed, ends on the plateau, and neither standing body moves. Guard: passes today."""
    scn = make_scenario(
        [grp("A", "walker", 1800.0, 1000.0, 1, order="move", goal=[3200.0, 1000.0]),
         grp("B", "post", 1990.0, 1000.0, 1),
         grp("B", "post", 2425.0, 1000.0, 2)],
        terrain={"preset": "ramp", "h": 1, "sl": 600.0, "g": 1},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 900, "stalemate_ticks": 6000})
    _walker(scn)
    _post(scn)
    res = runmod.run(scn, seed=0, trace=True)
    ut = unit_trace(res, 0)
    on = np.flatnonzero(ut.on_slope)
    assert len(on) > 0, "the walker never mounted the slope"
    assert abs(len(on) - 80) <= 1, "%d ticks on the slope, expected 80" % len(on)
    assert (np.diff(on) == 1).all()
    assert (ut.layer[ut.on_slope] == 2).any(), "the walker was never counted as layer 2 on the slope"
    assert res.unit[0]["layer"] == 2 and res.unit[0]["x"] > 2600.0
    for i, (px, py) in ((1, (1990.0, 1000.0)), (2, (2425.0, 1000.0))):
        u = res.unit[i]
        assert abs(u["x"] - px) < 1e-3 and abs(u["y"] - py) < 1e-3, "standing unit %d was pushed to %s" % (i, (u["x"], u["y"]))


# ---- test 6: determinism and the deadlock ------------------------------------------------------

def _crowd(jitter=10.0):
    """A crowded corridor run with random spawn jitter: 10 walkers from a 5-wide box and a dummy."""
    return _corridor(1, start="box", spacing=37.5, ticks=500, jitter=jitter,
                     extra=[grp("B", "post", 2450.0, MID_Y, 1)])


def _tb(res):
    return res.trace.tobytes()


def test_crowd_same_seed_twice_is_byte_identical_and_seeds_differ():
    """Determinism contract: the same crowded run twice (same seed, spawn jitter on) gives identical
    `raw` and trace bytes. Negative twin: another seed gives different trace bytes (the jitter is
    live, so identical bytes above are not a dead detector). Guard: passes today."""
    a = runmod.run(_crowd(), seed=3, trace=True)
    b = runmod.run(_crowd(), seed=3, trace=True)
    assert a.raw == b.raw and _tb(a) == _tb(b)
    c = runmod.run(_crowd(), seed=4, trace=True)
    assert _tb(a) != _tb(c)


def test_crowd_is_identical_across_optimisation_levels():
    """E-01 R-004-05 determinism across builds: the O0 and O2 libraries give identical `raw` and
    trace bytes on the crowded corridor, seeds 0..2. Guard: passes today."""
    for seed in range(3):
        a = runmod.run(_crowd(), seed=seed, trace=True, lib="O0")
        b = runmod.run(_crowd(), seed=seed, trace=True, lib="O2")
        assert a.raw == b.raw, "raw differs O0 vs O2 at seed %d" % seed
        assert _tb(a) == _tb(b), "trace differs O0 vs O2 at seed %d" % seed


def test_head_on_columns_in_a_one_cell_corridor_deadlock_without_error():
    """DOCUMENTED DEADLOCK: two columns of ten walkers, one on each side of a 1-cell corridor, each
    ordered to the far side, meet head-on in it. Bodies cannot pass and nothing breaks the tie (all
    pushes are along x; both fronts stay exactly on y = 1025), so the fronts stand 29..30 apart for
    the rest of the run. Only damage resets the stalemate clock, and nobody fires on MOVE orders,
    so the run ends STALEMATE (tick 400) or CAP, not an error, in under 5 seconds. Assert the
    deadlock itself: every A unit is still west of every B unit at the end (nobody swapped sides).
    Red today: the soft build lets the columns walk through each other."""
    scn = make_scenario(
        [grp("A", "walker", 700.0, MID_Y, 1, count=10, formation="column", spacing=37.5,
             order="move", goal=[3400.0, MID_Y]),
         grp("B", "walker", 3300.0, MID_Y, 1, count=10, formation="column", spacing=37.5, facing=180.0,
             order="move", goal=[600.0, MID_Y])],
        terrain={"preset": "lane", "ch": 1, "wt": 20, "h": 1},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 800, "stalemate_ticks": 400})
    _walker(scn)
    t0 = time.perf_counter()
    res = runmod.run(scn, seed=0, trace=True)
    elapsed = time.perf_counter() - t0
    assert elapsed < 5.0, "the deadlocked crowd took %.1f s" % elapsed
    assert res.winner in (WIN_STALEMATE, WIN_CAP)
    assert res.survivors == (10, 10)
    xs = [u["x"] for u in res.unit]
    assert max(xs[:10]) < min(xs[10:]), "the columns passed through each other: A max x %.0f, B min x %.0f" % (max(xs[:10]), min(xs[10:]))
    assert overlapping_pairs(res).max() == 0


# ---- test 7: no regression ---------------------------------------------------------------------

def test_ten_v_five_raiders_a_still_wins_every_seed():
    """README 5 positive control (scenarios/r0_raiders_10v5.toml): A (10) beats B (5), 20 of 20
    seeds 0..19, with hard bodies in the line-on-line fight. Guard: passes today."""
    scn = scenario.load(str(LAB / "scenarios" / "r0_raiders_10v5.toml"))
    wins = sum(runmod.run(scn, seed=s).winner == WIN_A for s in range(20))
    assert wins == 20, "A won %d of 20" % wins


def test_ten_v_ten_mirror_still_splits_the_winners():
    """README 5 noise floor (scenarios/x0_mirror.toml): identical 10 v 10, seeds 0..199: each side
    wins at least 60 of 200 (hard bodies must not hand the fight to one side by index order or
    geometry). Guard: passes today."""
    scn = scenario.load(str(LAB / "scenarios" / "x0_mirror.toml"))
    win = [runmod.run(scn, seed=s).winner for s in range(200)]
    a, b = win.count(WIN_A), win.count(WIN_B)
    assert a >= 60 and b >= 60, "A won %d, B won %d of 200" % (a, b)
