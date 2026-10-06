"""E-01 R-001-05 (a unit takes the route of least time, changing layer along the way; a blocked destination means it
paths as close as it can and stops) and E-13 R-097-09 (a unit inside a blocked cell moves to the nearest open one):
a flying unit routed up over a mass blocked on its home layer must come back down to its home layer, never strand on
layer 4 above a cell that is blocked on its home layer.

Measured defect (skill lab 2026-10-06, csrc/tactical_move.c, om_move_across_plan / om_move_layer_unit `transit`,
`transit_home`): the descent waits for the cell under the unit to be open on the home layer; when it never is, the
unit sits on layer 4 with no destination, cannot see or shoot what is below, and the fight stalls.

Scene: canvas 2000 x 2000, a full-height wall `om_map_block_rect(1010, 0, 1322, 2000, layers 0..3)`. The rectangle is
rasterised to whole 100 wu route cells, so it blocks x 1000..1399 (cells 1000, 1100, 1200, 1300) on layers 0..3 and
leaves layer 4 open: x = 1322 blocks the whole 1300..1399 column. Raider (speed 150) at (300, 1000), layer 0. Measured
by hand (engine layer, x) every 50 ticks: the unit is on layer 4 over the wall by tick 50..100.
- OPEN goal: (1700, 1000), open on every layer.
- OVERHANG goal: (1350, 1000), inside the 1300..1399 cell: blocked on layer 0, open on layer 4. Nearest open layer-0
  cells are x >= 1400 (65 wu east of where the unit stops over the goal) and x < 1000 (far west).
Red today for the overhang goal and the removed goal: the unit ends on layer 4 (x 1335 / 1050) and never descends.
Tick-by-tick (layer, cell) lines are in every failure message."""
import pytest

from test_PP_C_g4_support import FRIEND, RAIDER, new_world, snap, spawn, step

START = (300.0, 1000.0)
OPEN_GOAL = (1700.0, 1000.0)
OVERHANG_GOAL = (1350.0, 1000.0)
WALL_X = (1000.0, 1400.0)     # the rasterised cells
RUN = 600                     # ticks: far above any route here (generous run limit, not a rule value)
NEAR = 100.0                  # wu: a goal-cell-sized allowance for "at the goal / in the nearest open cell"


def _cell(x, y):
    return (int(x // 100) * 100, int(y // 100) * 100)


def _world(lib, world_factory, goal):
    w = new_world(world_factory, lib, canvas=True)
    assert lib.om_map_block_rect(w, 1010.0, 0.0, 1322.0, 2000.0, 0, 3) == 0
    assert lib.om_map_sample_layer_accessibility(w, 1350.0, 1000.0, 0) == 0, "wall not there (Phase A stub)"
    assert lib.om_map_sample_layer_accessibility(w, 1350.0, 1000.0, 4) == 1, "layer 4 above the wall must be open"
    u = spawn(lib, w, RAIDER, FRIEND, START[0], START[1], 0)
    if goal is not None:
        lib.om_command_move(w, u, goal[0], goal[1])
    return w, u


def _run(lib, w, u, n, log, start=0, hook=None):
    for k in range(start + 1, start + n + 1):
        if hook:
            hook(k)
        step(lib, w)
        if k % 50 == 0:
            s = snap(lib, w, u)
            log.append(f"tick {k}: layer {s[0]} cell {_cell(s[3], s[4])} pos ({s[3]:.1f}, {s[4]:.1f})")
    return snap(lib, w, u)


def _report(log):
    return "\n".join(log)


def test_R_001_05_a_unit_ordered_across_a_block_to_an_open_goal_ends_on_its_home_layer_at_the_goal(lib, world_factory):
    """R-001-05: the normal case. Over the wall, down again, on layer 0 within 100 wu of the open goal. Control for the
    two red tests (the descent works when the cell below is open). Passes today."""
    w, u = _world(lib, world_factory, OPEN_GOAL)
    log = []
    went_over = []
    s = _run(lib, w, u, RUN, log, hook=lambda k: went_over.append(lib.om_unit_get_layer(w, u)))
    assert max(went_over) == 4, "control: it went up and over (else the scene tests nothing)\n" + _report(log)
    assert s[0] == 0 and s[1] == 0.0, "settled on layer 0\n" + _report(log)
    assert abs(s[3] - OPEN_GOAL[0]) <= NEAR and abs(s[4] - OPEN_GOAL[1]) <= NEAR, _report(log)


def test_R_001_05_a_goal_inside_the_blocked_overhang_ends_on_the_home_layer_in_the_nearest_open_cell(lib, world_factory):
    """R-001-05 second clause + R-097-09: the goal (1350, 1000) is blocked on layer 0 (rasterised wall) and open on layer
    4. The unit paths as close as it can and stops, on its home layer 0, in an open cell: never stranded on layer 4
    above the blocked cell. Nearest open cell is x >= 1400, so within 200 wu of the goal (the cell beyond plus
    slack). Red today: ends on layer 4 at (1335, 1000), target layer 0, no progress."""
    w, u = _world(lib, world_factory, OVERHANG_GOAL)
    log = []
    s = _run(lib, w, u, RUN, log)
    assert s[0] == 0 and s[1] == 0.0, f"stranded off its home layer: layer {s[0]}\n" + _report(log)
    assert lib.om_map_sample_layer_accessibility(w, s[3], s[4], 0) == 1, "ends in a cell blocked on its home layer\n" + _report(log)
    assert ((s[3] - OVERHANG_GOAL[0]) ** 2 + (s[4] - OVERHANG_GOAL[1]) ** 2) ** 0.5 <= 200.0, _report(log)


def test_R_097_09_a_unit_crossing_whose_goal_is_removed_mid_transit_returns_to_layer_0_in_the_nearest_open_cell(lib, world_factory):
    """R-001-05 + R-097-09: the Raider is ordered to the open far goal and its orders are cleared at tick 100, while it
    is on layer 4 over the wall (x about 1050, a cell blocked on layers 0..3). With no destination it must still come
    back down to layer 0, moving to the nearest open cell (x < 1000 or x >= 1400), within 300 ticks of the clear.
    Red today if it strands on layer 4 above the blocked cell (the descent waits for its own cell to open)."""
    w, u = _world(lib, world_factory, OPEN_GOAL)
    log = []
    s = _run(lib, w, u, 100, log)
    assert s[0] == 4 and WALL_X[0] <= s[3] < WALL_X[1], "control: crossing on layer 4 over the wall at tick 100\n" + _report(log)
    lib.om_unit_clear_orders(w, u)
    s = _run(lib, w, u, 300, log, start=100)
    assert s[0] == 0 and s[1] == 0.0, f"stranded off its home layer: layer {s[0]}\n" + _report(log)
    assert lib.om_map_sample_layer_accessibility(w, s[3], s[4], 0) == 1, "ends in a cell blocked on its home layer\n" + _report(log)


def test_R_004_05_the_overhang_and_the_removed_goal_scenes_are_deterministic(lib, world_factory):
    """Determinism guard: each scene run twice gives the identical per-50-tick position and layer trace. Passes today
    and must keep passing after the fix (the fix may not read a clock or hash order)."""
    def play(goal, clear_at):
        w, u = _world(lib, world_factory, goal)
        out = []
        for k in range(1, 401):
            if k == clear_at:
                lib.om_unit_clear_orders(w, u)
            step(lib, w)
            if k % 10 == 0:
                out.append(snap(lib, w, u))
        return out
    for goal, clear_at in ((OVERHANG_GOAL, None), (OPEN_GOAL, 101)):
        a = play(goal, clear_at)
        assert a == play(goal, clear_at), f"goal {goal} clear {clear_at}: the second run differs"
        assert any(s[0] == 4 for s in a), "control: the trace includes the crossing"
