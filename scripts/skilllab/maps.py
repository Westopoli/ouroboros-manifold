"""Situation sampler: deterministic space maps in play coordinates (plan Phase S, item 5b).
The draw ranges are documented design numbers, not thresholds."""
import random

from scripts.skilllab.contract import Block, Cover, Terrain
from scripts.skilllab.terrain import _validate_terrain

KINDS = ("open", "block", "wall", "lane", "cover_field")


def _layers(rng):
    lo = rng.randint(0, 2)
    return lo, rng.randint(lo, 4)


def _block(rng):
    w, h = rng.uniform(200, 800), rng.uniform(200, 800)
    cx, cy = rng.uniform(-600, 600), rng.uniform(-600, 600)
    lo, hi = _layers(rng)
    return (Block(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, lo, hi),)


def _wall(rng):
    length, thick = rng.uniform(1200, 2400), rng.uniform(60, 120)
    cx, cy = rng.uniform(-500, 500), rng.uniform(-300, 300)
    gap = rng.uniform(150, 400)
    y0, y1 = cy - length / 2, cy + length / 2
    gc = rng.uniform(y0 + gap / 2, y1 - gap / 2)
    lo, hi = _layers(rng)
    x0, x1 = cx - thick / 2, cx + thick / 2
    return (Block(x0, y0, x1, gc - gap / 2, lo, hi), Block(x0, gc + gap / 2, x1, y1, lo, hi))


def _lane(rng):
    walls = []
    for _ in range(2):
        walls.append((rng.uniform(1200, 2400), rng.uniform(60, 120), rng.uniform(-300, 300)))
    half, centre = rng.uniform(100, 250), rng.uniform(-100, 100)
    lo, hi = _layers(rng)
    (l0, t0, x0), (l1, t1, x1) = walls
    return (Block(x0 - l0 / 2, centre - half - t0, x0 + l0 / 2, centre - half, lo, hi),
            Block(x1 - l1 / 2, centre + half, x1 + l1 / 2, centre + half + t1, lo, hi))


def _cover_field(rng):
    return tuple(Cover(rng.uniform(-1200, 1200), rng.uniform(-1000, 1000), rng.uniform(50, 150), rng.randint(1, 5))
                 for _ in range(rng.randint(3, 8)))


def sample_map(kind, seed, canvas=(4000.0, 4000.0)):
    if kind not in KINDS:
        raise ValueError("unknown map kind %r, expected one of %r" % (kind, KINDS))
    rng = random.Random(seed)
    blocks, covers = (), ()
    if kind in ("block", "wall", "lane"):
        blocks = {"block": _block, "wall": _wall, "lane": _lane}[kind](rng)
    elif kind == "cover_field":
        covers = _cover_field(rng)
    terrain = Terrain(canvas=canvas, blocks=blocks, covers=covers)
    _validate_terrain(terrain)
    return terrain


def sample_maps(kinds, per_kind, seed=0):
    if per_kind < 1:
        raise ValueError("per_kind must be at least 1, got %r" % per_kind)
    for k in kinds:
        if k not in KINDS:
            raise ValueError("unknown map kind %r, expected one of %r" % (k, KINDS))
    out = []
    for k in kinds:
        for _ in range(per_kind):
            map_seed = seed * 1000 + len(out)
            out.append((k, map_seed, sample_map(k, map_seed)))
    return out
