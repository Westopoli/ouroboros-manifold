"""A146 / R-120-02 (E-14 patrol) + P3 canvas clamp: patrol waypoints stay inside the canvas.

The macro exposes no waypoint getter, so the waypoint is observed through the squad: an
off-canvas waypoint can never be reached (movement clamps to the canvas), so the patrol
stalls on it and the loop (patrol_idx advancing) never continues. A clamped waypoint is
reachable, so the squad visits every side of the diamond.
RED before the fix: the edge squad stalls at the off-canvas north waypoint.
"""
from b1_macro_scene import (
    CANVAS, OM_MACRO_MOD_CAUTIOUS, OM_MACRO_PATROL, centroid,
    spawn_enemy_squad, tactical_world,
)

RADIUS = 600.0   # csrc/enemy_macro.c OM_MACRO_PATROL_RADIUS
ARRIVE = 60.0    # OM_MACRO_PATROL_ARRIVE
TICKS = 6000
SAMPLE = 20


def _visited(lib, w, ids):
    pts = [centroid(lib, w, ids)]
    for t in range(SAMPLE, TICKS + 1, SAMPLE):
        lib.om_tactical_tick_to(w, t)
        pts.append(centroid(lib, w, ids))
    return pts


def _run(lib, world_factory, y0):
    w = tactical_world(lib, world_factory)
    lib.om_tactical_set_param(w, 0, 1.0)  # PP: runs the new movement (switch default 0, A147 option c')
    ids = spawn_enemy_squad(lib, w, y0=y0)
    ax, ay = centroid(lib, w, ids)
    lib.om_macro_set_state(w, 0, OM_MACRO_PATROL, OM_MACRO_MOD_CAUTIOUS)
    return ax, ay, _visited(lib, w, ids)


def _reaches_all_sides(ax, ay, pts, north_y):
    """patrol_idx kept advancing: the squad got within ARRIVE-ish of east, north, west and south waypoints."""
    near = lambda p, x, y: (p[0] - x) ** 2 + (p[1] - y) ** 2 <= (ARRIVE * 2) ** 2
    wps = [(ax + RADIUS, ay), (ax, north_y), (ax - RADIUS, ay), (ax, ay - RADIUS)]
    return all(any(near(p, x, y) for p in pts) for x, y in wps)


def test_R_120_02_patrol_at_canvas_edge_waypoints_clamped_and_loop_continues(lib, world_factory):
    """R-120-02 + A146: spawned 15 wu from the north edge, every patrol waypoint is clamped to the canvas and the loop continues."""
    ax, ay, pts = _run(lib, world_factory, CANVAS - 15.0)
    assert all(0.0 <= p[0] <= CANVAS and 0.0 <= p[1] <= CANVAS for p in pts)
    assert _reaches_all_sides(ax, ay, pts, min(ay + RADIUS, CANVAS)), \
        "R-120-02: patrol stalled on an off-canvas waypoint (patrol_idx stopped advancing)"


def test_R_120_02_patrol_mid_canvas_waypoints_unchanged(lib, world_factory):
    """Positive control: a mid-canvas squad's waypoints are unclamped, the full diamond (north waypoint at anchor + radius) is visited."""
    ax, ay, pts = _run(lib, world_factory, CANVAS / 2.0)
    assert _reaches_all_sides(ax, ay, pts, ay + RADIUS)
    assert max(p[1] for p in pts) > ay + RADIUS - ARRIVE
