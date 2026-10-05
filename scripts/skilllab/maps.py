"""Situation sampler: deterministic space maps in play coordinates (plan Phase S, item 5b).
The draw ranges are documented design numbers, not thresholds."""
import random
from typing import NamedTuple

from scripts.skilllab.contract import Block, Cover, Terrain
from scripts.skilllab.terrain import _validate_terrain

KINDS = ("open", "block", "wall", "lane", "cover_field")


class Frame(NamedTuple):
    """Where the fight is, in play coordinates: the two spawns and the layer the groups fight on."""
    spawn0: tuple
    spawn1: tuple
    layer: int


# The landscape scene's group anchors (asym_play, 16 v 16 blobs) minus half the canvas; both groups start on layer 0.
DEFAULT_FRAME = Frame((-445.0, 0.0), (445.0, 0.0), 0)

# provisional (lab draft, 2026-10-05): all sizes and ranges below
BLOCK_SIDE = (200, 800)       # block width and height
BLOCK_CENTRE_X = 200          # block centre x within +-this of the segment midpoint
WALL_LENGTH = (1200, 2400)
WALL_THICK = (60, 120)
WALL_X = 250                  # wall centre x within +-this of the segment midpoint
WALL_GAP = (150, 400)
LANE_LENGTH_PAST = (100, 800)  # how far each lane wall runs past its spawn
LANE_THICK = (60, 120)
LANE_HALF = (80, 200)         # half the lane width
LANE_CENTRE = 40              # lane centre within +-this of the segment
COVER_RADIUS = (50, 150)
COVER_COUNT = (3, 8)
COVER_X = 300                 # the corridor disc's x within +-this of the segment midpoint


def _layers(rng, fight):
    lo = rng.randint(0, fight)
    return lo, rng.randint(fight, 4)


def _mid(f):
    return (f.spawn0[0] + f.spawn1[0]) / 2, (f.spawn0[1] + f.spawn1[1]) / 2


def _block(rng, f):
    w, h = rng.uniform(*BLOCK_SIDE), rng.uniform(*BLOCK_SIDE)
    mx, my = _mid(f)
    cx, cy = mx + rng.uniform(-BLOCK_CENTRE_X, BLOCK_CENTRE_X), my + rng.uniform(-h / 2 + 50, h / 2 - 50)
    lo, hi = _layers(rng, f.layer)
    return (Block(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, lo, hi),)


def _wall(rng, f):
    length, thick = rng.uniform(*WALL_LENGTH), rng.uniform(*WALL_THICK)
    mx, my = _mid(f)
    cx, cy = mx + rng.uniform(-WALL_X, WALL_X), my + rng.uniform(-300, 300)
    gap = rng.uniform(*WALL_GAP)
    y0, y1 = cy - length / 2, cy + length / 2
    gc = rng.uniform(y0 + gap / 2, y1 - gap / 2)
    lo, hi = _layers(rng, f.layer)
    x0, x1 = cx - thick / 2, cx + thick / 2
    return (Block(x0, y0, x1, gc - gap / 2, lo, hi), Block(x0, gc + gap / 2, x1, y1, lo, hi))


def _lane(rng, f):
    (l0, r0), (l1, r1) = (((f.spawn0[0] - rng.uniform(*LANE_LENGTH_PAST)), (f.spawn1[0] + rng.uniform(*LANE_LENGTH_PAST)))
                          for _ in range(2))
    t0, t1 = rng.uniform(*LANE_THICK), rng.uniform(*LANE_THICK)
    half, centre = rng.uniform(*LANE_HALF), _mid(f)[1] + rng.uniform(-LANE_CENTRE, LANE_CENTRE)
    lo, hi = _layers(rng, f.layer)
    return (Block(l0, centre - half - t0, r0, centre - half, lo, hi),
            Block(l1, centre + half, r1, centre + half + t1, lo, hi))


def _cover_field(rng, f):
    mx, my = _mid(f)
    r = rng.uniform(*COVER_RADIUS)
    first = Cover(mx + rng.uniform(-COVER_X, COVER_X), my + rng.uniform(-r, r), r, rng.randint(f.layer + 1, 5))
    rest = tuple(Cover(rng.uniform(-1200, 1200), rng.uniform(-1000, 1000), rng.uniform(*COVER_RADIUS), rng.randint(1, 5))
                 for _ in range(rng.randint(*COVER_COUNT) - 1))
    return (first,) + rest


def sample_map(kind, seed, canvas=(4000.0, 4000.0), frame=DEFAULT_FRAME):
    if kind not in KINDS:
        raise ValueError("unknown map kind %r, expected one of %r" % (kind, KINDS))
    rng = random.Random(seed)
    blocks, covers = (), ()
    if kind in ("block", "wall", "lane"):
        blocks = {"block": _block, "wall": _wall, "lane": _lane}[kind](rng, frame)
    elif kind == "cover_field":
        covers = _cover_field(rng, frame)
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
