"""Shared fixtures for the H-063 tests (not a test file): layouts with ground features in the H-025 TOML schema, a runner call, and frame readers.
Geometry recipe (premises dumped 2026-11-02 on base aac0cd41, Vanguards, sight off, default orders both_same_point): side A block at x 1000, side B at x 3000, same
y; both attack-move to the midpoint (2000, y) and stop when the enemy is in the 300 wu range, resting near x 1850 and x 2150. A feature rectangle centred at
(2000, y), 600 wu wide, therefore holds the resting units when the engine ignores it (the stage 2 runner does) and holds none when the engine blocks it."""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.arena import snapshot  # noqa: E402
from scripts.skilllab.catalogue import produce  # noqa: E402

PITCH = 40.0
YC = 2000.0


def rect(x, y, w, h):
    return {"x": float(x), "y": float(y), "w": float(w), "h": float(h)}


def block(n, x0, yc, face, layer=0, cols=4, role="Vanguard"):
    return [{"role": role, "x": x0 + (i // cols) * PITCH, "y": yc + ((i % cols) - (cols - 1) / 2) * PITCH, "facing": face, "layer": layer} for i in range(n)]


def layout(lid, situation, landscape, feature, yc=YC, orders="both_same_point", a_layer=0, ax=1000.0, bx=3000.0):
    a, b = block(8, ax, yc, 0.0, a_layer), block(8, bx, yc, round(math.pi, 4))
    out = {"id": lid, "situation": situation, "landscape": landscape, "seed": 1, "predict": "A", "predict_why": "Test fixture.", "verdict": "", "feedback": "",
           "defender": "A", "orders": orders, "side_a": {"headcount": 8, "units": a}, "side_b": {"headcount": 8, "units": b}}
    if feature is not None:
        out["features"] = [feature]
    return out


def without_features(lay):
    """The control: the same units and ids, `features` emptied. R6 wants a feature for every situation but open_field, so the situation becomes open_field."""
    out = json.loads(json.dumps(lay))
    out.pop("features", None)
    out["situation"] = "open_field"
    out["defender"] = ""
    return out


# the four planar kinds: (kind, landscape, feature dict, rectangles that block). Rectangles are centre x, y, width w, height h (produce._rect).
def _chokepoint():
    walls = [rect(2000, YC - 350, 600, 500), rect(2000, YC + 350, 600, 500)]   # a 200 wu gap between them at y 1900 to 2100
    return "chokepoint", "small_flat", {"kind": "chokepoint", "x": 2000.0, "y": YC, "gap": 200, "radius": 600, "walls": walls}, walls, YC - 350


def _cover():
    boxes = [rect(2000, YC, 600, 300)]
    return "cover", "small_flat", {"kind": "cover", "x": 2000.0, "y": YC, "boxes": boxes}, boxes, YC


def _city():
    buildings = [rect(2000, YC, 600, 600)]
    return "city", "small_flat", {"kind": "city", "x": 2000.0, "y": YC, "radius": 800, "buildings": buildings}, buildings, YC


def _ridge():
    ridge = rect(2000, YC, 600, 1400)
    return ("flank_route", "small_tiered", {"kind": "flank_route", "x": 1000.0, "y": YC, "points": [[1000.0, YC], [2000.0, 3300.0], [3000.0, YC]], "ridge": ridge,
                                            "height_band": 1}, [ridge], YC)


KINDS = {"chokepoint": _chokepoint, "cover": _cover, "city": _city, "ridge": _ridge}


def planar(name, lid):
    """(layout, rectangles) for one planar kind; side blocks sit on the line through the first rectangle's centre y."""
    situation, landscape, feature, rects, yc = KINDS[name]()
    return layout(lid, situation, landscape, feature, yc=yc), rects


def write(lay, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (lay["id"] + ".toml")
    path.write_text(produce.dump_toml(lay))
    return path


def run(path, out, seed=1, *extra):
    cmd = [sys.executable, "-m", "scripts.skilllab.arena.run", "--layout", str(path), "--seed", str(seed), "--out", str(out), *extra]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)


def fight(lay, directory, seed=1, *extra):
    """Run `lay` through the CLI; returns (process, the fight document or None)."""
    path = write(lay, Path(directory) / "layouts")
    out = Path(directory) / "out"
    proc = run(path, out, seed, *extra)
    f = out / ("%s-s%d.fight.json" % (lay["id"], seed))
    return proc, (snapshot.read(f) if f.exists() else None)


def inside(x, y, r):
    """Strictly inside the rectangle (centre x, y, size w, h)."""
    return abs(x - r["x"]) < r["w"] / 2 and abs(y - r["y"]) < r["h"] / 2


def units_inside(doc, rects):
    """[(tick, unit id, x, y)] for every unit position, dead ones included, in any frame, inside any of `rects`."""
    return [(f["tick"], u["id"], u["x"], u["y"]) for f in doc["frames"] for u in f["units"] if any(inside(u["x"], u["y"], r) for r in rects)]
