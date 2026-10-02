"""B1-2 (plan 2026-09-30, item B1): patrol issues real waypoint-loop move
orders around the force's anchor (R-120-02: "plain-moves through its
waypoints in a cycle").

RED on main: om_macro_issue_group_orders has no PATROL branch, so a patrolling
force never receives an order and its centroid stays bit-identical.

The bible pins neither the loop radius nor the waypoint count nor what the
anchor is, so no absolute distance is asserted. The loop detector is purely
geometric: the path must leave its start and then close back on itself.
"""
from b1_macro_scene import (
    OM_MACRO_AMBUSH, OM_MACRO_CMD_MOVE, OM_MACRO_MOD_CAUTIOUS, OM_MACRO_PATROL,
    centroid, dist, spawn_enemy_squad, tactical_world,
)

SAMPLE_EVERY = 20
RUN_TICKS = 6000  # 300 s at 20 ticks/s; RAIDER walks 150 wu/s, 45000 wu of path
MIN_EXCURSION = 15.0  # OM_UNIT_COLLISION_RADIUS: "it moved" floor, not a loop size


def _trace(lib, w, ids, ticks=RUN_TICKS):
    pts = [centroid(lib, w, ids)]
    for t in range(SAMPLE_EVERY, ticks + 1, SAMPLE_EVERY):
        lib.om_tactical_tick_to(w, t)
        pts.append(centroid(lib, w, ids))
    return pts


def _path_len(pts, i, j):
    return sum(dist(pts[k], pts[k + 1]) for k in range(i, j))


def _is_loop(pts):
    """Leaves the start by more than MIN_EXCURSION, then some pair of samples
    i<j is within E/4 of each other having travelled at least 2E between them
    (E = farthest distance from the start): the path closed on itself."""
    e = max(dist(pts[0], p) for p in pts)
    if e <= MIN_EXCURSION:
        return False
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if dist(pts[i], pts[j]) <= e / 4.0 and _path_len(pts, i, j) >= 2.0 * e:
                return True
    return False


def test_R_120_02_patrol_force_loops_around_its_anchor(lib, world_factory):
    """R-120-02: a patrol force plain-moves through waypoints in a cycle: its centroid leaves the anchor and its path closes into a loop within five minutes."""
    w = tactical_world(lib, world_factory)
    ids = spawn_enemy_squad(lib, w)
    lib.om_macro_set_state(w, 0, OM_MACRO_PATROL, OM_MACRO_MOD_CAUTIOUS)
    pts = _trace(lib, w, ids)
    e = max(dist(pts[0], p) for p in pts)
    assert e > MIN_EXCURSION, f"R-120-02: patrol force never left its anchor (max excursion {e:.2f} wu)"
    assert _is_loop(pts), "R-120-02: patrol force moved but its path never closed into a waypoint loop"


def test_R_120_02_patrol_orders_are_plain_moves(lib, world_factory):
    """R-120-02/R-120-04: patrol issues plain moves (the command type the macro layer reports for patrol) and does it through the tick, so after an evaluation the squad has real velocity, not just a log row."""
    w = tactical_world(lib, world_factory)
    ids = spawn_enemy_squad(lib, w)
    lib.om_macro_set_state(w, 0, OM_MACRO_PATROL, OM_MACRO_MOD_CAUTIOUS)
    start = centroid(lib, w, ids)
    # Test-defect, A146: the squad walks a diamond and the canvas clamp keeps it inside, so at tick 200 it can be
    # back near its start. The intent is 'the squad moved': take the largest excursion over the 200 ticks.
    far = 0.0
    for t in range(SAMPLE_EVERY, 201, SAMPLE_EVERY):
        lib.om_tactical_tick_to(w, t)
        far = max(far, dist(start, centroid(lib, w, ids)))
    lib.om_tactical_tick_to(w, 200)
    assert lib.om_macro_get_last_issued_command_type(w, 0) == OM_MACRO_CMD_MOVE
    assert far > MIN_EXCURSION, "R-120-02: patrol issued no order, squad did not move in 200 ticks"


def test_R_120_02_patrol_detector_positive_control(lib, world_factory):
    """Positive control for the loop detector: a squad the test itself walks round a 4-waypoint square is recognised as a loop."""
    w = tactical_world(lib, world_factory)
    ids = spawn_enemy_squad(lib, w)
    x0, y0 = centroid(lib, w, ids)
    square = [(x0 - 600, y0), (x0 - 600, y0 - 600), (x0, y0 - 600), (x0, y0)]
    pts = [centroid(lib, w, ids)]
    t = 0
    for wx, wy in square * 2:
        lib.om_command_move(w, ids, len(ids), wx, wy)
        for _ in range(12):  # 240 ticks: 600 wu at 150 wu/s takes 80 ticks
            t += SAMPLE_EVERY
            lib.om_tactical_tick_to(w, t)
            pts.append(centroid(lib, w, ids))
    assert _is_loop(pts)


def test_R_120_02_patrol_detector_negative_control(lib, world_factory):
    """Negative control: a squad held still in ambush (no player in sight) is not a loop."""
    w = tactical_world(lib, world_factory)
    ids = spawn_enemy_squad(lib, w)
    lib.om_macro_set_state(w, 0, OM_MACRO_AMBUSH, OM_MACRO_MOD_CAUTIOUS)
    assert not _is_loop(_trace(lib, w, ids, ticks=600))
