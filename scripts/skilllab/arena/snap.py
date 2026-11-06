"""Snap the layout's planar feature rectangles to the engine's block grid (stage 4 fix F2; docs/reports/2026-11-06-stage4-fix-plan.md, DEC-stage4-snap-100-2026-11-06).

The engine blocks whole 100 wu cells (`om_map_block_rect` rounds a rectangle outward to OM_NAVMESH_CELL_SIZE cells, csrc/tactical_mapgen.c:851-882; R-097-01,
csrc/om_constants.h:585). Under `--sight on` each wall, box, building and ridge rectangle is snapped at conversion so that what is blocked is what is drawn: each edge to the
nearest cell edge (a tie to the lower), an extent thinner than one cell becomes the one cell that holds its centre (the upper cell when the centre is on a boundary),
and two rectangles that are a cell or more apart as authored stay a cell or more apart (the later one is moved away by whole cells). The authored layout is never
rewritten. `built_features` is the layout's feature list with the snapped rectangles, which the fight file carries and the replay draws.
See also: scripts/skilllab/arena/features.py (`_engine_boxes`, the old pad-and-round conversion kept for `--sight off`)."""
import copy
import math

from scripts.skilllab.arena import features

CELL = 100.0   # OM_NAVMESH_CELL_SIZE


def _edge(v):
    return math.ceil(v / CELL - 0.5) * CELL   # nearest cell edge, a tie to the lower


def snap_rect(x0, y0, x1, y1):
    """The (x0, y0, x1, y1) snapped to whole cells, at least one cell each way."""
    out = []
    for lo, hi in ((x0, x1), (y0, y1)):
        a, b = _edge(lo), _edge(hi)
        if b - a < CELL:
            a = math.floor((lo + hi) / 2 / CELL) * CELL
            b = a + CELL
        out.append((a, b))
    return (out[0][0], out[1][0], out[0][1], out[1][1])


def _keep_gaps(authored, built):
    """Move a rectangle away, a whole cell at a time, where snapping closed a gap of a cell or more between it and an earlier rectangle that it faces."""
    for _ in range(len(built) + 2):
        moved = False
        for j in range(len(built)):
            for i in range(j):
                for axis in (0, 1):
                    lo, hi, other = (0, 2, 1) if axis == 0 else (1, 3, 0)
                    a, b, ba, bb = authored[i], authored[j], built[i], built[j]
                    if min(ba[other + 2], bb[other + 2]) - max(ba[other], bb[other]) <= 0:
                        continue   # they do not face each other once snapped
                    gap = max(b[lo] - a[hi], a[lo] - b[hi])
                    if gap < CELL:
                        continue
                    sgap = bb[lo] - ba[hi] if b[lo] >= a[hi] else ba[lo] - bb[hi]
                    if sgap >= CELL:
                        continue
                    shift = (CELL - sgap) * (1 if b[lo] >= a[hi] else -1)
                    built[j] = tuple(v + shift if k in (lo, hi) else v for k, v in enumerate(bb))
                    moved = True
        if not moved:
            return built
    raise ValueError("snap: the gaps between the features cannot be kept open")


def authored_rects(layout):
    """[(x0, y0, x1, y1)] of every wall, box, building and ridge rectangle, in the order of features.planar_rects."""
    return [(x - w / 2, y - h / 2, x + w / 2, y + h / 2) for x, y, w, h in features.planar_rects(layout)]


def built_rects(layout):
    """[(x0, y0, x1, y1)] the snapped rectangles, one per authored rectangle, same order."""
    authored = authored_rects(layout)
    return _keep_gaps(authored, [snap_rect(*r) for r in authored])


def built_features(layout):
    """A copy of the layout's `features` with every planar rectangle replaced by its snapped one (centre and size), other features unchanged."""
    built = iter(built_rects(layout))
    out = copy.deepcopy(layout.get("features", []))
    for f in out:
        for r in features._feature_rects(f):
            x0, y0, x1, y1 = next(built)
            r.update(x=(x0 + x1) / 2, y=(y0 + y1) / 2, w=x1 - x0, h=y1 - y0)
    return out


def report(layout):
    """['SNAPPED <id> <kind> authored [x0 y0 x1 y1] ... built [x0 y0 x1 y1] ...'] one per feature that carries rectangles: the authored and built extents."""
    built, lines = iter(built_rects(layout)), []
    authored = iter(authored_rects(layout))
    fmt = lambda rs: " ".join("[%g %g %g %g]" % r for r in rs)
    for f in layout.get("features", []):
        n = len(features._feature_rects(f))
        if n:
            lines.append("SNAPPED %s %s authored %s built %s" % (layout["id"], f["kind"], fmt([next(authored) for _ in range(n)]), fmt([next(built) for _ in range(n)])))
    return lines
