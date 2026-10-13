"""E-01 R-001-07 (as amended 2026-10-06) and R-200-02: a walking unit stands only on cells that have ground for it on
its layer, takes no timed transfer, and a layer order of any kind changes nothing for it; a flyer is unchanged.
Terrain stage 2 spec 2026-10-06, "move" lane.

Scene: seed 11 terrain on a 16000 wu canvas (100 wu cells, row-major; engine layer L stands on band L + 1). The
Raider type (speed 150) is set to walking with om_roster_set_movement_kind. Red today because the lane's pieces
are contract stubs: om_terrain_walk_mask is all zeros and om_walk_route returns -1, so a walker has no cell to
stand on and does not steer.
"""
import ctypes
import random

from conftest import OMFeature

RAIDER = 0
FRIEND = 0
OM_MOVE_FLYING, OM_MOVE_WALKING = 0, 1
CANVAS = 16000.0
SEED = 11
CELL_WU = 100.0
LAYER = 2                    # band 3 ground: the largest walkable plateau on seed 11
TICKS = 2000                 # spec: 2,000 ticks of random orders
ORDER_EVERY = 100            # provisional (2026-10-06): ticks between random orders
PROBE_TICKS = 200            # provisional (2026-10-06): ticks watched after a layer order


def _world(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    return w


def _mask(lib, w, layer):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    n = cw.value * ch.value
    buf = (ctypes.c_uint8 * n)()
    assert lib.om_terrain_walk_mask(w, layer, buf, n) == n
    return bytes(buf), cw.value


def _masked(mask, cw, x, y):
    cx, cy = int(x // CELL_WU), int(y // CELL_WU)
    return 0 <= cx < cw and 0 <= cy < len(mask) // cw and mask[cy * cw + cx] == 1


def _first_masked_centre(mask, cw):
    for i, v in enumerate(mask):
        if v:
            return (i % cw + 0.5) * CELL_WU, (i // cw + 0.5) * CELL_WU
    return None


def _walker(lib, w):
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_WALKING) == 0
    mask, cw = _mask(lib, w, LAYER)
    start = _first_masked_centre(mask, cw)
    assert start is not None, "walk mask for layer 2 is empty (om_terrain_walk_mask is a contract stub)"
    u = lib.om_unit_spawn(w, RAIDER, FRIEND, start[0], start[1], LAYER)
    assert u != 0
    return u, mask, cw


def test_R_001_07_a_walker_never_leaves_masked_cells_over_2000_ticks_of_random_orders(lib, world_factory):
    w = _world(lib, world_factory)
    u, mask, cw = _walker(lib, w)
    rng = random.Random(SEED)
    for k in range(1, TICKS + 1):
        if k % ORDER_EVERY == 1:
            lib.om_command_move(w, u, rng.uniform(0.0, CANVAS), rng.uniform(0.0, CANVAS))
        lib.om_tactical_step(w)
        x, y = lib.om_unit_get_pos(w, u)
        layer = lib.om_unit_get_layer(w, u)
        m = mask if layer == LAYER else _mask(lib, w, layer)[0]
        assert _masked(m, cw, x, y), f"tick {k}: walker at ({x:.1f}, {y:.1f}) layer {layer} is on an unmasked cell"


def test_R_001_07_a_walker_actually_moves_toward_an_order(lib, world_factory):
    """Positive control for the test above: a walker that never moves would pass it vacuously."""
    w = _world(lib, world_factory)
    u, mask, cw = _walker(lib, w)
    x0, y0 = lib.om_unit_get_pos(w, u)
    lib.om_command_move(w, u, x0 + 1000.0, y0)
    for _ in range(PROBE_TICKS):
        lib.om_tactical_step(w)
    x, y = lib.om_unit_get_pos(w, u)
    assert abs(x - x0) + abs(y - y0) > CELL_WU, f"walker did not move from ({x0:.0f}, {y0:.0f}): now ({x:.0f}, {y:.0f})"


def test_R_001_07_a_layer_order_to_a_walker_changes_nothing(lib, world_factory):
    w = _world(lib, world_factory)
    u, mask, cw = _walker(lib, w)
    # Walk-routing proof first: the walker is only a walker if the route exists (stub returns -1).
    x0, y0 = lib.om_unit_get_pos(w, u)
    lib.om_command_move(w, u, x0 + 500.0, y0)
    lib.om_tactical_step(w)
    assert lib.om_unit_get_pos(w, u) != (x0, y0), "walker did not steer (om_walk_route is a contract stub)"
    before = (lib.om_unit_get_layer(w, u), lib.om_unit_transition_progress(w, u), lib.om_unit_get_target_layer(w, u))
    ids = (ctypes.c_uint32 * 1)(u)
    for target in (LAYER + 1, LAYER - 1, 4, 0):
        assert lib.om_command_set_layer(w, ids, 1, target) == 0
        for _ in range(PROBE_TICKS):
            lib.om_tactical_step(w)
            assert lib.om_unit_get_layer(w, u) == before[0], f"layer order {target} moved the walker"
            assert lib.om_unit_transition_progress(w, u) == 0.0, f"layer order {target} started a transfer"
            assert lib.om_unit_get_target_layer(w, u) == before[2], f"layer order {target} set a target layer"


def test_R_001_07_a_flyer_still_makes_a_timed_transfer_on_a_layer_order(lib, world_factory):
    """Guard (passes today): the same order to a flying Raider on open ground is a timed transfer (S-004)."""
    w = _world(lib, world_factory)
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_FLYING) == 0
    u = lib.om_unit_spawn(w, RAIDER, FRIEND, 8000.0, 8000.0, 3)
    assert u != 0
    ids = (ctypes.c_uint32 * 1)(u)
    assert lib.om_command_set_layer(w, ids, 1, 4) == 0
    for _ in range(PROBE_TICKS):
        lib.om_tactical_step(w)
    assert lib.om_unit_get_layer(w, u) == 4


# ---- sight and fire agree (spec: "one helper, both sides"), R-005-10 ----
EYE_WU = 50.0                # OM_TP_SIGHT_EYE_HEIGHT default (provisional, 2026-10-06)
SAMPLE_WU = 25.0
OWN_CELL_WU = 50.0           # samples strictly nearer than this to either end are skipped
PAIRS = 100
FIXED_BLOCKED = ((8346.0, 11858.0), (8667.0, 12117.0))     # band 3 both, a rise between them
FIXED_CLEAR = ((9644.0, 2774.0), (10099.0, 2779.0))        # band 3 both, open between them
MARGIN_WU = 5.0              # provisional (2026-10-06): the fixed pairs must clear/block by more than this


def _ref_margin(lib, w, p0, p1):
    """Independent reference of om_terrain_sight_blocks for two units on layer 2 (band 3): the largest amount any
    sample's terrain height exceeds the sight line (positive = blocked, negative = clear), eye = max(ground, layer
    floor) + EYE_WU at each end, samples every 25 wu skipping those under 50 wu from an end."""
    hs = (ctypes.c_double * 8)()
    lib.om_terrain_band_heights(w, hs, 8)
    floor = hs[LAYER]
    H = lambda x, y: lib.om_terrain_height_at(w, x, y)
    e0 = max(H(*p0), floor) + EYE_WU
    e1 = max(H(*p1), floor) + EYE_WU
    d = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
    worst, t = -1e9, SAMPLE_WU
    while t <= d:
        if t >= OWN_CELL_WU and d - t >= OWN_CELL_WU:
            f = t / d
            worst = max(worst, H(p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f) - (e0 + (e1 - e0) * f))
        t += SAMPLE_WU
    return worst


def _ground_pair_world(lib, world_factory):
    w = _world(lib, world_factory)
    assert lib.om_set_era_kind(w, 1) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, OM_MOVE_FLYING) == 0
    a = lib.om_unit_spawn(w, RAIDER, 0, 8000.0, 8000.0, LAYER)
    b = lib.om_unit_spawn(w, RAIDER, 1, 8100.0, 8000.0, LAYER)
    assert a and b
    return w, a, b


def _put(lib, w, a, b, p0, p1):
    lib.om_unit_set_pos(w, a, p0[0], p0[1])
    lib.om_unit_set_pos(w, b, p1[0], p1[1])


def test_R_005_10_the_fixed_pair_across_a_rise_is_blocked_for_sight_and_for_fire(lib, world_factory):
    """Stated answer: the rise between (8346, 11858) and (8667, 12117) stands above the line of sight, so sight
    blocks (1) and a shot is refused (0). The reference margin is checked so the pair cannot be right by luck."""
    w, a, b = _ground_pair_world(lib, world_factory)
    _put(lib, w, a, b, *FIXED_BLOCKED)
    assert _ref_margin(lib, w, *FIXED_BLOCKED) > MARGIN_WU, "fixed blocked pair is not blocked by the reference"
    assert lib.om_terrain_sight_blocks(w, LAYER, *FIXED_BLOCKED[0], LAYER, *FIXED_BLOCKED[1]) == 1
    assert lib.om_combat_can_shoot(w, a, b) == 0


def test_R_005_10_the_fixed_pair_over_open_ground_is_clear_for_sight_and_for_fire(lib, world_factory):
    """Stated answer: (9644, 2774) to (10099, 2779) has nothing above the line: sight 0, shot allowed 1."""
    w, a, b = _ground_pair_world(lib, world_factory)
    _put(lib, w, a, b, *FIXED_CLEAR)
    assert _ref_margin(lib, w, *FIXED_CLEAR) < -MARGIN_WU, "fixed clear pair is not clear by the reference"
    assert lib.om_terrain_sight_blocks(w, LAYER, *FIXED_CLEAR[0], LAYER, *FIXED_CLEAR[1]) == 0
    assert lib.om_combat_can_shoot(w, a, b) == 1


def test_R_005_10_sight_and_fire_agree_on_100_sampled_pairs_in_a_ground_era(lib, world_factory):
    w, a, b = _ground_pair_world(lib, world_factory)
    rng = random.Random(SEED)
    blocked = clear = 0
    while blocked + clear < PAIRS:
        x, y = rng.uniform(1000.0, 15000.0), rng.uniform(1000.0, 15000.0)
        dx, dy = rng.uniform(-400.0, 400.0), rng.uniform(-400.0, 400.0)
        p0, p1 = (x, y), (x + dx, y + dy)
        if lib.om_terrain_band_at(w, *p0) != LAYER + 1 or lib.om_terrain_band_at(w, *p1) != LAYER + 1:
            continue
        if ((dx * dx + dy * dy) ** 0.5) < 2 * OWN_CELL_WU:
            continue
        m = _ref_margin(lib, w, p0, p1)
        if abs(m) <= MARGIN_WU:
            continue
        _put(lib, w, a, b, p0, p1)
        sight = lib.om_terrain_sight_blocks(w, LAYER, *p0, LAYER, *p1)
        fire = lib.om_combat_can_shoot(w, a, b)
        assert sight == (1 if m > 0 else 0), f"pair {p0} {p1}: sight {sight}, reference margin {m:.1f}"
        assert fire == 1 - sight, f"pair {p0} {p1}: sight {sight} but fire {fire}"
        blocked += m > 0
        clear += m < 0
    assert blocked > 0 and clear > 0, f"positive control: {blocked} blocked, {clear} clear pairs sampled"
