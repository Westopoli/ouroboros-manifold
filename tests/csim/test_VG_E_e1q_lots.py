"""Visible-game lane E1 part c, piece E1q-lots: lots on the density field, no block, no appear timer
(docs/northstar/plans/2026-10-07-visible-game-spec.md rev 10d+, "Lane E1 part c: the settlement port", the E1q-lots and Tests
paragraphs; bible R-193-05 stages, R-193-09 lanes, Q-193-02 thresholds, S:176-177 buildable, S:239-246 cliff; mockup
scenes/mockups/settlement/settlement_sim.gd (S) at ff2ed55f, read-only). Fenced: builders never edit this file. Written on the K-e5
tree (rules.md (d)): old block layout of 36 lots, ids from n_lots, density on the legacy 120 grid.

Rules proved (E1q-lots): every LOT_RISE_TICKS 20 ticks the lot step gives a stage-1 lot, at the cell centre
((gx + 0.5) * 100, (gy + 0.5) * 100) and with id = next_lot_id++, to every buildable cell with D >= 0.10 and no lot. A cell is
buildable when water == 0 (height >= 0 cm), wdist > SHORE_MARGIN 1 (more than one cell, Chebyshev, from water), lane == 0
(gx % 4 == 3 or gy % 4 == 3) and it is not inside the 5 x 5 footprint of a lot with owner >= 0 (no placed lot stands in the
natural-growth scenes, so that clause is not exercised here). A lot's target stage is the number of thresholds
(0.10, 0.22, 0.38, 0.58) its cell's D has passed, at most 3 where slope > 0.22; it rises one stage per lot step and never falls
except to rubble (E1d). OM_LOT_CAP (read from csrc/om_internal.h, 2048, DRAFT-lot-cap) stops creation.

How the rules are checked. The expected cells are derived in this file from the heights the test set through the K-e5 hook
(water, wdist by 8-neighbour BFS capped at 8, lane, slope as FM:380-402 / spec: mean |dh| over the orthogonal neighbours that
exist, in wu per cell, over 6.25, clamped to 1) and from D read through om_density_at at the cell centre; the lot table is read
through om_lot_count / om_lot_get_at; lot_hit_tick through the save bytes. A lot that took an area hit (lot_hit_tick != 0) is
left out of the stage-equality checks, since E1d lowers it. Lots are created at the lot step that follows the growth step that
lifts D over 0.10 (60 is a multiple of 20, so they run on the same tick), so every read between steps sees lots current with D.

Fixtures (all a ground mission, seed 7, objective cell (119, 104) of 240 x 240 cells, set through the K-e5 hook after
om_mission_begin; the player's HOME region 0 carries the economy; econ = economy / OM_FIELD_MAX 100):
  SEA   flat 7000 cm with a three-cell sea strip at columns cx + 6 .. cx + 8, economy 40, read after 1200 steps.
  CONE  an island of Chebyshev radius 24 about the core whose height rises 70 wu per ring (-500 cm sea outside), economy 100,
        read after 9000 steps: the island's field has stopped changing, so lots have finished rising and the stage can be checked
        for equality; the rings give all four stages.
  CLIFF columns <= cx - 12 sea, cx - 11 .. cx flat, east of cx a tilt of 300 wu per cell (slope 0.24 > 0.22), economy 100,
        read after 6100 steps.
  FLAT  flat 7000 cm everywhere, economy 40 (economy 100 for the cap).

NEEDS the new field (E1q-field) to be green? Each case says. "yes" = the case cannot be green with the lots builder alone, since
it reads the derived grids (water, wdist, lane, slope_q) or the 100 wu field that E1q-field fills; "no" = a lots-only build on the
K-e5 tree can turn it green. Positive controls (test_control_*) are green on the K-e5 tree.
"""
import ctypes
import pathlib
import re
import struct


import conftest as C
from conftest import OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region
from test_VG_E_ke5 import LOT_CAP as KE5_LOT_CAP, locate, read_block

REPO = pathlib.Path(__file__).resolve().parents[2]
W = ctypes.c_void_p
P = ctypes.POINTER
U32, I32, F64 = ctypes.c_uint32, ctypes.c_int32, ctypes.c_double

SEED = 7
CANVAS_WU = 24000.0
CELL_WU = 100.0
SIDE = 240
FLAT_CM = 7000
SEA_CM = -500
LANE_PERIOD, LANE_PHASE = 4, 3
SHORE_MARGIN = 1
WDIST_CAP, WDIST_NONE = 8, 255
SLOPE_NORM = 6.25
CLIFF_SLOPE, CLIFF_MAX_STAGE = 0.22, 3
THRESH = (0.10, 0.22, 0.38, 0.58)
OM_LOT_CAP = int(re.search(r"#define\s+OM_LOT_CAP\s+(\d+)", (REPO / "csrc/om_internal.h").read_text()).group(1))


class Lot(ctypes.Structure):
    _fields_ = [("id", U32), ("x", F64), ("y", F64), ("stage", I32), ("building", I32), ("owner", I32)]


# ------------------------------------------------------------------------------------------------ fixtures

def bind(lib):
    sig = {
        "om_density_at": ([W, F64, F64], F64),
        "om_terrain_generate": ([W, ctypes.c_uint64, F64, F64], ctypes.c_int),
        "om_terrain_cells": ([W, P(U32), P(U32)], U32),
        "om_terrain_get_heights": ([W, P(I32), U32], U32),
        "om_terrain_set_heights": ([W, P(I32), U32, U32], ctypes.c_int),
        "om_world_step": ([W], ctypes.c_uint64),
        "om_mission_begin": ([W], None),
        "om_save_state_size": ([W], U32),
        "om_save_state_write": ([W, P(ctypes.c_uint8), U32], None),
        "om_load_state_read": ([W, P(ctypes.c_uint8), U32], ctypes.c_int),
        "om_lot_count": ([W], U32),
        "om_lot_get_at": ([W, U32, P(Lot)], ctypes.c_int),
        "om_economy_place": ([W, I32, F64, F64], ctypes.c_int),
        "om_player_faction": ([W], I32),
    }
    for name, (args, res) in sig.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, res


def scene(lib, make, *, seed=SEED, economy=40.0, terrain=None, setup=True):
    """A generated ground mission, begun; `terrain` is fn(gx, gy, cx, cy) -> cm over the 240 x 240 cells (cx, cy the cell that
    holds the mission objective), set through the K-e5 hook before the first step. setup=False stops before om_mission_setup."""
    bind(lib)
    w = make(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, 0, OMArchetype.PLAYER)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=10.0, economy=economy, population=10.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=10.0, faction_id=1)
    assert lib.om_set_era_kind(w, 1) == 0
    assert lib.om_terrain_generate(w, seed, CANVAS_WU, CANVAS_WU) in (0, 1)
    if not setup:
        return w
    lib.om_mission_setup(w, 0, 3, 0)
    lib.om_mission_begin(w)
    if terrain is not None:
        cx, cy = objective_cell(lib, w)
        cm = (I32 * (SIDE * SIDE))(*[terrain(i % SIDE, i // SIDE, cx, cy) for i in range(SIDE * SIDE)])
        assert lib.om_terrain_set_heights(w, cm, SIDE, SIDE) == 1, "the K-e5 hook refused the synthetic terrain"
    return w


def objective_cell(lib, w):
    v = C.OMVec2()
    assert lib.om_objective_get_center(w, 0, ctypes.byref(v)) == 1, "the mission has no objective node"
    return int(v.x // CELL_WU), int(v.y // CELL_WU)


def flat(gx, gy, cx, cy):
    return FLAT_CM


def sea_strip(gx, gy, cx, cy):
    return SEA_CM if cx + 6 <= gx <= cx + 8 else FLAT_CM


def cone_island(gx, gy, cx, cy):
    r = max(abs(gx - cx), abs(gy - cy))
    return FLAT_CM + 7000 * r if r <= 24 else SEA_CM


def cliff_east(gx, gy, cx, cy):
    if gx <= cx - 12:
        return SEA_CM
    return FLAT_CM if gx <= cx else FLAT_CM + 30000 * (gx - cx)


def steps(lib, w, n):
    for _ in range(n):
        lib.om_world_step(w)


def d_at(lib, w, gx, gy):
    return lib.om_density_at(w, (gx + 0.5) * CELL_WU, (gy + 0.5) * CELL_WU)


def heights(lib, w):
    cw, ch = U32(), U32()
    n = lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    out = (I32 * max(n, 1))()
    got = lib.om_terrain_get_heights(w, out, n)
    assert (cw.value, ch.value) == (SIDE, SIDE) and got == SIDE * SIDE
    return list(out[:got])


def lots(lib, w):
    out = []
    for i in range(lib.om_lot_count(w)):
        r = Lot()
        assert lib.om_lot_get_at(w, i, ctypes.byref(r)) == 0
        out.append((r.id, r.x, r.y, r.stage, r.building, r.owner))
    return out


def cell_of(lot):
    return int(lot[1] // CELL_WU), int(lot[2] // CELL_WU)


def save(lib, w):
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    return bytes(buf)


def load(lib, w, data):
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    return lib.om_load_state_read(w, buf, len(data))


def hit_ticks(lib, w):
    """lot_hit_tick[OM_LOT_CAP] of the saved economy block (indexed by lot position), 0 = never hit."""
    data = save(lib, w)
    blk = locate(lib, w, data)
    assert blk is not None, "the economy block of the save does not parse under the K-e5 layout"
    tail = read_block(data, blk)["tail"]
    return struct.unpack_from(f"<{KE5_LOT_CAP}I", tail, len(tail) - 4 * KE5_LOT_CAP)


# ------------------------------------------------------------------------------------------------ the rules, as detectors

def is_lane(gx, gy):
    return gx % LANE_PERIOD == LANE_PHASE or gy % LANE_PERIOD == LANE_PHASE


def wdist_grid(h, side=SIDE):
    """Chebyshev distance to the nearest water cell (height < 0) by 8-neighbour BFS to depth WDIST_CAP; WDIST_NONE beyond."""
    wd = [WDIST_NONE] * (side * side)
    queue = [i for i, v in enumerate(h) if v < 0]
    for i in queue:
        wd[i] = 0
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        if wd[i] >= WDIST_CAP:
            continue
        cx, cy = i % side, i // side
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < side and 0 <= ny < side and wd[ny * side + nx] == WDIST_NONE:
                    wd[ny * side + nx] = wd[i] + 1
                    queue.append(ny * side + nx)
    return wd


def slope_grid(h, side=SIDE):
    """Mean |dh| over the orthogonal neighbours that exist, in wu, per 100 wu cell, over SLOPE_NORM, clamped to 1."""
    out = [0.0] * (side * side)
    for i in range(side * side):
        gx, gy = i % side, i // side
        nb = [h[j] for ok, j in ((gx > 0, i - 1), (gx < side - 1, i + 1), (gy > 0, i - side), (gy < side - 1, i + side)) if ok]
        out[i] = min(1.0, (sum(abs(h[i] - v) for v in nb) / len(nb)) / CELL_WU / CELL_WU / SLOPE_NORM)
    return out


def stage_of(d):
    """Target stage: the number of thresholds D has passed."""
    return sum(1 for t in THRESH if d >= t)


def buildable(gx, gy, h, wd):
    i = gy * SIDE + gx
    return h[i] >= 0 and wd[i] > SHORE_MARGIN and not is_lane(gx, gy)


def eligible_cells(lib, w, h, wd):
    """{(gx, gy): D} for every buildable cell whose density has reached the first threshold."""
    out = {}
    for i in range(SIDE * SIDE):
        gx, gy = i % SIDE, i // SIDE
        if buildable(gx, gy, h, wd):
            d = d_at(lib, w, gx, gy)
            if d >= THRESH[0]:
                out[(gx, gy)] = d
    return out


def classify(cell, d, h, wd):
    """Why a lot standing on `cell` is wrong, or None."""
    gx, gy = cell
    i = gy * SIDE + gx
    if h[i] < 0:
        return "in the sea"
    if wd[i] <= SHORE_MARGIN:
        return "within one cell of the sea"
    if is_lane(gx, gy):
        return "on a lane cell"
    if d < THRESH[0]:
        return "on density below 0.10"
    return None


# ------------------------------------------------------------------------------------------------ controls (green on the K-e5 tree)

def test_control_hook_sets_flat_land_and_density_reads_zero_before_setup(lib, world_factory):
    """Positive control, same fixture as every case below. om_density_at answers 0.0 before om_mission_setup (K-e5 pre-setup
    test); on the begun ground mission the hook sets a flat terrain, returns 1, the heights read back, and the lot table is
    readable (zero lots before any step)."""
    pre = scene(lib, world_factory, setup=False)
    for x, y in [(12000.0, 12000.0), (11950.0, 10450.0), (0.0, 0.0)]:
        assert lib.om_density_at(pre, x, y) == 0.0
    w = scene(lib, world_factory, terrain=flat)
    assert heights(lib, w) == [FLAT_CM] * (SIDE * SIDE)
    assert lots(lib, w) == []


def test_control_rule_model_detectors():
    """CONTROL: the derived-rule model on synthetic data. Lanes at gx % 4 == 3 or gy % 4 == 3; wdist 1 beside water and WDIST_NONE
    beyond the cap; slope 0 flat, 0.24 on a 300 wu per cell tilt; the stage mapping at and around each threshold; the lot
    classifier fires on a lane cell, a sea cell, a shore cell and a thin-density cell and is quiet on a good cell."""
    assert [is_lane(g, 0) for g in range(8)] == [False, False, False, True, False, False, False, True]
    assert is_lane(1, 3) and not is_lane(1, 2)
    h = [FLAT_CM] * (SIDE * SIDE)
    h[100 * SIDE + 100] = SEA_CM
    wd = wdist_grid(h)
    assert wd[100 * SIDE + 100] == 0 and wd[100 * SIDE + 101] == 1 and wd[101 * SIDE + 101] == 1 and wd[100 * SIDE + 102] == 2
    assert wd[100 * SIDE + 100 + WDIST_CAP] == WDIST_CAP and wd[100 * SIDE + 100 + WDIST_CAP + 1] == WDIST_NONE
    tilt = [FLAT_CM + 30000 * (i % SIDE) for i in range(SIDE * SIDE)]
    assert slope_grid([FLAT_CM] * (SIDE * SIDE))[5000] == 0.0
    assert abs(slope_grid(tilt)[100 * SIDE + 100] - 0.24) < 1e-9
    assert [stage_of(d) for d in (0.0, 0.0999, 0.10, 0.2199, 0.22, 0.3799, 0.38, 0.5799, 0.58, 3.0)] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    assert classify((101, 100), 0.5, h, wd) == "within one cell of the sea"
    assert classify((100, 100), 0.5, h, wd) == "in the sea"
    assert classify((103, 50), 0.5, h, wd) == "on a lane cell"
    assert classify((50, 50), 0.05, h, wd) == "on density below 0.10"
    assert classify((50, 50), 0.5, h, wd) is None
    assert buildable(50, 50, h, wd) and not buildable(103, 50, h, wd)


def test_control_flat_world_has_lots_to_read(lib, world_factory):
    """CONTROL (green on the K-e5 tree too): after 600 steps on flat land the lot table has rows of the documented shape."""
    w = scene(lib, world_factory, terrain=flat)
    steps(lib, w, 600)
    rows = lots(lib, w)
    assert rows, "no lots after 600 steps on flat land"
    assert all(r[1] >= 0.0 and r[2] >= 0.0 and 0 <= r[3] <= 5 for r in rows)


# ------------------------------------------------------------------------------------------------ where lots stand

def test_a_lot_exists_on_every_buildable_cell_with_density_and_nowhere_below(lib, world_factory):
    """E1q-lots (Tests): after 1200 steps on SEA, the set of cells that hold a lot equals the set of buildable cells with
    D >= 0.10 (a lot on each, none elsewhere), each lot at its cell centre. Control: the set is non-empty and under OM_LOT_CAP.
    NEEDS E1q-field: yes (water, wdist and lane come from om_density_rebuild_inputs; D is the 100 wu field). Red on the K-e5
    tree: the block of 36 lots at 200 wu spacing."""
    w = scene(lib, world_factory, terrain=sea_strip)
    steps(lib, w, 1200)
    h = heights(lib, w)
    want = eligible_cells(lib, w, h, wdist_grid(h))
    assert len(want) >= 50, f"control: only {len(want)} eligible cells, the set comparison would be vacuous"
    rows = lots(lib, w)
    for r in rows:
        gx, gy = cell_of(r)
        assert (r[1], r[2]) == ((gx + 0.5) * CELL_WU, (gy + 0.5) * CELL_WU), f"lot {r[0]} is not at a cell centre: ({r[1]}, {r[2]})"
    have = {cell_of(r) for r in rows}
    assert len(have) == len(rows), "two lots share a cell"
    missing, extra = sorted(set(want) - have), sorted(have - set(want))
    assert not missing, f"{len(missing)} buildable cells with D >= 0.10 hold no lot, first {missing[:3]} (D {want[missing[0]]})"
    assert not extra, f"{len(extra)} lots stand on cells that are not buildable with D >= 0.10, first {extra[:3]}"
    assert len(want) < OM_LOT_CAP, f"premise: {len(want)} eligible cells reach the cap {OM_LOT_CAP}, so a lot per cell is not expected"


def test_no_lot_on_a_lane_cell_in_the_sea_or_within_one_cell_of_it(lib, world_factory):
    """E1q-lots (Tests, S:176-177 and R-193-09): of the lots on SEA after 1200 steps none is on a lane cell (every fourth row
    and column), in the sea, or within one cell of it, and none stands on D < 0.10. Controls: lots exist on both sides of the
    strip, and the land beside the strip does hold lots at two cells' distance from the water (so the margin test is not
    satisfied by an empty shore). NEEDS E1q-field: yes (the derived grids). Red on the K-e5 tree: the block ignores them."""
    w = scene(lib, world_factory, terrain=sea_strip)
    cx, cy = objective_cell(lib, w)
    steps(lib, w, 1200)
    h = heights(lib, w)
    wd = wdist_grid(h)
    rows = lots(lib, w)
    assert rows, "no lots after 1200 steps on SEA"
    bad = {}
    for r in rows:
        cell = cell_of(r)
        why = classify(cell, d_at(lib, w, *cell), h, wd)
        if why:
            bad.setdefault(why, []).append(cell)
    assert not bad, "lots on cells that are not buildable: " + "; ".join(f"{len(v)} {k}, first {v[:2]}" for k, v in sorted(bad.items()))
    cells = {cell_of(r) for r in rows}
    assert any(gx < cx + 6 for gx, _ in cells) and any(gx > cx + 8 for gx, _ in cells), "control: lots on only one side of the strip"
    assert any(wd[gy * SIDE + gx] == SHORE_MARGIN + 1 for gx, gy in cells), "control: no lot two cells from the water"


# ------------------------------------------------------------------------------------------------ stages

def test_lot_stage_equals_the_threshold_count(lib, world_factory):
    """E1q-lots (Tests, R-193-05, Q-193-02): on CONE after 9000 steps (the field has stopped changing) every lot that took no
    area hit stands at the number of thresholds (0.10, 0.22, 0.38, 0.58) its cell's D has passed. Controls: the field is quiet
    between steps 8940 and 9000; at least 200 lots are checked and all four stages 1 to 4 occur (the equality is not vacuous).
    NEEDS E1q-field: no (the stage rule reads only D; a lots-only build with the legacy field can turn it green if that field is
    quiet by then). Red on the K-e5 tree: stage there is 1 + count (TD-VG-E-19 retires that)."""
    w = scene(lib, world_factory, terrain=cone_island, economy=100.0)
    steps(lib, w, 8940)
    before = [d_at(lib, w, i % SIDE, i // SIDE) for i in range(SIDE * SIDE)]
    steps(lib, w, 60)
    after = [d_at(lib, w, i % SIDE, i // SIDE) for i in range(SIDE * SIDE)]
    assert before == after, f"premise: {sum(1 for a, b in zip(before, after) if a != b)} cells still change at tick 9000"
    rows, hits = lots(lib, w), hit_ticks(lib, w)
    checked, wrong = [], []
    for k, r in enumerate(rows):
        if hits[k] != 0 or r[3] == 0:
            continue
        d = d_at(lib, w, *cell_of(r))
        checked.append(r[3])
        if r[3] != stage_of(d):
            wrong.append((r[0], r[3], stage_of(d), d))
    assert not wrong, f"{len(wrong)} lots off their threshold count, first (id, stage, target, D) {wrong[:3]}"
    assert len(checked) >= 200, f"control: only {len(checked)} unhit lots checked of {len(rows)}"
    assert set(checked) == {1, 2, 3, 4}, f"control: stages seen {sorted(set(checked))}"


def test_a_steep_cell_never_stands_above_stage_3(lib, world_factory):
    """E1q-lots (S:239-246): on CLIFF after 6100 steps no lot on a cell with slope > 0.22 stands above stage 3, and no lot of
    any kind stands above its target. Controls: some steep-cell lot has a target of 4 (D >= 0.58) and stands at exactly 3 (the
    cap is what held it), and some level-cell lot stands at 4 (stage 4 is reachable on this map). NEEDS E1q-field: yes
    (slope_q). Red on the K-e5 tree: no lot stands on the steep cells with a cap."""
    w = scene(lib, world_factory, terrain=cliff_east, economy=100.0)
    steps(lib, w, 6100)
    h = heights(lib, w)
    sl = slope_grid(h)
    rows = lots(lib, w)
    above, capped, level4, steep_target4 = [], 0, 0, 0
    for r in rows:
        gx, gy = cell_of(r)
        steep = sl[gy * SIDE + gx] > CLIFF_SLOPE
        target = stage_of(d_at(lib, w, gx, gy))
        if r[3] > target or (steep and r[3] > CLIFF_MAX_STAGE):
            above.append((r[0], (gx, gy), r[3], target, steep))
        if steep and target >= 4:
            steep_target4 += 1
            capped += r[3] == CLIFF_MAX_STAGE
        level4 += (not steep) and r[3] == 4
    assert not above, f"{len(above)} lots above their allowed stage, first (id, cell, stage, target, steep) {above[:3]}"
    assert steep_target4 >= 1, "control: no steep-cell lot has a target of 4"
    assert capped >= 1, f"control: none of {steep_target4} steep lots with a target of 4 stands at stage 3"
    assert level4 >= 1, "control: no level-cell lot stands at stage 4"


# ------------------------------------------------------------------------------------------------ ids

def test_lot_ids_strictly_ascend_and_survive_a_save_round_trip(lib, world_factory):
    """E1q-lots (next_lot_id, saved): on FLAT after 1200 steps the ids ascend strictly from 1 or more; a save loaded into a fresh
    mission gives the same table, and 600 more steps on both give the same table again, with every new id above the largest
    earlier one (the counter was saved). NEEDS E1q-field: no (guard; the legacy code numbers n_lots + 1, also ascending)."""
    src = scene(lib, world_factory, terrain=flat)
    steps(lib, src, 1200)
    before = lots(lib, src)
    ids = [r[0] for r in before]
    assert len(ids) > 1 and ids[0] >= 1 and all(a < b for a, b in zip(ids, ids[1:])), "ids do not strictly ascend"
    dst = scene(lib, world_factory, terrain=flat)
    assert load(lib, dst, save(lib, src)) == 0
    assert lots(lib, dst) == before, "the lot table changed through a save round trip"
    steps(lib, src, 600)
    steps(lib, dst, 600)
    after = lots(lib, src)
    assert after == lots(lib, dst), "the loaded world grows different lots from the uninterrupted one"
    new = [r[0] for r in after if r[0] not in set(ids)]
    assert new, "control: no lot appeared in the 600 steps after the save"
    assert min(new) > max(ids) and [r[0] for r in after] == sorted(set(r[0] for r in after)), "new ids reuse or precede earlier ones"


def test_a_placed_lots_id_is_unique(lib, world_factory):
    """E1q-lots (economy_place.c uses the same counter): on FLAT after 1200 steps, om_economy_place at a free walkable cell 80
    cells east of the core is accepted and the new lot (owner the player's faction) has an id no other lot has and above every
    earlier id; 300 more steps keep every id unique and ascending. Control: the placement is accepted and the lot is there.
    NEEDS E1q-field: no. Red on the K-e5 tree: the placed lot takes id = n_lots, the id of the last natural lot."""
    w = scene(lib, world_factory, terrain=flat)
    cx, cy = objective_cell(lib, w)
    steps(lib, w, 1200)
    before = lots(lib, w)
    assert before, "no lots to be unique against"
    x, y = (cx + 80 + 0.5) * CELL_WU, (cy + 0.5) * CELL_WU
    assert lib.om_economy_place(w, 3, x, y) == 0, "control: the placement was refused"
    after = lots(lib, w)
    placed = [r for r in after if r[5] >= 0]
    assert len(placed) == 1 and cell_of(placed[0]) == (cx + 80, cy), f"control: the placed lot is not there: {placed}"
    assert placed[0][5] == lib.om_player_faction(w)
    ids = [r[0] for r in after]
    assert len(set(ids)) == len(ids), f"duplicate lot id after a placement: the placed lot has id {placed[0][0]}, earlier ids end {ids[-3:-1]}"
    assert placed[0][0] > max(r[0] for r in before), "the placed lot's id does not exceed every earlier id"
    steps(lib, w, 300)
    ids = [r[0] for r in lots(lib, w)]
    assert len(set(ids)) == len(ids) and ids == sorted(ids), "ids stopped being unique and ascending after more growth"


# ------------------------------------------------------------------------------------------------ count and cap

def test_more_than_36_lots_on_a_flat_open_canvas_after_1200_ticks(lib, world_factory):
    """E1q-lots (Tests): there is no block; on FLAT after 1200 ticks the lot count exceeds 36, the old block's ceiling.
    NEEDS E1q-field: no. Red on the K-e5 tree: exactly 36."""
    w = scene(lib, world_factory, terrain=flat)
    steps(lib, w, 1200)
    n = lib.om_lot_count(w)
    assert n > 36, f"{n} lots after 1200 ticks on a flat open canvas (the old block of 10 x 10 cells holds 36)"


def test_at_the_lot_cap_no_further_lot_appears_on_an_eligible_cell(lib, world_factory):
    """E1q-lots (OM_LOT_CAP, DRAFT-lot-cap): on FLAT with economy 100 the cap is filled in a bounded run (2400 steps; the define
    is read from csrc/om_internal.h and is not lowered), the count stands at OM_LOT_CAP, and 600 steps later it still does
    while buildable cells with D >= 0.10 and no lot exist. Control: such a cell exists at the cap, and the lot count fell short of
    the cap before the field reached far (step 600). NEEDS E1q-field: no. Red on the K-e5 tree: 36 lots."""
    w = scene(lib, world_factory, terrain=flat, economy=100.0)
    steps(lib, w, 600)
    assert lib.om_lot_count(w) < OM_LOT_CAP, "control: the cap was already full at step 600"
    steps(lib, w, 1800)
    assert lib.om_lot_count(w) == OM_LOT_CAP, f"{lib.om_lot_count(w)} lots after 2400 steps on a large flat canvas, the cap is {OM_LOT_CAP}"
    h = heights(lib, w)
    wd = wdist_grid(h)

    def starved():
        have = {cell_of(r) for r in lots(lib, w)}
        return [c for c in eligible_cells(lib, w, h, wd) if c not in have]
    assert starved(), "control: at the cap every eligible cell already holds a lot, the cap case would be vacuous"
    steps(lib, w, 600)
    assert lib.om_lot_count(w) == OM_LOT_CAP, "a lot appeared beyond OM_LOT_CAP"
    assert starved(), "every eligible cell holds a lot after 600 more steps"
