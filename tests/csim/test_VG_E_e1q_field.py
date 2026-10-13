"""Visible-game lane E1 part c, piece E1q-field: the settlement density field ported from the approved mockup
(docs/northstar/plans/2026-10-07-visible-game-spec.md rev 10d+, "Lane E1 part c: the settlement port", the E1q-field and Tests
paragraphs; bible R-193-01, R-166-01/02, Q-166-02, Q-193-07 (a); mockup scenes/mockups/settlement/settlement_sim.gd (S) and
scenes/mockups/landscape/field_map.gd (FM) at ff2ed55f, read-only). Fenced: builders never edit this file. Written on the K-e5
tree (rules.md (d)): old growth on the legacy 120 grid, om_density_rebuild_inputs a no-op, om_terrain_set_heights present.

How the field is read. Through the public getters only: om_density_at at the centre of each 100 wu terrain cell
((gx + 0.5) * 100, (gy + 0.5) * 100), the mission objective through om_objective_get_center (read right after om_mission_begin,
before any step: the objective centre may drift later), and the saved economy block through the save bytes (density_side, P,
n_active, active, core_cell), parsed with the K-e5 test's locate / read_block (tests/csim/test_VG_E_ke5.py, fenced, same layout).

Fixtures. A ground mission: era kind 1, om_terrain_generate(seed 7, 24000 x 24000) = 240 x 240 cells of 100 wu,
om_mission_setup(region 0, archetype 3), om_mission_begin. The player's HOME region 0 carries the economy (K-e3 samples it
once at init: density_economy; the field's econ term is density_economy / OM_FIELD_MAX 100, so economy 40 is econ 0.4).
Synthetic terrains are set right after om_mission_begin through om_terrain_set_heights (the K-e5 hook), before the first step, so
growth meets them from tick 0. Flat land is 7000 cm (the dry test is strict: heights of at least 6000 cm; 7000 is above the
dry level), sea is -500 cm (water = elev_cm < 0, spec E1q-field). Growth runs at tick % 60 == 0 starting at tick 0 (csrc/economy.c
om_economy_step is called with the tick before the increment): 60 * k world steps are k growth steps.

Needs the new field (E1q-field) to be green? Marked "NEEDS E1q-field: yes" in each case; a "no" case is a guard that is already
green on the K-e5 tree and must stay green. Positive controls (test_control_*) are green on the K-e5 tree.

Cases the spec lists that this file narrows (Architect ruling 2026-10-11):
 - 8-fold symmetry: the spec's growth order (in place, NW N NE W E SW S SE) keeps the transposition exactly but breaks the
   mirrors and quarter turns by 1 to 3 Q16 units (1.5e-5 each) from the order the float products and the Q16 truncation meet
   (a Python model of the spec's formulas, checked 6, 12 and 30 steps, econ 0.4 and 1.0). The exact transposition case is the
   positive control of the full-group case, which asserts DRAFT_SYMMETRY_ULPS (a named draft, Q-193-08).
 - "D == 0 in the sea": dropped; the spec is amended. The sea strip claim stays in test_a_sea_strip_lowers_density_just_across_it.
Core cell. The spec reads the core from the mission objective (Q-193-07 (a)); this file takes the cell that holds the objective
centre (floor(x / 100), floor(y / 100)); the mockup's round() has no sim counterpart because sim cells have their centres at
(g + 0.5) * 100. test_core_cell_is_the_cell_holding_the_objective pins it.
Named drafts: DRAFT-density-budget 2 ms per growth step, printed by the timing control, not asserted; DRAFT-symmetry-ulps 4 Q16
units (Q-193-08), asserted by the full-group symmetry case.
"""
import ctypes
import hashlib
import json
import pathlib
import subprocess
import sys
import time


import conftest as C
from conftest import OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region
from test_VG_E_ke5 import locate, read_block, splice

REPO = pathlib.Path(__file__).resolve().parents[2]
W = ctypes.c_void_p
P = ctypes.POINTER
U32, I32, F64 = ctypes.c_uint32, ctypes.c_int32, ctypes.c_double

SEED = 7
CANVAS_WU = 24000.0
CELL_WU = 100.0
SIDE = 240                    # canvas / CELL_WU
GROWTH_TICKS = 60             # OM_DENSITY_RING_TICKS
DRAFT_SYMMETRY_ULPS = 4       # DRAFT-symmetry-ulps, 4 Q16 units, Q-193-08: a named draft, not a ruling
Q16 = 65536.0
FLAT_CM = 7000                # above TG_DRY_LEVEL_WU 60 (= 6000 cm); the dry test is strict
SEA_CM = -500
RIDGE_CM = 900 * 100          # a 900 wu ridge in cm
LEGACY_SIDE = 120
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


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
        "om_world_checksum_full": ([W, P(ctypes.c_uint64), U32], ctypes.c_uint64),
        "om_lot_count": ([W], U32),
    }
    for name, (args, res) in sig.items():
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, res


def scene(lib, make, *, seed=SEED, economy=40.0, terrain=None, setup=True):
    """A generated ground mission, begun; `terrain` (None keeps the generated heights) is fn(gx, gy, cx, cy) -> cm over the
    240 x 240 cells, cx, cy the cell that holds the mission objective, set through the K-e5 hook before the first step.
    setup=False returns the world after terrain generation, before om_mission_setup."""
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


def steps(lib, w, n):
    for _ in range(n):
        lib.om_world_step(w)


def d_at(lib, w, gx, gy):
    return lib.om_density_at(w, (gx + 0.5) * CELL_WU, (gy + 0.5) * CELL_WU)


def grid(lib, w):
    return [d_at(lib, w, i % SIDE, i // SIDE) for i in range(SIDE * SIDE)]


def heights(lib, w):
    cw, ch = U32(), U32()
    n = lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    out = (I32 * max(n, 1))()
    got = lib.om_terrain_get_heights(w, out, n)
    return (cw.value, ch.value), list(out[:got])


def save(lib, w):
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    return bytes(buf)


def load(lib, w, data):
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    return lib.om_load_state_read(w, buf, len(data))


def saved_block(lib, w):
    data = save(lib, w)
    blk = locate(lib, w, data)
    assert blk is not None, "the economy block of the save does not parse under the K-e5 layout"
    return data, blk, read_block(data, blk)


# terrain recipes: fn(gx, gy, cx, cy) -> cm
def flat(gx, gy, cx, cy):
    return FLAT_CM


def sea_strip(gx, gy, cx, cy):
    """Flat land with a sea strip three cells wide, columns cx + 6 .. cx + 8, the full height of the map."""
    return SEA_CM if cx + 6 <= gx <= cx + 8 else FLAT_CM


def ridge(gx, gy, cx, cy):
    """Flat land with a 900 wu ridge four cells wide, columns cx + 5 .. cx + 8, the full height of the map (a sheer wall)."""
    return FLAT_CM + (RIDGE_CM if cx + 5 <= gx <= cx + 8 else 0)


# ------------------------------------------------------------------------------------------------ detectors

def reach_in_every_direction(g_at, core, k):
    """True when the density is above zero at the cell k cells from the core in each of the eight compass directions."""
    cx, cy = core
    return all(g_at(cx + k * dx, cy + k * dy) > 0.0 for dx, dy in DIRS)


def transpose_violations(g_at, core, radius):
    """Cells (dx, dy) in the box of the given radius about the core whose density differs from the transposed cell (dy, dx)."""
    cx, cy = core
    return [(dx, dy) for dy in range(-radius, radius + 1) for dx in range(-radius, radius + 1)
            if g_at(cx + dx, cy + dy) != g_at(cx + dy, cy + dx)]


# ------------------------------------------------------------------------------------------------ controls (green on the K-e5 tree)

def test_control_hook_sets_flat_land_and_density_reads_zero_before_setup(lib, world_factory):
    """Positive control, same fixture as every case below. Before om_mission_setup om_density_at answers 0.0 everywhere (K-e5
    paragraph's pre-setup test); on the begun ground mission the hook sets a flat terrain and returns 1, and the heights read back."""
    pre = scene(lib, world_factory, setup=False)
    for x, y in [(12000.0, 12000.0), (11950.0, 10450.0), (0.0, 0.0), (-5.0, 1e9)]:
        assert lib.om_density_at(pre, x, y) == 0.0
    w = scene(lib, world_factory, terrain=flat)
    dims, got = heights(lib, w)
    assert dims == (SIDE, SIDE) and got == [FLAT_CM] * (SIDE * SIDE)
    cx, cy = objective_cell(lib, w)
    assert 0 <= cx < SIDE and 0 <= cy < SIDE


def test_control_detectors_trip_on_known_grids():
    """CONTROL: the reach and transposition detectors fire on synthetic data and stay quiet on clean data."""
    core = (10, 10)
    full = {(10 + dx, 10 + dy): 1.0 for dx in range(-3, 4) for dy in range(-3, 4)}
    assert reach_in_every_direction(lambda x, y: full.get((x, y), 0.0), core, 3)
    assert not reach_in_every_direction(lambda x, y: full.get((x, y), 0.0), core, 4)
    cut = dict(full)
    del cut[(13, 13)]
    assert not reach_in_every_direction(lambda x, y: cut.get((x, y), 0.0), core, 3)
    sym = {(10 + dx, 10 + dy): 1.0 + 0.1 * (dx + dy) + 0.01 * dx * dy for dx in range(-3, 4) for dy in range(-3, 4)}
    assert transpose_violations(lambda x, y: sym.get((x, y), 0.0), core, 3) == []
    sym[(12, 11)] += 0.5
    assert transpose_violations(lambda x, y: sym.get((x, y), 0.0), core, 3) == [(2, 1), (1, 2)]


def test_control_flat_world_grows_some_density(lib, world_factory):
    """CONTROL (green on the K-e5 tree too): on flat land with economy 40 some cell has density after three growth steps."""
    w = scene(lib, world_factory, terrain=flat)
    steps(lib, w, 3 * GROWTH_TICKS)
    assert max(grid(lib, w)) > 0.0, "no density anywhere after three growth steps on flat land"


# ------------------------------------------------------------------------------------------------ the grid (K-e5 / E1q-field "density_side")

def test_density_side_is_canvas_over_cell(lib, world_factory):
    """E1q-field: density_side comes from om_terrain_cells, one density cell per 100 wu terrain cell: 24000 / 100 = 240, not the
    legacy 120. NEEDS E1q-field: yes. Red on the K-e5 tree: the saved density_side is 120."""
    w = scene(lib, world_factory, terrain=flat)
    (cw, ch), _ = heights(lib, w)
    assert (cw, ch) == (int(CANVAS_WU / CELL_WU),) * 2
    _, blk, f = saved_block(lib, w)
    assert blk["dp"] == 1, "a ground mission has a density field"
    assert f["side"] == cw == ch, f"density_side {f['side']}, canvas / 100 = {cw} (the legacy grid is {LEGACY_SIDE})"


def test_core_cell_is_the_cell_holding_the_objective(lib, world_factory):
    """E1q-field / Q-193-07 (a): the core is the mission objective, saved as core_cell (cell index = gy * side + gx, the cell
    that holds om_objective_get_center). NEEDS E1q-field: yes. Red on the K-e5 tree: core_cell is 60 * 120 + 60."""
    w = scene(lib, world_factory, terrain=flat)
    cx, cy = objective_cell(lib, w)
    _, _, f = saved_block(lib, w)
    assert f["core"] == cy * f["side"] + cx, f"core_cell {f['core']}, the objective cell is ({cx}, {cy}) = {cy * f['side'] + cx}"


# ------------------------------------------------------------------------------------------------ growth on flat land

def test_flat_land_reach_after_k_growth_steps_is_at_least_k(lib, world_factory):
    """E1q-field Tests: on flat synthetic land with no sea, the reach after k growth steps is at least k cells, in every one of
    the eight directions from the core. 60 * k + 1 world steps (k or k + 1 growth steps, whichever tick the first one takes).
    NEEDS E1q-field: yes. Red on the K-e5 tree: its core is the canvas centre, not the objective, so for small k the cells k
    cells from the objective are outside its field."""
    w = scene(lib, world_factory, terrain=flat)
    core = objective_cell(lib, w)
    done = 0
    for k in range(1, 13):
        steps(lib, w, 60 * k + 1 - done)
        done = 60 * k + 1
        assert reach_in_every_direction(lambda x, y: d_at(lib, w, x, y), core, k), (
            f"after {k} growth steps the field does not reach {k} cells from the core {core} in all eight directions")


def test_flat_land_field_is_symmetric_about_the_core_under_transposition(lib, world_factory):
    """E1q-field Tests, narrowed (see the module note): on flat land the field is exactly equal at (dx, dy) and (dy, dx) about
    the core, over the box of radius 10 after ten growth steps. The other symmetries hold to Q16 noise only (the draft-tolerance case below).
    Control first: the box holds at least 100 nonzero cells. NEEDS E1q-field: yes. Red on the K-e5 tree: its field is centred
    on the canvas centre."""
    w = scene(lib, world_factory, terrain=flat)
    core = objective_cell(lib, w)
    steps(lib, w, 60 * 10 + 1)
    g_at = lambda x, y: d_at(lib, w, x, y)
    nonzero = sum(1 for dx in range(-10, 11) for dy in range(-10, 11) if g_at(core[0] + dx, core[1] + dy) > 0.0)
    assert nonzero >= 100, f"control: only {nonzero} nonzero cells in the box, the symmetry check would be vacuous"
    bad = transpose_violations(g_at, core, 10)
    assert bad == [], f"{len(bad)} cells differ from their transpose about the core {core}, first {bad[:3]}"


def test_flat_land_field_is_eight_fold_symmetric_within_the_draft_tolerance(lib, world_factory):
    """Spec Tests (E1q-field), 8-fold symmetry about the core with DRAFT-symmetry-ulps. Positive control: the exact transposition
    case above, plus at least 100 nonzero cells in the box. NEEDS E1q-field: yes. Red on the K-e5 tree: its field is centred on
    the canvas centre."""
    radius = 10
    w = scene(lib, world_factory, terrain=flat)
    cx, cy = objective_cell(lib, w)
    steps(lib, w, 60 * 10 + 1)
    nonzero = sum(1 for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1) if d_at(lib, w, cx + dx, cy + dy) > 0.0)
    assert nonzero >= 100, f"control: only {nonzero} nonzero cells in the box"
    worst, where = 0.0, None
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            here = d_at(lib, w, cx + dx, cy + dy)
            for ox, oy in ((dx, -dy), (-dx, dy), (-dx, -dy), (dy, dx), (dy, -dx), (-dy, dx), (-dy, -dx)):
                gap = abs(here - d_at(lib, w, cx + ox, cy + oy))
                if gap > worst:
                    worst, where = gap, (dx, dy, ox, oy)
    assert worst * Q16 <= DRAFT_SYMMETRY_ULPS, f"widest asymmetry {worst * Q16:.2f} Q16 units at {where} (draft {DRAFT_SYMMETRY_ULPS})"


# ------------------------------------------------------------------------------------------------ water

def test_a_sea_strip_lowers_density_just_across_it(lib, world_factory):
    """E1q-field Tests: with a sea strip (columns cx + 6 .. cx + 8) the density just across it is lower than on the near shore
    at equal ring: the cell k cells east of the core (across) against the cell k cells west (near side), k = 11 and 12, after
    25 growth steps. Control: both are above zero (the reach crosses water at 0.85 per cell). NEEDS E1q-field: yes. Red on the
    K-e5 tree: it has no water, so the two cells are equal."""
    w = scene(lib, world_factory, terrain=sea_strip)
    cx, cy = objective_cell(lib, w)
    _, h = heights(lib, w)
    assert [h[cy * SIDE + cx + d] for d in (5, 6, 7, 8, 9)] == [FLAT_CM, SEA_CM, SEA_CM, SEA_CM, FLAT_CM]
    steps(lib, w, 60 * 25 + 1)
    for k in (11, 12):
        west, east = d_at(lib, w, cx - k, cy), d_at(lib, w, cx + k, cy)
        assert west > 0.0 and east > 0.0, f"control: ring {k} west {west} east {east}, the field must reach both"
        assert east < west, f"ring {k}: density across the sea {east} is not lower than on the near shore {west}"


# ------------------------------------------------------------------------------------------------ height

def test_a_900_wu_ridge_lowers_density_behind_it(lib, world_factory):
    """E1q-field Tests: a 900 wu ridge (columns cx + 5 .. cx + 8) gives lower density behind it (columns cx + 12 .. cx + 15, rows
    cy - 2 .. cy + 2) than the flat control at the same cells, after 25 growth steps. Control: the flat world has density
    there. NEEDS E1q-field: yes. Red on the K-e5 tree: it ignores heights, so the two worlds are equal."""
    r = scene(lib, world_factory, terrain=ridge)
    f = scene(lib, world_factory, terrain=flat)
    cx, cy = objective_cell(lib, r)
    assert objective_cell(lib, f) == (cx, cy)
    _, h = heights(lib, r)
    assert h[cy * SIDE + cx + 6] == FLAT_CM + RIDGE_CM and h[cy * SIDE + cx + 10] == FLAT_CM
    for w in (r, f):
        steps(lib, w, 60 * 25 + 1)
    for gy in range(cy - 2, cy + 3):
        for gx in range(cx + 12, cx + 16):
            flat_d, ridge_d = d_at(lib, f, gx, gy), d_at(lib, r, gx, gy)
            assert flat_d > 0.0, f"control: the flat world has no density at ({gx}, {gy})"
            assert ridge_d < flat_d, f"({gx}, {gy}): behind the ridge {ridge_d}, flat control {flat_d}"


# ------------------------------------------------------------------------------------------------ economy

def test_economy_zero_gives_zero_density_everywhere(lib, world_factory):
    """E1q-field Tests / S-115: a region at economy 0 grows no town: D == 0 on every cell after ten growth steps. Control: the
    same scene at economy 40 has density. NEEDS E1q-field: no (guard, green on the K-e5 tree too)."""
    rich = scene(lib, world_factory, terrain=flat, economy=40.0)
    poor = scene(lib, world_factory, terrain=flat, economy=0.0)
    for w in (rich, poor):
        steps(lib, w, 60 * 10 + 1)
    assert max(grid(lib, rich)) > 0.0, "control: the economy-40 world has no density"
    g = grid(lib, poor)
    assert max(g) == 0.0, f"economy 0: {sum(1 for v in g if v > 0.0)} cells hold density, max {max(g)}"


# ------------------------------------------------------------------------------------------------ save and resume

def _field_state(lib, w):
    _, blk, f = saved_block(lib, w)
    return {"side": f["side"], "core": f["core"], "P": f["P"], "active": f["active"], "D": grid(lib, w)}


def test_save_at_step_5_then_5_more_steps_equals_10_uninterrupted(lib, world_factory):
    """E1q-field Tests (the frontier round trip): a save at growth step 5, loaded into a fresh mission, then 5 more steps, gives
    the same D, P, active and core as 10 uninterrupted steps, on a terrain that makes the frontier irregular (sea strip). Control
    first: the world at step 5 already differs from the one at step 10. NEEDS E1q-field: no (the legacy growth recomputes
    from scratch each step, so it is green on the K-e5 tree too; test_a_lost_frontier_stops_growth is the case that needs it)."""
    a = scene(lib, world_factory, terrain=sea_strip)
    b = scene(lib, world_factory, terrain=sea_strip)
    steps(lib, a, 60 * 10)
    steps(lib, b, 60 * 5)
    mid = _field_state(lib, b)
    data = save(lib, b)
    c = scene(lib, world_factory, terrain=sea_strip)
    assert load(lib, c, data) == 0
    steps(lib, c, 60 * 5)
    whole, resumed = _field_state(lib, a), _field_state(lib, c)
    assert mid["D"] != whole["D"], "control: step 5 and step 10 have the same field"
    assert resumed["side"] == whole["side"] and resumed["core"] == whole["core"]
    assert resumed["active"] == whole["active"], "the growth frontier differs after save, load and 5 more steps"
    assert resumed["P"] == whole["P"], "P differs after save, load and 5 more steps"
    assert resumed["D"] == whole["D"], "D differs after save, load and 5 more steps"


def test_a_lost_frontier_stops_growth(lib, world_factory):
    """E1q-field (positive control of the case above): the saved frontier is what carries growth. The step-5 save with `active`
    emptied, loaded and run 5 more steps, ends with less of the canvas reached than the uninterrupted run (the field cannot
    spread without a frontier). NEEDS E1q-field: yes. Red on the K-e5 tree: the legacy growth ignores `active`."""
    a = scene(lib, world_factory, terrain=sea_strip)
    b = scene(lib, world_factory, terrain=sea_strip)
    steps(lib, a, 60 * 10)
    steps(lib, b, 60 * 5)
    data, blk, f = saved_block(lib, b)
    assert len(f["active"]) > 0, "control: the step-5 save holds a growth frontier"
    f["active"] = []
    c = scene(lib, world_factory, terrain=sea_strip)
    assert load(lib, c, splice(data, blk, f)) == 0
    steps(lib, c, 60 * 5)
    whole, cut = grid(lib, a), grid(lib, c)
    assert sum(1 for v in cut if v > 0.0) < sum(1 for v in whole if v > 0.0), "an emptied frontier still grew the field"


# ------------------------------------------------------------------------------------------------ determinism across processes

def _digest_run():
    """The child of the two-process case: same scene, 600 steps, print the full checksum, its sections and a digest of the save."""
    h = ctypes.CDLL(str(C.LIB_PATH))
    C._configure_common(h)
    C._bind_generated(h)
    make, created = C._world_factory_for(h, None)
    w = scene(h, make, terrain=sea_strip)
    steps(h, w, 600)
    sec = (ctypes.c_uint64 * 16)()
    full = h.om_world_checksum_full(w, sec, 16)
    print(json.dumps({"full": full, "sections": list(sec), "save_sha256": hashlib.sha256(save(h, w)).hexdigest()}))


def _child():
    res = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())], cwd=str(REPO), capture_output=True, text=True, timeout=600)
    assert res.returncode == 0, res.stderr[-2000:]
    return json.loads(res.stdout.strip().splitlines()[-1])


def test_the_same_seed_hashes_the_same_across_two_processes(lib, world_factory):
    """E1q-field Tests: the same seed and command stream give a byte-identical field in two separate processes (no hash-order,
    address or wall-clock input). Control: the digest moves when the seed changes. NEEDS E1q-field: no (guard, green on the
    K-e5 tree too)."""
    first, second = _child(), _child()
    assert first == second, "two processes, one seed, two different hashes"
    w = scene(lib, world_factory, terrain=sea_strip)
    steps(lib, w, 600)
    sec = (ctypes.c_uint64 * 16)()
    full = lib.om_world_checksum_full(w, sec, 16)
    # the whole save is compared between the two children only: byte 40 of a save differs between worlds of one process
    assert full == first["full"] and list(sec) == first["sections"], "this process and a child disagree"
    other = scene(lib, world_factory, terrain=sea_strip, seed=SEED + 1)
    steps(lib, other, 600)
    assert lib.om_world_checksum_full(other, sec, 16) != first["full"], "control: another seed gave the same checksum"


# ------------------------------------------------------------------------------------------------ timing control

def test_control_timing_growth_step_cost_is_printed_not_asserted(lib, world_factory, capsys):
    """DRAFT-density-budget (2 ms per growth step, Architect draft, Westley to confirm): prints the cost of the growth step
    after 40 growth steps on flat land (growth ticks are also lot-step ticks, so the lot-only ticks are printed to subtract) and
    asserts nothing about it. The only assertion is that the field grew (the control
    measured a real step). NEEDS E1q-field: no."""
    w = scene(lib, world_factory, terrain=flat)
    times = []
    for tick in range(60 * 40):
        t0 = time.perf_counter()
        lib.om_world_step(w)
        times.append((tick, time.perf_counter() - t0))
    med = lambda xs: sorted(xs)[len(xs) // 2]
    both = [t for k, t in times if k % GROWTH_TICKS == 0]                              # growth step and lot step (60 is a multiple of 20)
    lot_only = [t for k, t in times if k % 20 == 0 and k % GROWTH_TICKS != 0]            # lot step alone
    other = [t for k, t in times if k % 20 != 0]
    with capsys.disabled():
        print("\nDRAFT-density-budget (not asserted): median world step on a growth tick %.3f ms (growth + lot step, max %.3f); "
              "lot-step-only tick %.3f ms; other ticks %.3f ms; so the growth step costs about %.3f ms (budget 2 ms)"
              % (1000 * med(both), 1000 * max(both), 1000 * med(lot_only), 1000 * med(other), 1000 * (med(both) - med(lot_only))))
    assert max(grid(lib, w)) > 0.0


if __name__ == "__main__":  # the child of the two-process case
    _digest_run()
