"""Shared helpers for the terrain stage 2 "fog" lane tests (spec 2026-10-06, lane "fog"; E-01 R-005-09, R-005-11, S-162).
Holds no tests of its own. Fence: tests/csim/test_E01_T2_fog_*.py and test_E01_R005_*.py of this lane; builders never edit these.

Layers: the bible numbers 1 to 5, the engine and every test here count 0 to 4 (band k is engine layer k - 1).
Geometry is found on terrain seed 11 (canvas 16,000, 100 wu cells) by scanning cells in a fixed order, with a python
reference of the spec's sight sampler (om_terrain_sight_blocks) used only to PICK scenes; the assertions go through
om_unit_can_see and om_command_ping, never through the reference.
"""
import ctypes
import math

SEED = 11
CANVAS = 16000.0
CELL = 100.0
CELLS = 160
EYE = 50.0          # OM_TP_SIGHT_EYE_HEIGHT default, spec 2026-10-06
SAMPLE_STEP = 25.0  # spec: sight sample step
OWN_CELL = 50.0     # spec: samples strictly nearer than this to either end are skipped
FLYER_SEEN_MULT = 1.5  # OM_TP_GROUND_FLYER_SEEN_MULT default
SCAN_STEP = 3       # provisional (2026-10-06): cell stride of the scene search
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1)]

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD = range(5)
RADIUS = {RAIDER: 800.0, INTERCEPTOR: 1000.0, VANGUARD: 700.0, BOMBARD: 300.0}
MOVE_FLYING, MOVE_WALKING = 0, 1
WALKER_TYPES = (VANGUARD, RAIDER)   # walking in these tests; INTERCEPTOR and BOMBARD stay flyers
PING_OK, PING_REASON_CASTER, PING_REASON_REACH, PING_REASON_GROUND = 0, 1, 2, 5


def make_ground_world(lib, world_factory, era_kind=1):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    assert lib.om_set_era_kind(w, era_kind) == 0
    for t in WALKER_TYPES:
        assert lib.om_roster_set_movement_kind(w, t, MOVE_WALKING) == 0
    return w


def spawn(lib, w, utype, faction, x, y, layer):
    uid = lib.om_unit_spawn(w, utype, faction, float(x), float(y), layer)
    assert uid != 0, f"om_unit_spawn({utype}, {faction}, {x}, {y}, {layer}) returned 0"
    return uid


def sees(lib, w, observer, target):
    return int(lib.om_unit_can_see(w, observer, target))


def centre(c):
    return (c + 0.5) * CELL


class Scan:
    """Terrain readouts for scene picking."""

    def __init__(self, lib, w):
        self.lib, self.w = lib, w
        h = (ctypes.c_double * 8)()
        assert lib.om_terrain_band_heights(w, h, 8) == 5
        self.floors = list(h)[:5]
        self._band = {}
        self._h = {}

    def band(self, cx, cy):
        k = (cx, cy)
        if k not in self._band:
            self._band[k] = self.lib.om_terrain_band_at(self.w, centre(cx), centre(cy))
        return self._band[k]

    def walk(self, cx, cy):
        """The cell centre is walkable (a walking type's spawn returns 0 on an unwalkable cell, spec unit row)."""
        return self.lib.om_terrain_walkable_at(self.w, centre(cx), centre(cy)) != 0

    def height(self, x, y):
        return self.lib.om_terrain_height_at(self.w, x, y)

    def blocks(self, l0, x0, y0, l1, x1, y1):
        """The spec's om_terrain_sight_blocks, in python (picking only)."""
        e0 = max(self.height(x0, y0), self.floors[l0]) + EYE
        e1 = max(self.height(x1, y1), self.floors[l1]) + EYE
        d = math.hypot(x1 - x0, y1 - y0)
        n = int(d / SAMPLE_STEP)
        for i in range(1, n + 1):
            s = i * SAMPLE_STEP
            if s < OWN_CELL or d - s < OWN_CELL:
                continue
            t = s / d
            line = e0 + (e1 - e0) * t
            if self.height(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) > line:
                return True
        return False

    def cells(self):
        for cy in range(2, CELLS - 2, SCAN_STEP):
            for cx in range(2, CELLS - 2, SCAN_STEP):
                yield cx, cy

    def pairs(self, dist_lo, dist_hi):
        """(cx, cy, dx, dy, steps) for every start cell, direction and distance in whole cells, fixed order."""
        for cx, cy in self.cells():
            for dx, dy in DIRS:
                for steps in range(dist_lo // 100, dist_hi // 100 + 1):
                    ex, ey = cx + dx * steps, cy + dy * steps
                    if 1 <= ex < CELLS - 1 and 1 <= ey < CELLS - 1 and self.walk(cx, cy) and self.walk(ex, ey) \
                            and steps * CELL * (math.sqrt(2.0) if dx and dy else 1.0) <= dist_hi:
                        yield cx, cy, ex, ey, steps * CELL * (math.sqrt(2.0) if dx and dy else 1.0)


def _wu(sc, cx, cy, ex, ey):
    return centre(cx), centre(cy), centre(ex), centre(ey)


def _cells_on(sc, cx, cy, ex, ey):
    n = max(abs(ex - cx), abs(ey - cy))
    return [sc.band(cx + (ex - cx) * i // n, cy + (ey - cy) * i // n) for i in range(n + 1)]


def down_pair(sc, lo, hi, lower_band, plateau=False, skip=0):
    """(px, py, qx, qy, layer_p, layer_q): P on band lower_band + 1, Q on lower_band, lo..hi wu apart, line clear by the
    spec's sampler. plateau: the cell after P on the line is also P's band (the line leaves across P's own plateau)."""
    found = 0
    for cx, cy, ex, ey, d in sc.pairs(lo, hi):
        if sc.band(cx, cy) != lower_band + 1 or sc.band(ex, ey) != lower_band:
            continue
        cells = _cells_on(sc, cx, cy, ex, ey)
        if plateau and cells[1] != lower_band + 1:
            continue
        x0, y0, x1, y1 = _wu(sc, cx, cy, ex, ey)
        if not sc.blocks(lower_band, x0, y0, lower_band - 1, x1, y1):
            found += 1
            if found > skip:
                return x0, y0, x1, y1, lower_band, lower_band - 1
    raise AssertionError(f"no clear down pair at {lo}..{hi} wu for band {lower_band} on seed {SEED}")


def ridge_pair_same_band(sc, lo, hi):
    """Two cells of one band b, every cell between of band b too (so the cell grid never blocks on a layer-b-1 line),
    the spec's sampler blocks: a ridge inside the band higher than both eye lines. (x0, y0, x1, y1, layer)."""
    for cx, cy, ex, ey, d in sc.pairs(lo, hi):
        b = sc.band(cx, cy)
        if b < 1 or set(_cells_on(sc, cx, cy, ex, ey)) != {b}:
            continue
        x0, y0, x1, y1 = _wu(sc, cx, cy, ex, ey)
        if sc.blocks(b - 1, x0, y0, b - 1, x1, y1):
            return x0, y0, x1, y1, b - 1
    raise AssertionError(f"no same-band ridge pair at {lo}..{hi} wu on seed {SEED}")


def clear_pair_same_band(sc, lo, hi, band=1):
    """Two cells of one band, every cell between the same band, sampler clear. (x0, y0, x1, y1, layer)."""
    for cx, cy, ex, ey, d in sc.pairs(lo, hi):
        if set(_cells_on(sc, cx, cy, ex, ey)) != {band}:
            continue
        x0, y0, x1, y1 = _wu(sc, cx, cy, ex, ey)
        if not sc.blocks(band - 1, x0, y0, band - 1, x1, y1):
            return x0, y0, x1, y1, band - 1
    raise AssertionError(f"no clear same-band pair at {lo}..{hi} wu on seed {SEED}")


def ridge_pair_across_bands(sc, lo, hi):
    """P on band b + 1, Q on band b, the sampler blocks (a ridge above both eyes). (x0, y0, x1, y1, layer_p, layer_q)."""
    for cx, cy, ex, ey, d in sc.pairs(lo, hi):
        bp, bq = sc.band(cx, cy), sc.band(ex, ey)
        if bq >= 1 and bp == bq + 1:
            x0, y0, x1, y1 = _wu(sc, cx, cy, ex, ey)
            if sc.blocks(bq, x0, y0, bq - 1, x1, y1):
                return x0, y0, x1, y1, bq, bq - 1
    raise AssertionError(f"no ridge across bands at {lo}..{hi} wu on seed {SEED}")


def valley_ridge_pair(sc, lo, hi):
    """Two band-1 cells with a ridge between that blocks a walker at either end (layer 0 eye) but not an eye at the
    floor of layer 3 (the flyer). (flyer_x, flyer_y, walker_x, walker_y)."""
    for cx, cy, ex, ey, d in sc.pairs(lo, hi):
        if sc.band(cx, cy) == 1 and sc.band(ex, ey) == 1:
            x0, y0, x1, y1 = _wu(sc, cx, cy, ex, ey)
            if sc.blocks(0, x0, y0, 0, x1, y1) and not sc.blocks(3, x0, y0, 0, x1, y1):
                return x0, y0, x1, y1
    raise AssertionError(f"no valley ridge pair at {lo}..{hi} wu on seed {SEED}")


def open_line(sc, length_cells):
    """(x0, y, x1, y): a +x line of band-1 cells, length_cells long, clear for a layer-4 eye. Walkers sit at x0 + d."""
    for cx, cy in sc.cells():
        if cx + length_cells < CELLS - 1 and set(sc.band(cx + i, cy) for i in range(length_cells + 1)) == {1} \
                and all(sc.walk(cx + i, cy) for i in range(length_cells + 1)):
            return centre(cx), centre(cy), centre(cx + length_cells), centre(cy)
    raise AssertionError("no band-1 line on seed 11")
