# spec: docs/northstar/plans/2026-10-06-terrain-stage2-spec.md, "lab" lane row (E-01 R-001-07, R-005-09, E-17 walk mask)
"""Ground-era smoke scene on the production library: two walker groups on terrain seed 11, no fire.

16 hold-fire Vanguard clones per side (the lab's no-fire pattern, search.HOLD_FIRE_TYPE), kind walking, era kind 1.
Group HIGH stands on band 3 (layer 2), group LOW on band 2 (layer 1), 400 wu apart, inside the Vanguard's 700 wu
sensor radius. Both spots were found on seed 11 as flat, walkable 120 wu squares (bands asserted below, so a field change
fails loudly). Test numbers are test drafts (2026-10-06), Westley may tighten.

Red until the lab lane lands: each test fails on 'engine wrapper has no <name>' (or 'Terrain has no field_seed').
"""
import dataclasses
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, engine, search  # noqa: E402
from scripts.skilllab.contract import Terrain  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402

SEED = 11
CANVAS = 12000.0
WALKING = 1
HIGH_AT, HIGH_BAND = (8150.0, 6050.0), 3      # test draft (2026-10-06)
LOW_AT, LOW_BAND = (8550.0, 6050.0), 2        # test draft (2026-10-06)
BLOB_RADIUS = 60.0                            # test draft (2026-10-06)
FORCE = 16                                    # test draft (2026-10-06)
TICKS = 600                                   # test draft (2026-10-06)
BUDGET_SECONDS = 10.0                         # test draft (2026-10-06)
SLOPE_PROBE = (6550.0, 4050.0)                # inside seed 11's slope 3 (bands 3 to 4)
NAMES = ("set_movement_kind", "movement_kind", "set_era_kind", "terrain_slope_at", "terrain_walk_mask")


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _need(e, *names):
    for n in names:
        assert hasattr(e, n), "engine wrapper has no %s" % n


def _scene(e):
    """Returns (world, high ids, low ids); every unit walks, no unit fires."""
    _need(e, *NAMES)
    van = e.type_id("Vanguard")
    w = e.new_world(0)
    for k, v in batches.BASE_SETTINGS.items():
        e.set_param(w, e.param_id(k), float(v))
    e.disable_abilities(w)
    assert e.terrain_generate(w, SEED, CANVAS) == 0
    e.set_era_kind(w, 1)
    stats = dict(e.type_stats(w, van), attack_range=0.0, role="Vanguard", ability_id=0)
    e.register_unit_type(w, search.HOLD_FIRE_TYPE, stats)
    e.set_movement_kind(w, search.HOLD_FIRE_TYPE, WALKING)
    assert e.movement_kind(w, search.HOLD_FIRE_TYPE) == WALKING
    assert e.terrain_band_at(w, *HIGH_AT) == HIGH_BAND and e.terrain_band_at(w, *LOW_AT) == LOW_BAND
    high = [e.spawn(w, search.HOLD_FIRE_TYPE, 0, x, y, HIGH_BAND - 1)
            for x, y in place("blob", FORCE, HIGH_AT[0], HIGH_AT[1], 0.0, {"radius": BLOB_RADIUS})]
    low = [e.spawn(w, search.HOLD_FIRE_TYPE, 1, x, y, LOW_BAND - 1)
           for x, y in place("blob", FORCE, LOW_AT[0], LOW_AT[1], 0.0, {"radius": BLOB_RADIUS})]
    return w, high, low


def test_terrain_takes_a_field_seed():
    assert "field_seed" in {f.name for f in dataclasses.fields(Terrain)}, "Terrain has no field_seed"
    t = Terrain(canvas=(CANVAS, CANVAS), field_seed=SEED)
    assert t.field_seed == SEED and Terrain(canvas=(CANVAS, CANVAS)).field_seed is None


def test_the_higher_group_sees_the_lower_and_the_lower_sees_nothing(library):
    e = library
    w, high, low = _scene(e)
    try:
        for _ in range(20):
            e.step(w)
        assert e.seen_by_sight(w, 0, low) == set(low), "higher group should see all of the lower group"
        assert e.seen_by_sight(w, 1, high) == set(), "lower group must see nothing of the higher"
        assert all(e.unit_hp(w, u) == e.unit_hp(w, high[0]) for u in high + low)   # nobody fired
    finally:
        e.free_world(w)


def test_slope_lookup_finds_the_slope_and_not_flat_ground(library):
    e = library
    w, high, low = _scene(e)
    try:
        assert e.terrain_slope_at(w, *SLOPE_PROBE) >= 0
        assert e.terrain_slope_at(w, *HIGH_AT) == -1 and e.terrain_slope_at(w, *LOW_AT) == -1
    finally:
        e.free_world(w)


def test_a_walker_ordered_across_the_map_stays_on_masked_cells(library):
    e = library
    w, high, low = _scene(e)
    try:
        cw, ch, _ = e.terrain_dump_bands(w)
        masks = {}
        e.order_move(w, high, 600.0, 600.0)
        for tick in range(TICKS):
            e.step(w)
            if tick % 5:
                continue
            for u in high:
                layer = e.unit_layer(w, u)
                if layer not in masks:
                    masks[layer] = e.terrain_walk_mask(w, layer)
                x, y = e.unit_pos(w, u)
                cell = int(y // 100) * cw + int(x // 100)
                assert masks[layer][cell] == 1, "tick %d unit %d at (%.0f, %.0f) layer %d is off the mask" % (
                    tick, u, x, y, layer)
        x, y = e.unit_pos(w, high[0])
        assert abs(x - HIGH_AT[0]) + abs(y - HIGH_AT[1]) > 300, "the walker never moved"
    finally:
        e.free_world(w)


def test_the_fight_runs_600_ticks_in_under_10_seconds(library):
    e = library
    t0 = time.perf_counter()
    w, high, low = _scene(e)
    try:
        e.order_move(w, high, 600.0, 600.0)
        e.order_move(w, low, 11000.0, 11000.0)
        for _ in range(TICKS):
            e.step(w)
        assert time.perf_counter() - t0 < BUDGET_SECONDS
    finally:
        e.free_world(w)
