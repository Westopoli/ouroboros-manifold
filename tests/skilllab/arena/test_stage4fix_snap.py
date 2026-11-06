# Rule pins: R-097-01, R-007-06
# spec: docs/reports/2026-11-06-stage4-fix-plan.md::F2 (what blocks is what is drawn); Story H-088 follow-up; Flag client
"""Stage 4 fix F2: what blocks is what is drawn (scripts/skilllab/arena/snap.py, features.apply(exact=True), run.py `SNAPPED` lines, fight file `built_features`).

The engine blocks whole 100 wu cells (R-097-01, csrc/om_constants.h:585) and the lab used to pad each rectangle 1 wu and assume 50 wu cells, so every wall, box and
building blocked up to 99 wu a side more than it was drawn (L-0039: three 120 x 60 boxes became one 300 x 600 block, investigation 2026-11-06). Under `--sight on`
each feature rectangle is snapped to the grid at conversion; the authored layout files do not change; `--sight off` keeps the stage 3 conversion byte for byte.

Fixtures: the real catalogue layouts L-0039 (cover) and L-0080 (trap), and a synthetic pair of boxes whose rounding is adverse (edges at 1950 and 2050, a gap of exactly one cell).
The engine's own blocked cells are read through the library symbol om_mapgen_cell_blocked (test-only ctypes), not through any lab helper."""
import ctypes
import hashlib
import tomllib
from pathlib import Path

import pytest

import h063_fixtures as fx
from scripts.skilllab.arena import features, snap, snapshot
from scripts.skilllab.catalogue import produce
from scripts.skilllab.engine import Engine

ROOT = Path(__file__).resolve().parents[3]
CATALOGUE = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"
CELL = 100.0
L0039_SHA = "08f6b535da4fd820da91b5bcef7a7b0f1351135ae9c5ee5efcac1451dc46ad44"   # L-0039.toml as authored, 2026-11-06 (stays byte-identical)
L0061_SHA = "cce66467f47d43786fc6d78184e5fb6d0a53ecb95a230a42616a22cd166c4926"


def _layout(name):
    with open(CATALOGUE / (name + ".toml"), "rb") as f:
        return tomllib.load(f)


def _blocked_cells(layout, exact):
    """{(col, row)} of the cells the engine blocks on layer 0 after features.apply(exact=...) on the layout (om_mapgen_cell_blocked, 100 wu cells)."""
    e = Engine()
    w = e.new_world(1)
    try:
        preset = produce.presets()[layout["landscape"]]
        features.apply(e, w, layout, preset, 1, exact=exact)
        fn = e._lib.om_mapgen_cell_blocked
        fn.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32]
        fn.restype = ctypes.c_int
        n = int(preset["width"] // CELL)
        return {(c, r) for r in range(n) for c in range(n) if fn(w, 0, c, r)}
    finally:
        e.free_world(w)


def _cells(rects):
    return {(c, r) for x0, y0, x1, y1 in rects for r in range(int(y0 // CELL), int(y1 // CELL)) for c in range(int(x0 // CELL), int(x1 // CELL))}


def _authored(layout):
    return [(x - w / 2, y - h / 2, x + w / 2, y + h / 2) for x, y, w, h in features.planar_rects(layout)]


def _two_boxes_adverse():
    boxes = [fx.rect(1900, 2000, 100, 300), fx.rect(2100, 2000, 100, 300)]   # edges 1950 and 2050: one cell apart, each rounds toward the other
    feature = {"kind": "cover", "x": 2000.0, "y": 2000.0, "boxes": boxes}
    return fx.layout("L-9810", "cover", "small_flat", feature)


@pytest.mark.parametrize("name", ["L-0039", "L-0080", "L-0083"])
def test_built_edges_sit_on_the_grid_within_50_wu_of_the_authored_edge(name):
    """R-097-01: the engine's cells are 100 wu. Every snapped edge is a multiple of 100 and within 50 wu of the authored edge; an extent thinner than one cell
    (L-0039's boxes are 60 high) becomes exactly one cell holding the authored centre."""
    lay = _layout(name)
    authored, built = _authored(lay), snap.built_rects(lay)
    assert len(authored) == len(built) > 0
    for a, b in zip(authored, built):
        assert all(abs(v / CELL - round(v / CELL)) < 1e-9 for v in b), b
        for lo, hi, blo, bhi in ((a[0], a[2], b[0], b[2]), (a[1], a[3], b[1], b[3])):
            assert bhi - blo >= CELL
            if hi - lo >= CELL:
                assert abs(blo - lo) <= 50 and abs(bhi - hi) <= 50, (a, b)
            else:
                assert bhi - blo == CELL and blo <= (lo + hi) / 2 <= bhi, (a, b)


def test_a_gap_of_one_cell_stays_open_after_the_snap():
    """The brief: snapping never merges two features' cells across a gap of one cell or more. Edges 1950 and 2050 would both round to 2000 by nearest-edge."""
    built = snap.built_rects(_two_boxes_adverse())
    assert built[1][0] - built[0][2] >= CELL, built


def test_l0039_engine_blocks_exactly_the_snapped_boxes_and_the_lanes_between_them_are_open():
    """R-007-06 (a box blocks only a line that passes through it) and the L-0039 finding: the engine blocked one 300 x 600 block with no gaps. Now it blocks the
    snapped boxes only (three cells), and the rows between them (the drawn gaps) are open."""
    lay = _layout("L-0039")
    built = sorted(snap.built_rects(lay), key=lambda r: r[1])
    blocked = _blocked_cells(lay, True)
    assert blocked == _cells(built) and len(blocked) == 3, len(blocked)
    for (x0, y0, x1, y1), (_, ny0, _, _) in zip(built, built[1:]):
        assert ny0 - y1 >= CELL, "no open lane under %r" % ((x0, y0, x1, y1),)
        assert all((c, int(y1 // CELL)) not in blocked for c in range(int(x0 // CELL), int(x1 // CELL))), "the lane row under %r is blocked" % ((x0, y0, x1, y1),)


def test_the_trap_walls_block_exactly_their_drawn_cells():
    """L-0080's walls are already on the 100 grid: the old 1 wu pad blocked a whole extra ring of cells (investigation L-0083); now the blocked cells are the drawn ones."""
    lay = _layout("L-0080")
    assert _blocked_cells(lay, True) == _cells(_authored(lay))


def test_the_old_conversion_is_unchanged_without_exact():
    """`--sight off` keeps the stage 3 conversion (the stage 3 fights reproduce byte for byte): features.apply without exact still pads and rounds out, so the
    cell between L-0039's first two boxes is blocked, as the investigation found."""
    blocked = _blocked_cells(_layout("L-0039"), False)
    assert (19, 19) in blocked and len(blocked) > 3


def test_the_snapped_line_is_printed_per_feature_under_sight_on_and_not_under_sight_off(tmp_path):
    """The brief: the conversion prints a `SNAPPED` line per feature (authored extent, built extent): one cover feature in L-0039."""
    on = fx.run(CATALOGUE / "L-0039.toml", tmp_path / "on", 1, "--sight", "on", "--cap-seconds", "2")
    lines = [l for l in on.stdout.splitlines() if l.startswith("SNAPPED")]
    assert len(lines) == 1 and "L-0039" in lines[0] and "cover" in lines[0] and "1900" in lines[0], on.stdout
    off = fx.run(CATALOGUE / "L-0039.toml", tmp_path / "off", 1, "--sight", "off", "--cap-seconds", "2")
    assert "SNAPPED" not in off.stdout


def test_drawn_equals_blocked_the_fight_file_carries_the_built_rectangles(tmp_path):
    """The replay draws the fight file's `built_features` (the snapped rectangles), so drawn equals blocked: the cells of those rectangles are the engine's blocked cells."""
    lay = _layout("L-0039")
    proc = fx.run(CATALOGUE / "L-0039.toml", tmp_path, 1, "--sight", "on", "--cap-seconds", "2")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    doc = snapshot.read(tmp_path / "L-0039-s1.fight.json")
    drawn = [(r["x"] - r["w"] / 2, r["y"] - r["h"] / 2, r["x"] + r["w"] / 2, r["y"] + r["h"] / 2) for f in doc["built_features"] for key in features.PLANAR_KEYS for r in f.get(key, [])]
    assert drawn and _cells(drawn) == _blocked_cells(lay, True)


def test_authored_catalogue_files_stay_byte_identical():
    """The snap is a conversion step: L-0039 and L-0061 (Westley's hand-authored layouts) are not rewritten."""
    for name, sha in (("L-0039", L0039_SHA), ("L-0061", L0061_SHA)):
        assert hashlib.sha256((CATALOGUE / (name + ".toml")).read_bytes()).hexdigest() == sha


def test_the_reachability_grid_uses_the_engines_100_wu_cells():
    """R-097-01: features.NAV_CELL is the engine's 100, not 50 (DEC-stage3-reach-engine-rule amended)."""
    assert features.NAV_CELL == 100.0
