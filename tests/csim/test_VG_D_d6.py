"""Visible-game lane D, piece D6 (Westley 2026-10-09, option A). Fenced: builders never edit this file.

R-246-01 (E-17): each space layer is an open-or-blocked sheet; rubble is small plates drawn at half thickness
(docs/northstar/plans/2026-10-02-space-kit-mode-spec.md, "Rubble"). Nothing makes rubble a cover obstacle, so
om_space_field_generate_nodes (csrc/space_field.c sf_rubble_cover) must lay no cover disc; rubble plates join the blocked
cell mask of their layer like every other plate.

RED on origin/push/vg-d-land-2 (one 200 wu cover disc per rubble polygon is present): tests 1 and 3.
Test 2 (rubble centroid cells blocked) is reported by the run; test 4 is a timing report, no assertion.
Controls pass by design.
"""
import ctypes
import time

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region,
)

N, CELLS, LAYERS, CELL = 240, 240 * 240, 5, 100.0
RUBBLE = 2  # OM_SPACE_KIND_RUBBLE, csrc/space_internal.h
SPACE_ERA, GROUND_ERA = 0, 1


def _scene(lib, world_factory, *, era, archetype=3, seed=7):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, 0, OMArchetype.PLAYER)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, 1, held_since=-1)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=20.0, faction_id=1)
    assert lib.om_set_era_kind(w, era) == 0
    lib.om_mission_setup(w, 0, archetype, 0)
    return w


def test_control_add_cover_raises_the_count(lib, world_factory):
    """CONTROL (D6, R-246-01): one disc added by the public API raises om_map_cover_count by one."""
    w = _scene(lib, world_factory, era=GROUND_ERA)
    n = lib.om_map_cover_count(w)
    lib.om_map_add_cover(w, 50.0, 50.0, 10.0, 1.0)
    assert lib.om_map_cover_count(w) == n + 1


def test_d6_field_adds_no_cover(lib, world_factory):
    """D6 / R-246-01: regenerating the field on a space mission leaves om_map_cover_count unchanged.
    RED now: sf_rubble_cover adds a disc per rubble polygon."""
    w = _scene(lib, world_factory, era=SPACE_ERA)
    assert lib.om_space_field_present(w) == 1
    before = lib.om_map_cover_count(w)
    w2 = _scene(lib, world_factory, era=GROUND_ERA)
    base = lib.om_map_cover_count(w2)
    assert before == base, f"space mission holds {before} cover discs, ground baseline {base}"


def test_d6_rubble_cells_are_blocked_in_their_layer(lib, world_factory):
    """D6 / R-246-01: each rubble polygon's centroid cell is blocked in its layer's mask.
    (If this is already green the raster blocks rubble and D6 only removes the disc code.)"""
    w = _scene(lib, world_factory, era=SPACE_ERA)
    masks = []
    for k in range(LAYERS):
        buf = (ctypes.c_uint8 * CELLS)()
        assert lib.om_space_field_get_mask(w, k, buf, CELLS) == CELLS
        masks.append(bytes(buf))
    rubble = bad = 0
    for i in range(lib.om_space_field_poly_count(w)):
        layer, kind = ctypes.c_uint32(), ctypes.c_uint32()
        xy = (ctypes.c_double * 128)()
        n = lib.om_space_field_poly_get(w, i, ctypes.byref(layer), ctypes.byref(kind), xy, 64)
        if kind.value != RUBBLE or n == 0:
            continue
        rubble += 1
        cx = sum(xy[2 * j] for j in range(n)) / n
        cy = sum(xy[2 * j + 1] for j in range(n)) / n
        if not masks[layer.value][int(cy // CELL) * N + int(cx // CELL)]:
            bad += 1
    assert rubble > 0, "no rubble polygons on the seed-7 mission"
    assert bad == 0, f"{bad} of {rubble} rubble centroid cells are open"


def test_d6_space_cover_equals_ground_cover_same_seed(lib, world_factory):
    """D6 / R-246-01: a space mission's cover count equals the ground era's for the same seed (field adds none).
    RED now: discs present."""
    s = _scene(lib, world_factory, era=SPACE_ERA, seed=1)
    g = _scene(lib, world_factory, era=GROUND_ERA, seed=1)
    assert lib.om_map_cover_count(s) == lib.om_map_cover_count(g)


def test_d6_timing_report(lib, world_factory):
    """D6 timing report (no assertion; Westley owns thresholds): 200 om_tactical_step calls, seed-1 space mission."""
    w = _scene(lib, world_factory, era=SPACE_ERA, seed=1)
    t = time.perf_counter()
    for _ in range(200):
        lib.om_tactical_step(w)
    print(f"D6 TIMING: 200 om_tactical_step = {time.perf_counter() - t:.3f} s, covers={lib.om_map_cover_count(w)}")
