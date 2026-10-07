"""Situation sampler: deterministic space maps in play coordinates (plan Phase S, item 5b).
The draw ranges are documented design numbers, not thresholds."""
import math
import random
from dataclasses import dataclass
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
CORRIDOR_WIDTH = 600.0        # provisional (2026-10-05): wu, the corridor between the spawns for cover density
UNIT_RADIUS_WU = 15.0         # provisional (2026-10-05): collision radius used when no engine is given
LAYOUT_BODY_WU = 30.0         # provisional (2026-10-06): 2R, hardcoded until D1
LAYOUT_WALL_THICK = 90.0      # provisional (2026-10-06): mid of WALL_THICK
LAYOUT_WALL_HALF = 600.0      # provisional (2026-10-06): wall half-length when no detour ratio is asked for
LAYOUT_LANE_HALF = 140.0      # provisional (2026-10-06): mid of LANE_HALF
LAYOUT_LANE_PAST = 400.0      # provisional (2026-10-06): mid of LANE_LENGTH_PAST
CORRIDOR_SLICES = 256         # provisional (2026-10-05): fixed slice count for partial disc overlap


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


def layout_map(features, seed, canvas=(4000.0, 4000.0), frame=DEFAULT_FRAME):
    f = features
    mx, my = _mid(frame)
    d = math.dist(frame.spawn0, frame.spawn1)
    lo, hi = 0, f.blocked_layer_top
    blocks = []
    if f.choke_width_bodies:
        gap, t = f.choke_width_bodies * LAYOUT_BODY_WU, LAYOUT_WALL_THICK
        top = LAYOUT_WALL_HALF
        if f.detour_ratio:
            top = math.sqrt(((f.detour_ratio * d - t) / 2) ** 2 - ((d - t) / 2) ** 2)
        x0, x1 = mx - t / 2, mx + t / 2
        blocks += [Block(x0, my - top, x1, my - gap / 2, lo, hi), Block(x0, my + gap / 2, x1, my + top, lo, hi)]
    n, t, half = f.lane_count, LAYOUT_WALL_THICK, LAYOUT_LANE_HALF
    if n:
        lx0, lx1 = frame.spawn0[0] - LAYOUT_LANE_PAST, frame.spawn1[0] + LAYOUT_LANE_PAST
        edges = [(-half - t, -half), (half, half + t)] if n == 1 else [
            (-t / 2, t / 2), (-t / 2 - 2 * half - t, -t / 2 - 2 * half), (t / 2 + 2 * half, t / 2 + 2 * half + t)]
        if n == 2 and f.choke_width_bodies:   # axis and choke gap sit inside the first channel
            edges = [(-half - t, -half), (half, half + t), (3 * half + t, 3 * half + 2 * t)]
        blocks += [Block(lx0, my + a, lx1, my + b, lo, hi) for a, b in sorted(edges)]
    covers = ()
    if f.cover_density_corridor:
        rng = random.Random(seed)
        area = f.cover_density_corridor * d * CORRIDOR_WIDTH
        m = math.ceil(area / (math.pi * COVER_RADIUS[1] ** 2))
        r = math.sqrt(area / (m * math.pi))
        covers = tuple(Cover(rng.uniform(frame.spawn0[0] + r, frame.spawn1[0] - r),
                             rng.uniform(my - CORRIDOR_WIDTH / 2 + r, my + CORRIDOR_WIDTH / 2 - r), r, rng.randint(1, 5))
                       for _ in range(m))
    terrain = Terrain(canvas=canvas, blocks=tuple(blocks), covers=covers)
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


@dataclass(frozen=True)
class Features:
    """What a sampled map does to a fight, one record per map (field order is the feat_ column order)."""
    choke_count: int
    choke_width_wu: float
    choke_width_bodies: float
    lane_count: int
    blocked_layer_ranges: tuple
    fight_layer_blocked: bool
    cover_density_corridor: float
    start_distance: float
    detour_ratio: float = 0.0
    blocked_layer_top: int = 0


def _disc_in_corridor(cu, cv, r, length, half_w):
    """Area of the disc (centre cu, cv in corridor coordinates) inside [0, length] x [-half_w, half_w]."""
    if cu - r >= 0 and cu + r <= length and abs(cv) + r <= half_w:
        return math.pi * r * r
    lo, hi = max(cu - r, 0.0), min(cu + r, length)
    if hi <= lo:
        return 0.0
    h = (hi - lo) / CORRIDOR_SLICES
    area = 0.0
    for i in range(CORRIDOR_SLICES):
        u = lo + (i + 0.5) * h
        c = math.sqrt(max(r * r - (u - cu) ** 2, 0.0))
        area += max(min(cv + c, half_w) - max(cv - c, -half_w), 0.0) * h
    return area


def sample_features(kind, seed, canvas=(4000.0, 4000.0), frame=DEFAULT_FRAME):
    terrain = sample_map(kind, seed, canvas, frame)
    dx, dy = frame.spawn1[0] - frame.spawn0[0], frame.spawn1[1] - frame.spawn0[1]
    dist = math.sqrt(dx * dx + dy * dy)
    ranges = tuple((b.layer_lo, b.layer_hi) for b in terrain.blocks)
    gap = 0.0
    if kind == "wall":
        a, b = terrain.blocks
        gap = float(b.y0 - a.y1)
    density = 0.0
    if terrain.covers and dist > 0:
        ux, uy = dx / dist, dy / dist
        area = 0.0
        for c in terrain.covers:
            rx, ry = c.x - frame.spawn0[0], c.y - frame.spawn0[1]
            area += _disc_in_corridor(rx * ux + ry * uy, -rx * uy + ry * ux, c.radius, dist, CORRIDOR_WIDTH / 2)
        density = area / (dist * CORRIDOR_WIDTH)
    return Features(
        choke_count=1 if kind == "wall" else 0,
        choke_width_wu=gap,
        choke_width_bodies=gap / (2 * UNIT_RADIUS_WU),
        lane_count=1 if kind == "lane" else 0,
        blocked_layer_ranges=ranges,
        fight_layer_blocked=any(lo <= frame.layer <= hi for lo, hi in ranges),
        cover_density_corridor=float(density),
        start_distance=float(dist),
    )
