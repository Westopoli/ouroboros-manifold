# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase A::P5 (fixed tables from audit G23)
# spec: docs/northstar/research/layer_dynamics/port_gap_audit_2026-10-02.md::G23
# spec: docs/bible/epics/E-13-movement-and-command.md::R-097-02 (route computed once and cached)
"""Fixed-table guard (audit G23): every fixed table in the C is either big enough for
OM_MAX_UNITS (10,100) and the largest canvas, or its test is red and named. P5 of the plan:
"Fixed tables from audit G23 (64 groups, 64 members, 1,024 queued orders, discovery ids to 255,
route cache 256, cover and obstacles 256, fog zones 64, vantage 32, structures 64) are each sized
for OM_MAX_UNITS and the largest canvas or shown not to bind, first, or the 10,000-unit test fails".

How "big enough" is measured (the plan gives no per-table number; these derivations are the
test writer's and are listed in the wave report for the Architect to confirm or replace):
  keyed by unit      groups, group members, queued orders, route-cache destinations, fog-tracked
                     elevation units, discovery ids: REQUIRED = OM_MAX_UNITS, the number of units
                     that can each hold one entry (csrc/ouroboros_sim.h).
  keyed by cell      density cells: the cells of the largest canvas, (OM_CANVAS_SIZE_RANGES_LARGE_HI
                     / OM_NAVMESH_CELL_SIZE) squared = 280 x 280 = 78,400 (csrc/om_constants.h; the
                     audit's 24,000 wu canvas is the E-13 scale canvas, 57,600 cells, and is smaller).
  keyed by map       cover discs and obstacle discs: PROPOSED, one per 500 wu patch of the largest
                     canvas, 56 x 56 = 3,136. No number exists in the bible or the plan.
  keyed by spine     fog zones and vantage nodes: the spine has 10 to 30 nodes (E-17 R-113), so 30
                     of each is the most one map places. Structures per mission: the largest
                     om_structure_compute_count over the three map sizes (8).
The 64-member and 64-group tables are also checked for what they do to play, not only for size
(groups that finish are reclaimed; the queue and route cache are not cumulative for a whole battle).

Over-cap rule (the positive control of this file): a request beyond a table must be refused
cleanly (a zero or all-ones handle where the API has one, silent drop where it is void), never
overflow: entries already stored stay intact and distinct. Every table has a test for it.

The scale conftest gates this directory behind OM_SCALE=1; run with that set.
"""
import ctypes
import re
from pathlib import Path

import pytest

from ._scale_helpers import REPO_ROOT, raw_world

VANGUARD = 2
SRC = Path(REPO_ROOT) / "csrc"


def _define(header, name):
    text = (SRC / header).read_text()
    return int(re.search(rf"#define\s+{name}\s+(\d+)", text).group(1))


OM_MAX_UNITS = _define("ouroboros_sim.h", "OM_MAX_UNITS")
CELL = _define("om_constants.h", "OM_NAVMESH_CELL_SIZE")
CANVAS_MAX = _define("om_constants.h", "OM_CANVAS_SIZE_RANGES_LARGE_HI")
CANVAS_CELLS = (CANVAS_MAX // CELL) ** 2
DISCS = (CANVAS_MAX // 500) ** 2                 # PROPOSED, see the module docstring
SPINE_MAX = 30
NO_HANDLE = 0xFFFFFFFF
SEED = 2026100202


def _world(lib):
    return raw_world(lib, 1, SEED, features=[])


def _spawn_grid(lib, w, n, faction=0, spacing=60.0, x0=500.0, y0=500.0, per_row=160):
    return [lib.om_unit_spawn(w, VANGUARD, faction, x0 + (i % per_row) * spacing,
                              y0 + (i // per_row) * spacing, 0) for i in range(n)]


def _one(uid):
    return (ctypes.c_uint32 * 1)(uid)


# ====================================================================== groups (64)

def _group_orders(lib, w, ids, x_of):
    return [lib.om_command_group_move(w, _one(u), 1, x_of(i), 20000.0) for i, u in enumerate(ids)]


def test_PP_table_groups_hold_one_group_per_unit(lib):
    """G23 / P5: 64 groups. One live group per unit (10,100 single-unit orders, distant goals so
    none finishes) must all be live: today the 65th overwrites the last slot."""
    w = _world(lib)
    ids = _spawn_grid(lib, w, OM_MAX_UNITS)
    gids = _group_orders(lib, w, ids, lambda i: 500.0 + (i % 160) * 60.0)
    lost = [g for g in gids if g == 0 or not lib.om_group_is_active(w, g)]
    lib.om_world_free(w)
    assert not lost, (f"group table binds: {len(lost)} of {len(gids)} single-unit groups are not live "
                      f"(first lost gid {lost[0]}); 64 slots, the 65th overwrites the 64th")


def test_PP_table_groups_over_cap_refused_cleanly(lib):
    """Over-cap rule, groups: after one group per unit, 1,000 more orders (units 1..1000 re-ordered)
    must each return 0 (refused) or a live group, and no group that was live before may stop being
    live (units 1..1000 only moved on to new groups, so groups of units 1001.. are the witnesses)."""
    w = _world(lib)
    ids = _spawn_grid(lib, w, OM_MAX_UNITS)
    gids = _group_orders(lib, w, ids, lambda i: 500.0 + (i % 160) * 60.0)
    witnesses = [g for g in gids[1000:] if g != 0 and lib.om_group_is_active(w, g)]
    extra = [lib.om_command_group_move(w, _one(u), 1, 600.0 + 3.0 * k, 21000.0) for k, u in enumerate(ids[:1000])]
    bad_new = [g for g in extra if g != 0 and not lib.om_group_is_active(w, g)]
    clobbered = [g for g in witnesses if not lib.om_group_is_active(w, g)]
    lib.om_world_free(w)
    assert not bad_new, f"{len(bad_new)} accepted over-cap groups are not live"
    assert not clobbered, f"over-cap orders destroyed {len(clobbered)} live groups (slot overwritten)"


# ================================================================ group members (64)

def _group_after(lib, n_far, ticks):
    w = _world(lib)
    click = (15000.0, 15000.0)
    near = [lib.om_unit_spawn(w, VANGUARD, 0, click[0] + (i % 8) * 4.0, click[1] + (i // 8) * 4.0, 0)
            for i in range(64)]
    far = _spawn_grid(lib, w, n_far, x0=500.0, y0=500.0)
    ids = near + far
    gid = lib.om_command_group_move(w, (ctypes.c_uint32 * len(ids))(*ids), len(ids), click[0], click[1])
    live_at_start = lib.om_group_is_active(w, gid)
    for _ in range(ticks):
        lib.om_tactical_step(w)
    live = lib.om_group_is_active(w, gid)
    lib.om_world_free(w)
    return live_at_start, live


def test_PP_table_group_members_all_tracked_for_arrival(lib):
    """G23 / P5: 64 members tracked for arrival. A group of OM_MAX_UNITS: the first 64 stand on the
    click point (arrived), every other unit is thousands of wu away. After 100 ticks the group must
    still be live (a group of two or more ends when every member has arrived)."""
    start, live = _group_after(lib, OM_MAX_UNITS - 64, 100)
    assert start
    assert live, ("group member table binds: the group ended when the first 64 members arrived, "
                  f"with {OM_MAX_UNITS - 64} members still far away")


def test_PP_table_group_members_control_a_group_that_has_all_arrived_ends(lib):
    """Positive control for the test above: the same 64 arrived members and nobody else: the group
    ends within 100 ticks, so 'still live' above means members were counted."""
    start, live = _group_after(lib, 0, 100)
    assert start and not live


def test_PP_table_group_members_over_cap_refused_cleanly(lib):
    """Over-cap rule, members: a list longer than the unit store (OM_MAX_UNITS + 500, the first 500
    ids repeated) must not overflow: it returns 0 or a live group, and the call returns."""
    w = _world(lib)
    ids = _spawn_grid(lib, w, OM_MAX_UNITS)
    over = ids + ids[:500]
    gid = lib.om_command_group_move(w, (ctypes.c_uint32 * len(over))(*over), len(over), 12000.0, 12000.0)
    ok = gid == 0 or lib.om_group_is_active(w, gid)
    lib.om_world_free(w)
    assert ok, "an over-long member list produced a group that is not live"


# ============================================================ queued orders (1,024)

def _queue_all(lib, w, ids):
    for u in ids:
        lib.om_command_queue_move(w, u, 500.0 + (u % 160) * 60.0, 22000.0)


def test_PP_table_queue_holds_one_order_per_unit(lib):
    """G23 / P5: 1,024 queued orders. One queued move per unit (10,100), then 100 ticks: every unit
    must have started to move."""
    w = _world(lib)
    ids = _spawn_grid(lib, w, OM_MAX_UNITS)
    start = {u: lib.om_unit_get_pos(w, u) for u in ids}
    _queue_all(lib, w, ids)
    for _ in range(100):
        lib.om_tactical_step(w)
    unmoved = [u for u in ids if lib.om_unit_get_pos(w, u) == start[u]]
    lib.om_world_free(w)
    assert not unmoved, (f"queue binds: {len(unmoved)} of {len(ids)} queued orders never took effect "
                         f"(first unit id {unmoved[0]}); 1,024 slots")


def test_PP_table_queue_over_cap_refused_cleanly(lib):
    """Over-cap rule, queue: OM_MAX_UNITS + 1,000 queued orders in one tick. Whatever is refused,
    the orders accepted first must still work: the first 1,000 units all move."""
    w = _world(lib)
    ids = _spawn_grid(lib, w, OM_MAX_UNITS)
    start = {u: lib.om_unit_get_pos(w, u) for u in ids}
    _queue_all(lib, w, ids)
    for k in range(1000):
        lib.om_command_queue_move(w, ids[k], 500.0 + k, 23000.0)
    for _ in range(100):
        lib.om_tactical_step(w)
    unmoved = [u for u in ids[:1000] if lib.om_unit_get_pos(w, u) == start[u]]
    lib.om_world_free(w)
    assert not unmoved, f"{len(unmoved)} of the first 1,000 queued orders were lost to the over-cap requests"


def _queue_chain_y(lib, n_orders):
    """One unit gets a queued move each tick, alternating west and east; the last sends it north.
    Returns y after 60 more ticks (it starts at 10,000; north is +y)."""
    w = _world(lib)
    u = lib.om_unit_spawn(w, VANGUARD, 0, 10000.0, 10000.0, 0)
    for k in range(n_orders - 1):
        lib.om_command_queue_move(w, u, 10000.0 + (500.0 if k % 2 else -500.0), 10000.0)
        lib.om_tactical_step(w)
    lib.om_command_queue_move(w, u, 10000.0, 20000.0)
    for _ in range(60):
        lib.om_tactical_step(w)
    y = lib.om_unit_get_pos(w, u)[1]
    lib.om_world_free(w)
    return y


def test_PP_table_queue_slots_are_reclaimed_over_a_battle(lib):
    """P5: the queue must not be cumulative for the whole battle. One unit gets a queued move every
    tick for 1,100 ticks; the 1,100th sends it north and must take effect (today the 1,025th and
    later orders are dropped). Control: the same chain with 100 orders does go north."""
    assert _queue_chain_y(lib, 100) > 10100.0, "control: a short chain must end with the unit going north"
    y = _queue_chain_y(lib, 1100)
    assert y > 10100.0, f"the 1,100th queued order never took effect (y={y:.1f}): queue slots are never freed"


# ===================================================================== discovery ids

def _deflection(lib, blocker_id):
    """Largest sideways deviation of a mover (id 1) walking straight at a blocker 3 wu off its line.
    OM_MAX_UNITS units in every scene (far-away fillers), so the tick rate is the same; only the id
    of the blocker changes."""
    w = _world(lib)
    mover = lib.om_unit_spawn(w, VANGUARD, 0, 1000.0, 1000.0, 0)
    for k in range(2, OM_MAX_UNITS + 1):
        if k == blocker_id:
            lib.om_unit_spawn(w, VANGUARD, 0, 1100.0, 1003.0, 0)
        else:
            lib.om_unit_spawn(w, VANGUARD, 0, 3000.0 + 150.0 * (k % 100), 3000.0 + 150.0 * (k // 100), 0)
    lib.om_command_move(w, _one(mover), 1, 1400.0, 1000.0)
    dev = 0.0
    for _ in range(120):
        lib.om_tactical_step(w)
        dev = max(dev, abs(lib.om_unit_get_pos(w, mover)[1] - 1000.0))
    lib.om_world_free(w)
    return dev


@pytest.mark.parametrize("blocker_id", [256, 1025, OM_MAX_UNITS - 1, OM_MAX_UNITS])
def test_PP_table_discovery_blocker_with_a_large_id_still_blocks(lib, blocker_id):
    """G23 / P5: discovery ids to 255. A blocker whose id is past 255, up to the last the unit store
    holds (OM_MAX_UNITS), deflects a mover exactly as one with id 2 does. At OM_MAX_UNITS this is red
    today: the move module's tables hold ids 1..10,099 (arrays of 10,100 indexed by id)."""
    control = _deflection(lib, 2)
    assert control > 10.0, "control: a blocker with id 2 must deflect the mover"
    got = _deflection(lib, blocker_id)
    assert got == control, (f"the blocker with id {blocker_id} deflects by {got:.2f} wu, the one with id 2 "
                            f"by {control:.2f}: the move module does not see unit {blocker_id}")


def test_PP_table_discovery_control_no_blocker_no_deflection(lib):
    """Positive control for the deflection detector: with no blocker the mover walks dead straight."""
    w = _world(lib)
    mover = lib.om_unit_spawn(w, VANGUARD, 0, 1000.0, 1000.0, 0)
    lib.om_command_move(w, _one(mover), 1, 1400.0, 1000.0)
    dev = 0.0
    for _ in range(120):
        lib.om_tactical_step(w)
        dev = max(dev, abs(lib.om_unit_get_pos(w, mover)[1] - 1000.0))
    lib.om_world_free(w)
    assert dev == 0.0


# ================================================================ density cells (1,024)

def _fill_density(lib, w, side, offset=0):
    for cx in range(side):
        for cy in range(side):
            lib.om_map_set_obstacle_density(w, cx + offset, cy, 0, 1.0)


def test_PP_table_density_cells_cover_the_largest_canvas(lib):
    """G23 / P5: 1,024 density cells. Every cell of the largest canvas (280 x 280) can be blocked."""
    side = CANVAS_MAX // CELL
    w = _world(lib)
    _fill_density(lib, w, side)
    open_cells = sum(1 for cx in range(side) for cy in range(side)
                     if not lib.om_navmesh_is_cell_blocked(w, cx, cy, 0))
    lib.om_world_free(w)
    assert open_cells == 0, (f"density table binds: {open_cells} of {CANVAS_CELLS} cells of the "
                             f"{CANVAS_MAX} wu canvas cannot be blocked")


def test_PP_table_density_cells_over_cap_refused_cleanly(lib):
    """Over-cap rule, density: after the canvas grid is set, 1,000 more cells (outside it) are
    requested. The request is void, so refusal is silent; every cell that read as blocked before
    must still be blocked after, and no cell outside the requests appears blocked."""
    side = CANVAS_MAX // CELL
    w = _world(lib)
    _fill_density(lib, w, side)
    before = {(cx, cy) for cx in range(side) for cy in range(side) if lib.om_navmesh_is_cell_blocked(w, cx, cy, 0)}
    for k in range(1000):
        lib.om_map_set_obstacle_density(w, side + 10 + k, 0, 0, 1.0)
    lost = [c for c in before if not lib.om_navmesh_is_cell_blocked(w, c[0], c[1], 0)]
    ghost = [k for k in range(0, 1000, 50) if lib.om_navmesh_is_cell_blocked(w, side + 5, side + 5 + k, 0)]
    lib.om_world_free(w)
    assert not lost, f"{len(lost)} cells blocked before the over-cap requests are no longer blocked"
    assert not ghost, "a cell nobody set reads as blocked"


# ==================================================================== route cache (256)

def test_PP_table_route_cache_holds_a_destination_per_unit(lib):
    """G23 / P5, R-097-02: route cache 256. OM_MAX_UNITS distinct destinations are each queried
    twice; every second query must be a cache hit."""
    w = _world(lib)
    dests = [(500.0 + (i % 160) * 150.0, 500.0 + (i // 160) * 150.0) for i in range(OM_MAX_UNITS)]
    for x, y in dests:
        lib.om_navmesh_find_path(w, 100.0, 100.0, x, y, 0)
    before = lib.om_navmesh_get_cache_hits(w)
    for x, y in dests:
        lib.om_navmesh_find_path(w, 100.0, 100.0, x, y, 0)
    hits = lib.om_navmesh_get_cache_hits(w) - before
    lib.om_world_free(w)
    assert hits == len(dests), f"route cache binds: {hits} of {len(dests)} repeated destinations hit the cache"


def test_PP_table_route_cache_new_shared_destination_is_cached_after_many(lib):
    """R-097-02 after a long battle: once 300 other destinations have been used, a destination shared
    by two queries is still computed once (the second query is a hit). The cache never evicts today."""
    w = _world(lib)
    for i in range(300):
        lib.om_navmesh_find_path(w, 100.0, 100.0, 500.0 + i * 100.0, 500.0, 0)
    shared = (20000.0, 20000.0)
    lib.om_navmesh_find_path(w, 100.0, 100.0, shared[0], shared[1], 0)
    before = lib.om_navmesh_get_cache_hits(w)
    lib.om_navmesh_find_path(w, 150.0, 150.0, shared[0], shared[1], 0)
    hits = lib.om_navmesh_get_cache_hits(w) - before
    lib.om_world_free(w)
    assert hits == 1, "a shared destination was not cached: the route cache is full and never evicts"


def test_PP_table_route_cache_over_cap_answers_stay_correct(lib):
    """Over-cap rule, route cache: answers for destinations past the cache are the same as before
    the cache filled (the cache never changes a path, it only skips work)."""
    w = _world(lib)
    first = [lib.om_navmesh_find_path(w, 100.0, 100.0, 400.0 + 10.0 * i, 900.0, 0) for i in range(5)]
    for i in range(OM_MAX_UNITS + 500):
        lib.om_navmesh_find_path(w, 100.0, 100.0, 500.0 + (i % 160) * 150.0, 500.0 + (i // 160) * 150.0, 0)
    again = [lib.om_navmesh_find_path(w, 100.0, 100.0, 400.0 + 10.0 * i, 900.0, 0) for i in range(5)]
    lib.om_world_free(w)
    assert first == again


# ==================================================================== route search cap

def test_PP_route_search_reaches_across_the_canvas(lib):
    """Not in G23's list, same file (tactical_move.c OM_MOVE_BFS_CAP 512): the router gives up after
    512 cells. A wall across the largest canvas with its only gap 140 cells from the start: the way
    round exists, so the query must find it (an answer above 2 is a route; 1 is 'none found')."""
    side = CANVAS_MAX // CELL
    w = _world(lib)
    for cy in range(side):
        if 200 <= cy <= 203:
            continue
        lib.om_map_set_obstacle_density(w, 140, cy, 0, 1.0)
    found = lib.om_navmesh_find_path(w, 13950.0, 5050.0, 14050.0, 5050.0, 0)
    lib.om_world_free(w)
    assert found > 2, ("route search cap binds: no way round a wall with a gap 150 cells away "
                       f"(answer {found}); the search stops after 512 cells")


# ============================================================ cover and obstacles (256)

def _patch_xy(i):
    return 250.0 + 500.0 * (i % 56), 250.0 + 500.0 * (i // 56)


def test_PP_table_cover_holds_the_proposed_count(lib):
    """G23 / P5: 256 cover discs. DISCS (PROPOSED 3,136, one per 500 wu patch of the largest canvas)
    must all be stored and readable."""
    w = _world(lib)
    handles = [lib.om_map_add_cover(w, *_patch_xy(i), 40.0, 1.0) for i in range(DISCS)]
    stored = lib.om_map_cover_count(w)
    lib.om_world_free(w)
    assert 0 not in handles and stored == DISCS, (
        f"cover table binds: {handles.count(0)} of {DISCS} cover discs refused, {stored} stored")


def test_PP_table_cover_over_cap_refused_cleanly(lib):
    """Over-cap rule, cover: DISCS + 1,000 requests. A refused request returns 0 and the count does
    not move; every stored disc keeps its own position."""
    w = _world(lib)
    n = DISCS + 1000
    handles = [lib.om_map_add_cover(w, *_patch_xy(i % DISCS), 40.0 + (i // DISCS), 1.0) for i in range(n)]
    count = lib.om_map_cover_count(w)
    accepted = sum(1 for h in handles if h != 0)
    x, y, r, h = (ctypes.c_double() for _ in range(4))
    wrong = 0
    for i in range(count):
        assert lib.om_map_cover_at(w, i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(r), ctypes.byref(h)) == 1
        if (x.value, y.value) != _patch_xy(i % DISCS):
            wrong += 1
    lib.om_world_free(w)
    assert count == accepted, f"count {count} differs from accepted requests {accepted}"
    assert wrong == 0, f"{wrong} stored cover discs do not hold the position they were given"


def test_PP_table_obstacles_hold_the_proposed_count(lib):
    """G23 / P5: 256 obstacle discs. DISCS (PROPOSED 3,136) must all be stored and read as blocked at
    their centres."""
    w = _world(lib)
    handles = [lib.om_map_add_obstacle(w, *_patch_xy(i), 40.0) for i in range(DISCS)]
    soft = [i for i in range(DISCS) if lib.om_map_sample_obstacle_density(w, *_patch_xy(i)) <= 0.7]
    lib.om_world_free(w)
    assert 0 not in handles, f"obstacle table binds: {handles.count(0)} of {DISCS} obstacle discs refused"
    assert not soft, f"{len(soft)} stored obstacle discs read as open at their centre"


def test_PP_table_obstacles_over_cap_refused_cleanly(lib):
    """Over-cap rule, obstacles: DISCS + 1,000 requests; refused ones return 0 and the discs stored
    before them still read as blocked."""
    w = _world(lib)
    handles = [lib.om_map_add_obstacle(w, *_patch_xy(i % DISCS), 40.0) for i in range(DISCS + 1000)]
    accepted = [i for i, h in enumerate(handles) if h != 0]
    soft = [i for i in accepted if lib.om_map_sample_obstacle_density(w, *_patch_xy(i % DISCS)) <= 0.7]
    ids_unique = len({h for h in handles if h != 0}) == len(accepted)
    lib.om_world_free(w)
    assert ids_unique, "two accepted obstacle requests share one handle (overflow)"
    assert not soft, f"{len(soft)} stored obstacle discs read as open after the over-cap requests"


# ====================================================================== fog (64, 32, 512)

def test_PP_table_fog_zones_hold_one_per_spine_node(lib):
    """G23 / P5: 64 fog zones. A spine has at most 30 nodes (E-17 R-113): 30 zones must all act.
    (Shown not to bind at 64; the over-cap test below runs past it.)"""
    w = _world(lib)
    for i in range(SPINE_MAX):
        lib.om_map_add_interference_zone(w, 1000.0 + 700.0 * i, 1000.0, 0, 0.5, 200.0)
    dead = [i for i in range(SPINE_MAX)
            if lib.om_zone_sample_interference(w, 1000.0 + 700.0 * i, 1000.0, 0) <= 0.0]
    lib.om_world_free(w)
    assert not dead, f"fog zone table binds: zones {dead} do not act"


def test_PP_table_fog_zones_over_cap_refused_cleanly(lib):
    """Over-cap rule, fog zones: 200 requests (void, so refusal is silent). Zones stored first keep
    acting at their own centres; no zone is written over."""
    w = _world(lib)
    for i in range(200):
        lib.om_map_add_interference_zone(w, 1000.0 + 700.0 * i, 1000.0, 0, 0.5, 200.0)
    first = [i for i in range(SPINE_MAX)
             if abs(lib.om_zone_sample_interference(w, 1000.0 + 700.0 * i, 1000.0, 0) - 0.5) > 1e-9]
    lib.om_world_free(w)
    assert not first, f"zones {first} no longer read their own intensity after the over-cap requests"


def _vantage_factor(lib, w, x):
    u = lib.om_unit_spawn(w, VANGUARD, 0, x, 3000.0, 0)
    return lib.om_unit_get_cross_layer_factor(w, u, 1)


def test_PP_table_vantage_holds_one_per_spine_node(lib):
    """G23 / P5: 32 vantage nodes. At most 30 spine nodes (E-17 R-113): a unit at the centre of each
    of 30 vantage nodes must get the doubled cross-layer factor, a unit outside any must not."""
    w = _world(lib)
    for i in range(SPINE_MAX):
        lib.om_map_add_vantage_node(w, 1000.0 + 700.0 * i, 3000.0, 100.0)
    plain = _vantage_factor(lib, w, 500.0)
    boosted = [i for i in range(SPINE_MAX) if _vantage_factor(lib, w, 1000.0 + 700.0 * i) > plain]
    lib.om_world_free(w)
    assert plain < 1.0, "control: a unit outside every vantage node must not get the doubled factor"
    assert boosted == list(range(SPINE_MAX)), f"vantage table binds: nodes {sorted(set(range(SPINE_MAX)) - set(boosted))}"


def test_PP_table_vantage_over_cap_refused_cleanly(lib):
    """Over-cap rule, vantage: 100 requests (void). The first 30 still work, and a unit far from all
    of them gets no factor."""
    w = _world(lib)
    for i in range(100):
        lib.om_map_add_vantage_node(w, 1000.0 + 700.0 * i, 3000.0, 100.0)
    plain = _vantage_factor(lib, w, 500.0)
    boosted = [i for i in range(SPINE_MAX) if _vantage_factor(lib, w, 1000.0 + 700.0 * i) > plain]
    lib.om_world_free(w)
    assert boosted == list(range(SPINE_MAX))


def test_PP_table_fog_tracked_elevation_units_cover_every_unit(lib):
    """G23 / P5: 512 elevation-tracked units. OM_MAX_UNITS units spawned with elevation tier 2: each
    must read its own elevation bonus. (Fed only by om_unit_spawn_with_elevation, which no game
    path calls today; the table still binds if it is ever wired.)"""
    w = _world(lib)
    flat = lib.om_unit_spawn(w, VANGUARD, 0, 100.0, 100.0, 0)
    base = lib.om_unit_get_effective_sensor_radius_to_target_elevation(w, flat, 0)
    ids = [lib.om_unit_spawn_with_elevation(w, VANGUARD, 0, 500.0 + (i % 160) * 60.0, 500.0 + (i // 160) * 60.0, 0, 2)
           for i in range(OM_MAX_UNITS - 1)]
    lost = [u for u in ids if lib.om_unit_get_effective_sensor_radius_to_target_elevation(w, u, 0) <= base]
    lib.om_world_free(w)
    assert not lost, (f"elevation table binds: {len(lost)} of {len(ids)} elevated units lost their "
                      f"bonus (first id {lost[0]})")


def test_PP_table_fog_tracked_over_cap_refused_cleanly(lib):
    """Over-cap rule, tracked units: 600 elevated units (past 512). The ones tracked first keep
    their bonus; the unit store itself is unaffected (ids stay dense and alive)."""
    w = _world(lib)
    flat = lib.om_unit_spawn(w, VANGUARD, 0, 100.0, 100.0, 0)
    base = lib.om_unit_get_effective_sensor_radius_to_target_elevation(w, flat, 0)
    ids = [lib.om_unit_spawn_with_elevation(w, VANGUARD, 0, 500.0 + 60.0 * i, 500.0, 0, 2) for i in range(600)]
    first_ok = all(lib.om_unit_get_effective_sensor_radius_to_target_elevation(w, u, 0) > base for u in ids[:500])
    alive = all(lib.om_unit_alive(w, u) for u in ids)
    lib.om_world_free(w)
    assert first_ok and alive


# ============================================================================ structures (64)

def test_PP_table_structures_hold_the_most_a_mission_places(lib):
    """G23 / P5: 64 structures. The most a mission places is the largest om_structure_compute_count
    over the three map sizes; both structure tables must hold that many, each distinct."""
    most = max(lib.om_structure_compute_count(1e9, size) for size in (0, 1, 2))
    w = _world(lib)
    handles = [lib.om_map_add_structure(w, 1000.0 + 700.0 * i, 1000.0, 0) for i in range(most)]
    for i in range(most):
        lib.om_structure_init(w, i, 100 + i, 50.0)
    types = [lib.om_structure_get_unit_type(w, i) for i in range(most)]
    lib.om_world_free(w)
    assert NO_HANDLE not in handles and len(set(handles)) == most
    assert types == [100 + i for i in range(most)]


def test_PP_table_structures_over_cap_refused_cleanly(lib):
    """Over-cap rule, structures: the map table returns the all-ones handle once full and keeps its
    first rows; the support table must not write structure 64 and up over structure 63."""
    w = _world(lib)
    handles = [lib.om_map_add_structure(w, 1000.0 + 20.0 * i, 1000.0, 0) for i in range(100)]
    accepted = [h for h in handles if h != NO_HANDLE]
    lib.om_structure_init(w, 63, 111, 50.0)
    for idx in range(64, 80):
        lib.om_structure_init(w, idx, 222, 50.0)
    kept = lib.om_structure_get_unit_type(w, 63)
    lib.om_world_free(w)
    assert len(accepted) == len(set(accepted)) and handles[len(accepted):] == [NO_HANDLE] * (100 - len(accepted))
    assert kept == 111, "structure init past the table overwrote structure 63 (index clamped, not refused)"
