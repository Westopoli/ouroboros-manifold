"""Visible-game programme lane E1, piece E1c: lot stages and lot records (docs/northstar/plans/2026-10-07-visible-game-spec.md
rev 6, lane E1; R-193-05 five stages by density, R-193-09 streets left open; contract: docs/architecture.md "Visible-game
economy fields"). Fenced: builders never edit this file.

Stage rule under test (thresholds 0.10/0.22/0.38/0.58 are the Q-193-02 liberty, applied to om_density_at at the lot):
the target stage is the number of thresholds the density has passed: < 0.10 -> 0; < 0.22 -> 1 staked; < 0.38 -> 2 scaffold;
< 0.58 -> 3 small; else 4 large (TD-VG-E-19: spec rev 10d, "empty" is no lot and stage 5 is reserved). Stage 0 is rubble (E1d)
and is skipped here. A lot "rises" a stage at a time, so the stage may lag the target but never exceeds it.
Streets (R-193-09): the lot-free grid cells inside the settlement's bounding box (100 wu cells, the terrain grid; TD-VG-E-19)
contain a 4-connected path from the left edge to the right edge and from the top edge to the bottom edge of that box.

How lots appear: no setter exists in K-e, so the tests start a ground-era mission (om_set_era_kind 1, walking kinds) and
step om_tactical_step; E1b/E1c/E1i make lots exist there. Nothing here names a symbol outside K-e.
RED on main: the K-e stubs never create a lot, so om_lot_count stays 0 -> "no lots after a ground mission".
Controls (pass on main): the pure stage mapping, and the two detectors run on synthetic data that must trip them.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier,
    set_edge, set_faction, set_owner, set_region,
)

V = ctypes.c_void_p
P = ctypes.POINTER
CELL = 100.0            # density grid cell, the 100 wu terrain cell (TD-VG-E-19; was 200.0, OM_DENSITY_SIDE 120 over 24000 wu)
SIDE = 240              # 24000 wu / 100 (TD-VG-E-19; was 120)
THRESH = (0.10, 0.22, 0.38, 0.58)
STEPS = 200            # draft: ticks stepped before reading lots
SEEDS = (3, 7, 11)      # draft


class Lot(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("x", ctypes.c_double), ("y", ctypes.c_double),
                ("stage", ctypes.c_int32), ("building", ctypes.c_int32), ("owner", ctypes.c_int32)]


def stage_of(d):
    """R-193-05 target stage 0..4 for a density value: the number of thresholds passed (TD-VG-E-19; was 1 + that count)."""
    return sum(1 for t in THRESH if d >= t)


def bind(lib):
    lib.om_lot_count.argtypes, lib.om_lot_count.restype = [V], ctypes.c_uint32
    lib.om_lot_get_at.argtypes, lib.om_lot_get_at.restype = [V, ctypes.c_uint32, P(Lot)], ctypes.c_int
    lib.om_density_at.argtypes, lib.om_density_at.restype = [V, ctypes.c_double, ctypes.c_double], ctypes.c_double
    lib.om_tactical_step.argtypes, lib.om_tactical_step.restype = [V], ctypes.c_uint64
    lib.om_save_state_size.argtypes, lib.om_save_state_size.restype = [V], ctypes.c_uint32
    lib.om_save_state_write.argtypes, lib.om_save_state_write.restype = [V, P(ctypes.c_uint8), ctypes.c_uint32], None
    lib.om_load_state_read.argtypes, lib.om_load_state_read.restype = [V, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_int


def lots(lib, w):
    out = []
    for i in range(lib.om_lot_count(w)):
        r = Lot()
        assert lib.om_lot_get_at(w, i, ctypes.byref(r)) == 0
        out.append((r.id, r.x, r.y, r.stage, r.building, r.owner))
    return out


def scene(lib, world_factory, seed, steps=STEPS):
    bind(lib)
    lib.om_roster_set_movement_kind.argtypes = [V, ctypes.c_uint32, ctypes.c_int]
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, 0, OMArchetype.PLAYER)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, 1, held_since=-1)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=20.0, economy=40.0, population=10.0, faction_id=0)  # TD-VG-E-10: player region, as the E1b scene
    assert lib.om_set_era_kind(w, 1) == 0
    for t in range(6):
        assert lib.om_roster_set_movement_kind(w, t, 1) == 0
    lib.om_mission_setup(w, 0, 1, 0)
    lib.om_mission_begin(w)
    for _ in range(steps):
        lib.om_tactical_step(w)
    return w


def stage_violations(rows, density):
    """Detector: lots (not rubble) whose stage exceeds the target for the density at their point, or is outside 0..5."""
    bad = []
    for (i, x, y, st, _b, _o) in rows:
        if st == 0:
            continue
        if not 1 <= st <= 5 or st > stage_of(density(x, y)):
            bad.append((i, st, stage_of(density(x, y))))
    return bad


def street_cells_open(rows):
    """Detector: lot-free cells of the lots' bounding box connect left-right and top-bottom (R-193-09)."""
    cells = {(int(x // CELL), int(y // CELL)) for (_i, x, y, *_r) in rows}
    if not cells:
        return False
    x0, x1 = min(c[0] for c in cells), max(c[0] for c in cells)
    y0, y1 = min(c[1] for c in cells), max(c[1] for c in cells)
    free = {(a, b) for a in range(x0, x1 + 1) for b in range(y0, y1 + 1)} - cells

    def spans(starts, goal):
        seen, todo = set(starts & free), list(starts & free)
        while todo:
            a, b = todo.pop()
            if goal((a, b)):
                return True
            for n in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if n in free and n not in seen:
                    seen.add(n)
                    todo.append(n)
        return False
    left = {(x0, b) for b in range(y0, y1 + 1)}
    top = {(a, y0) for a in range(x0, x1 + 1)}
    return spans(left, lambda c: c[0] == x1) and spans(top, lambda c: c[1] == y1)


# ---- controls (pass on main) ------------------------------------------------------------------------------------

def test_control_stage_mapping_edges():
    """CONTROL: the R-193-05 mapping at and around each threshold (TD-VG-E-19: counts, were 1 + count)."""
    assert [stage_of(d) for d in (0.0, 0.0999, 0.10, 0.2199, 0.22, 0.3799, 0.38, 0.5799, 0.58, 3.0)] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]


def test_control_stage_detector_trips():
    """CONTROL: the stage detector flags a stage-5 lot at density 0.05 and passes a stage-1 lot at 0.15 (TD-VG-E-19: was a
    stage-2 lot, the target of 0.15 under 1 + count) and a rubble lot."""
    assert stage_violations([(1, 0, 0, 5, 0, -1)], lambda x, y: 0.05)
    assert not stage_violations([(1, 0, 0, 1, 0, -1), (2, 0, 0, 0, 0, -1)], lambda x, y: 0.15)
    assert stage_violations([(1, 0, 0, 6, 0, -1)], lambda x, y: 9.0)


def test_control_street_detector_trips():
    """CONTROL: a solid 5x5 block of lots has no open street; the same block with one open column and row has."""
    solid = [(n, a * CELL + 1, b * CELL + 1, 1, 0, -1) for n, (a, b) in enumerate((a, b) for a in range(5) for b in range(5))]
    assert not street_cells_open(solid)
    gappy = [r for r in solid if int(r[1] // CELL) != 2 and int(r[2] // CELL) != 2]
    gappy += [(99, 0 * CELL + 1, 0 * CELL + 1, 1, 0, -1), (98, 4 * CELL + 1, 4 * CELL + 1, 1, 0, -1)]
    assert street_cells_open(gappy)


def test_control_fresh_world_has_no_lots_and_no_density(lib, world_factory):
    """CONTROL: before any mission the table is empty and the density field reads 0.0."""
    bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_lot_count(w) == 0
    assert lib.om_density_at(w, 100.0, 100.0) == 0.0


# ---- isolation: lot records ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_lots_exist_after_a_ground_mission(lib, world_factory, seed):
    """R-193-05/R-193-07: a base is on screen during a mission, so lots exist. Red on main: no lots after a ground mission."""
    w = scene(lib, world_factory, seed)
    assert lib.om_lot_count(w) > 0, "no lots after a ground mission (E1c not built)"


@pytest.mark.parametrize("seed", SEEDS)
def test_lot_records_are_well_formed(lib, world_factory, seed):
    """Records (id, cell, stage, owner): ascending unique ids, stage 0..5, owner -1 or a faction, inside the canvas,
    one lot per 100 wu cell (TD-VG-E-19; was 200 wu), building >= 0."""
    rows = lots(lib, scene(lib, world_factory, seed))
    assert rows, "no lots after a ground mission (E1c not built)"
    ids = [r[0] for r in rows]
    assert ids == sorted(set(ids)), "ids not ascending and unique"
    for (_i, x, y, st, b, o) in rows:
        assert 0 <= x < SIDE * CELL and 0 <= y < SIDE * CELL
        assert 0 <= st <= 5
        assert b >= 0
        assert o == -1 or 0 <= o < 15
    cells = [(int(r[1] // CELL), int(r[2] // CELL)) for r in rows]
    assert len(cells) == len(set(cells)), "two lots share a cell"


@pytest.mark.parametrize("seed", SEEDS)
def test_lot_stage_follows_density_never_above_target(lib, world_factory, seed):
    """R-193-05: no lot stands above the stage its cell's density allows (0.10/0.22/0.38/0.58 liberty)."""
    w = scene(lib, world_factory, seed)
    rows = lots(lib, w)
    assert rows, "no lots after a ground mission (E1c not built)"
    assert stage_violations(rows, lambda x, y: lib.om_density_at(w, x, y)) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_lots_rise_where_density_allows(lib, world_factory, seed):
    """R-193-05 rises: with time, at least one lot whose target is 2 or more has reached stage 2 or more."""
    w = scene(lib, world_factory, seed, steps=3 * STEPS)
    rows = lots(lib, w)
    assert rows, "no lots after a ground mission (E1c not built)"
    eligible = [r for r in rows if stage_of(lib.om_density_at(w, r[1], r[2])) >= 2]
    assert eligible, "no lot sits on density >= 0.22"  # TD-VG-E-19: target >= 2 is now 0.22 (was 0.10 under 1 + count)
    assert max(r[3] for r in eligible) >= 2, "no eligible lot rose past stage 1"


# ---- isolation: streets -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_streets_are_left_open(lib, world_factory, seed):
    """R-193-09: lot-free cells cross the settlement both ways."""
    rows = lots(lib, scene(lib, world_factory, seed))
    assert rows, "no lots after a ground mission (E1c not built)"
    assert street_cells_open(rows), "lots fill the settlement with no open street across it"


# ---- integration ------------------------------------------------------------------------------------------------

def test_same_seed_same_lots(lib, world_factory):
    """Determinism: two identical missions give identical lot tables."""
    a = lots(lib, scene(lib, world_factory, 7))
    assert a, "no lots after a ground mission (E1c not built)"
    assert a == lots(lib, scene(lib, world_factory, 7))


def test_lot_table_round_trips_through_save(lib, world_factory):
    """Save format 8 integration: a saved mid-mission world loads with the same lot table."""
    src = scene(lib, world_factory, 7)
    before = lots(lib, src)
    assert before, "no lots after a ground mission (E1c not built)"
    size = lib.om_save_state_size(src)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(src, buf, size)
    dst = world_factory(n_regions=2, seed=7)
    assert lib.om_load_state_read(dst, buf, size) == 0
    assert lots(lib, dst) == before


def test_lots_keep_ascending_ids_as_more_appear(lib, world_factory):
    """A lot is never removed: every id seen early is still present, with the same cell, later."""
    w = scene(lib, world_factory, 7, steps=STEPS)
    early = lots(lib, w)
    assert early, "no lots after a ground mission (E1c not built)"
    for _ in range(STEPS):
        lib.om_tactical_step(w)
    late = {r[0]: r for r in lots(lib, w)}
    for (i, x, y, *_r) in early:
        assert i in late and (late[i][1], late[i][2]) == (x, y)
