# Rule pins: R-001-07@8f31c3, R-004-07@c7c723
"""E-01 R-001-07 / R-004-07 (terrain stage 2): the collision push-apart must not move a walker off its walk mask.

Defect found 2026-10-06 on push/terrain2-land-2: om_move_collide_pair (csrc/tactical_move.c) shoves overlapping walkers
sideways; its only guard (om_move_slide) reads mapgen density, not the walk mask, so a walker next to an unwalkable
cell can be pushed onto it. Lab twin: tests/skilllab/integration/test_ground_scene_real.py
::test_a_walker_ordered_across_the_map_stays_on_masked_cells.

Scene: seed 11 terrain, 16000 wu canvas, 100 wu cells, layer 2 (band 3). Raider set to walking.
Red today for the mask reason (tests 1 and 2); test 3 (flyers unchanged) is green and pins the fix.
"""
import ctypes

from conftest import OMFeature

RAIDER = 0
OM_MOVE_FLYING, OM_MOVE_WALKING = 0, 1
CANVAS = 16000.0
SEED = 11
CELL = 100.0
LAYER = 2
BLOB_N = 16
BLOB_R = 60.0              # lab's shape: 16 units in a 60 wu blob
# Recorded 2026-10-06 on push/terrain2-land-2 at 6ea6b26baf6e207d33c3213bdfeb3562bc6d9700: flyer blob, 50 ticks.
# Re-recorded 2026-10-09 (TD-VG-E-1): K-e folds the economy words into the factions section; old 17656050431320828508.
# TD-VG-E-17: K-e5 hashes the economy block into the factions section, which moved the whole word (TD-VG-E-9 value
# 3388087635923795345); the pin is now the (units, movement) sections, which K-e5 does not touch.
# TD-VG-W-2: old 59688484827617401, new 15349036910042598830 (movement word only; units word 5542676384425136191 unchanged):
# W2 stored routes add the route block to the movement section.
FLYER_SECTIONS_50 = (5542676384425136191, 10129796491057787029)   # re-recorded 2026-11-02 for H-057 (OM_TP_ATTACK_MOVE_LEASH default 200 to 0 is hashed in the movement section; units word unchanged); earlier: re-recorded 2026-10-29 for LAB-REV2-E0 (movement section carries the movement slot); units word unchanged, positions identical to feb73b17; earlier: re-recorded 2026-10-13 on the W2 tree (was recorded 2026-10-11 on the K-e5 tree 2747b283)


def _units_movement(lib, w):
    """TD-VG-E-17: the trace is the "units" and "movement" sections (3, 4) of om_world_checksum_full, not the whole word."""
    buf = (ctypes.c_uint64 * 9)()
    lib.om_world_checksum_full(w, buf, 9)
    return (buf[3], buf[4])


def _world(lib, world_factory, kind):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, kind) == 0
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    n = cw.value * ch.value
    buf = (ctypes.c_uint8 * n)()
    assert lib.om_terrain_walk_mask(w, LAYER, buf, n) == n
    return w, bytes(buf), cw.value


def _on(mask, cw, x, y):
    cx, cy = int(x // CELL), int(y // CELL)
    return 0 <= cx < cw and 0 <= cy < len(mask) // cw and mask[cy * cw + cx] == 1


def _edge_cell(mask, cw):
    """First walkable cell whose east neighbour is unwalkable and whose west neighbour is walkable."""
    for i, v in enumerate(mask):
        cx = i % cw
        if v and 1 <= cx < cw - 1 and i // cw >= 2 and mask[i + 1] == 0 and mask[i - 1] == 1:
            return cx, i // cw
    raise AssertionError("no walkable cell with an unwalkable east neighbour on seed 11 layer 2")


def _blob(lib, w, mask, cw, kind_walker):
    """Units around the east edge of an edge cell; walkers only where the mask allows, flyers on the same points."""
    cx, cy = _edge_cell(mask, cw)
    ex, ey = (cx + 1) * CELL, (cy + 0.5) * CELL          # the east edge of the walkable cell
    ids, k = [], 0
    for j in range(BLOB_N):
        x = ex - 2.0 - (j % 4) * (BLOB_R / 4)
        y = ey + ((j // 4) - 1.5) * (BLOB_R / 4)
        assert _on(mask, cw, x, y), f"setup point ({x:.1f}, {y:.1f}) is off-mask"
        u = lib.om_unit_spawn(w, RAIDER, 0, x, y, LAYER)
        if u:                                       # the sim refuses a few spawn points; keep the rest
            ids.append(u)
    assert len(ids) >= 12, f"only {len(ids)} of {BLOB_N} blob units spawned"
    return ids


def _off(lib, w, mask, cw, ids):
    out = []
    for u in ids:
        x, y = lib.om_unit_get_pos(w, u)
        if not _on(mask, cw, x, y):
            out.append((u, round(x, 1), round(y, 1), int(x // CELL), int(y // CELL)))
    return out


def test_R_001_07_two_overlapping_walkers_at_a_mask_edge_stay_on_masked_cells(lib, world_factory):
    w, mask, cw = _world(lib, world_factory, OM_MOVE_WALKING)
    cx, cy = _edge_cell(mask, cw)
    ex, ey = (cx + 1) * CELL, (cy + 0.5) * CELL
    a = lib.om_unit_spawn(w, RAIDER, 0, ex - 5.0, ey, LAYER)
    b = lib.om_unit_spawn(w, RAIDER, 0, ex - 15.0, ey, LAYER)
    assert a and b
    assert _on(mask, cw, ex - 5.0, ey) and not _on(mask, cw, ex + 1.0, ey), "mask query control failed"
    done = 0
    for t in (1, 5, 50):
        while done < t:
            lib.om_tactical_step(w)
            done += 1
        bad = _off(lib, w, mask, cw, [a, b])
        assert not bad, f"after tick {t}: walkers off-mask (unit, x, y, cellx, celly) {bad}; edge cell ({cx}, {cy})"


def test_R_001_07_a_16_walker_blob_at_a_mask_edge_stays_on_masked_cells_every_tick(lib, world_factory):
    w, mask, cw = _world(lib, world_factory, OM_MOVE_WALKING)
    ids = _blob(lib, w, mask, cw, True)
    for t in range(1, 51):
        lib.om_tactical_step(w)
        bad = _off(lib, w, mask, cw, ids)
        assert not bad, f"tick {t}: walkers off-mask (unit, x, y, cellx, celly) {bad}"


def test_R_001_07_flyer_blob_trace_is_unchanged_by_the_walker_fix(lib, world_factory):
    """Guard: the fix must not move flyers. Positive control: the flyers do get pushed past the edge (the mask query
    is real and the blob does collide)."""
    w, mask, cw = _world(lib, world_factory, OM_MOVE_FLYING)
    ids = _blob(lib, w, mask, cw, False)
    x0 = [lib.om_unit_get_pos(w, u) for u in ids]
    for _ in range(50):
        lib.om_tactical_step(w)
    assert [lib.om_unit_get_pos(w, u) for u in ids] != x0, "flyers did not move at all"
    cs = _units_movement(lib, w)
    print("FLYER_SECTIONS_50", cs)
    assert cs == FLYER_SECTIONS_50
