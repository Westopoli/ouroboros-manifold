# spec: docs/northstar/plans/cascades/lab-stage4/spec.md::Acceptance criteria::AC-1
# Rule pins: none (lab harness story H-088)
"""Shared fixtures for the H-088 (stage 4, sight) tests (not a test file), built on h063_fixtures.

VANTAGE (spec criterion 5): `small_tiered`, side A eight Vanguards at layer 1 in a block at x 1400, y 1860 to 2140, side B eight Vanguards at layer 0 at x 2600, same
rows, orders `hold:A`, feature `{kind: vantage, x: 1100, y: 2000, radius: 700, height_band: 1}`. `layer = 1` rows stand one band up with no terrain built.
COVER (criterion 6): `small_flat`, eight Vanguards a side at x 1700 (A) and x 2300 (B), same rows, orders `hold:A`, three 120 x 60 boxes at x 2000, y 1900 / 2000 / 2100.
`crossing_pairs` is criterion 6's "segment crosses a box's cells" (the engine blocks whole 100 wu cells, R-097-01; under `--sight on` the cells are the snapped rectangles, snap.built_rects).

SIGHT_OFF_PIN is criterion 1's byte pin: the H-063 chokepoint fixture (`fx.planar("chokepoint", "L-9800")`), `--sight off --cap-seconds 30 --control-dir D`, seed 1, run on
the code of main 240773dd (before the leaf): the sha256 of the main fight file, of the control twin's fight file and of results.md. A fight file carries its layout's path,
which is a temporary directory here, so the one `"layout_path": "<value>"` string is replaced by the constant `"layout_path_pinned"` before hashing; every other byte is
the file's."""
import hashlib
import json
import math
from pathlib import Path

import h063_fixtures as fx
from scripts.skilllab.arena import features, snap

VANTAGE_FEATURE = {"kind": "vantage", "x": 1100.0, "y": 2000.0, "radius": 700.0, "height_band": 1}
COVER_BOXES = [fx.rect(2000, y, 120, 60) for y in (1900, 2000, 2100)]
COVER_FEATURE = {"kind": "cover", "x": 2000.0, "y": 2000.0, "boxes": COVER_BOXES}
NAV_CELL = features.NAV_CELL

PIN_LAYOUT_ID = "L-9800"
SIGHT_OFF_PIN = {   # recorded on main 240773dd, --sight off, seed 1, --cap-seconds 30 (identical across two runs in two directories); the two fight shas re-recorded 2026-11-07 for the per-unit `fired` key (the files minus every `fired` line have the old shas)
    "fight": "02699f1dcdddb52c1e6b6b829a3df75765a4fda62fe2864a67eb92c15212cd77",
    "control_fight": "9a25efc3a4d4aa3e47a60b536c79d5919be644b95ea2888ab6068750e0e23b78",
    "results": "77344e7f95361548035c57835c54bf310985c7fc56a093161238e6c7f2615719",
}
# Re-recorded 2026-11-08 (engine rule fixes F1 to F4; Test-defect): was fight 37902ffe, control_fight 608e81cb, results 1903a2be. The chokepoint walkers now go through the gap instead of parking at the
# walls (F1), a mover does not fire (F2), a lock holds (F3). The new files (600 ticks, cap) carry no `violations` or `invalid`: the run passes every check of scripts/skilllab/invariants.py.


def vantage_layout(lid, orders="hold:A"):
    """The VANTAGE fixture; `orders` hold:B makes B the (guarded) holder, the geometry unchanged."""
    return {"id": lid, "situation": "vantage", "landscape": "small_tiered", "seed": 1, "predict": "A", "predict_why": "Test fixture.", "verdict": "", "feedback": "",
            "defender": "A", "orders": orders, "side_a": {"headcount": 8, "units": fx.block(8, 1400.0, 2000.0, 0.0, layer=1, cols=8)},
            "side_b": {"headcount": 8, "units": fx.block(8, 2600.0, 2000.0, round(math.pi, 4), layer=0, cols=8)}, "features": [dict(VANTAGE_FEATURE)]}


def cover_layout(lid, boxes=True, orders="hold:A"):
    """The COVER fixture; `boxes` False is the same units with `features` emptied (an open field, as `fx.without_features` makes it)."""
    lay = {"id": lid, "situation": "cover", "landscape": "small_flat", "seed": 1, "predict": "A", "predict_why": "Test fixture.", "verdict": "", "feedback": "",
           "defender": "A", "orders": orders, "side_a": {"headcount": 8, "units": fx.block(8, 1700.0, 2000.0, 0.0, cols=8)},
           "side_b": {"headcount": 8, "units": fx.block(8, 2300.0, 2000.0, round(math.pi, 4), cols=8)}, "features": [dict(COVER_FEATURE, boxes=[dict(b) for b in COVER_BOXES])]}
    return lay if boxes else fx.without_features(lay)


def open_layout(lid, orders="both_same_point", roles=("Vanguard", "Vanguard")):
    """Two sides of eight on small_flat, no features, no walls (an open field); `roles` is (side A role, side B role)."""
    lay = fx.layout(lid, "open_field", "small_flat", None, orders=orders, ax=1700.0, bx=2300.0)
    for key, role in (("side_a", roles[0]), ("side_b", roles[1])):
        for u in lay[key]["units"]:
            u["role"] = role
    return lay


def blocked_cells(layout):
    """[(x0, y0, x1, y1)] the engine blocks for the layout under `--sight on`: the rectangles snapped to the 100 wu grid (snap.built_rects, no pad)."""
    return snap.built_rects(layout)


def crosses(a, b, cells):
    """True when the segment a -> b passes through the open interior of one of `cells` (sampled every wu; a segment that only grazes an edge is not counted, so the
    pairs this names are the ones the engine's blocked cells certainly hide)."""
    steps = max(1, int(math.dist(a, b)))
    for k in range(steps + 1):
        x, y = a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps
        if any(x0 < x < x1 and y0 < y < y1 for x0, y0, x1, y1 in cells):
            return True
    return False


def crossing_pairs(layout, units):
    """[(a id, b id)] for every side A unit and side B unit of `units` (a frame's unit rows) whose segment crosses a blocked cell of the layout's features."""
    cells = blocked_cells(layout)
    return [(a["id"], b["id"]) for a in units if a["side"] == "A" for b in units if b["side"] == "B" and crosses((a["x"], a["y"]), (b["x"], b["y"]), cells)]


def _pinned_sha(path):
    raw = Path(path).read_text()
    shown = json.dumps(json.loads(raw)["layout_path"])
    assert raw.count(shown) == 1
    return hashlib.sha256(raw.replace(shown, '"layout_path_pinned"').encode()).hexdigest()


def sight_off_digests(directory):
    """Run the pinned fixture with `--sight off` into `directory`; returns (process, {"fight", "control_fight", "results"} sha256 hexdigests of the files written)."""
    directory = Path(directory)
    control = directory / "control"
    proc, _ = fx.fight(fx.planar("chokepoint", PIN_LAYOUT_ID)[0], directory, 1, "--sight", "off", "--cap-seconds", "30", "--control-dir", control)
    if proc.returncode != 0:
        return proc, {}
    return proc, {"fight": _pinned_sha(directory / "out" / (PIN_LAYOUT_ID + "-s1.fight.json")),
                  "control_fight": _pinned_sha(control / (PIN_LAYOUT_ID + "-control-s1.fight.json")),
                  "results": hashlib.sha256((directory / "out" / "results.md").read_bytes()).hexdigest()}
