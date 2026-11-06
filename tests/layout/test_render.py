# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-8
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-9
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-10
"""S-247 wave 1, leaf 3: scripts/layout/render.py draws an om-layout-1 JSON as a PNG and a 12-seed sheet (R-112-04
picture; Westley judges by these pictures, DEC-no-look-pass-2026-11-05: no agent opens one, so exact checks on the
pixels are these tests). No C is built: tests/layout/fixtures/layout_hand.json is hand-written JSON of the schema.

Colours, tile order and the sidebar's width are the renderer's to choose (spec says "side A in one colour, side B in
another, neutral grey" and nothing more), so each pixel test compares a render with a variant of itself (a place moved
away, a lane widened, a drafts value changed) instead of naming a colour. The fixture's canvas is 8,000 wu = 400 px at
DRAFT_PX_WU 20; A base, the objective and B base sit on the centre line y = 4,000 and the two resources mirror each
other about it, so those samples do not depend on whether the renderer draws y downward or upward.
Red until scripts/layout/render.py exists. At most 40 assertions in this file (counted by `assert` statements).
"""
import ast
import copy
import json
import pathlib
import subprocess
import sys

import pytest
from PIL import Image, ImageChops

REPO = pathlib.Path(__file__).resolve().parents[2]
RENDER = REPO / "scripts" / "layout" / "render.py"
FIXTURE = REPO / "tests" / "layout" / "fixtures" / "layout_hand.json"
PX_WU = 20.0                       # DRAFT_PX_WU (spec "Named drafts")
CANVAS = 8000.0                    # the fixture's canvas
MAP = int(CANVAS / PX_WU)          # 400 px: the map area of the picture, sidebar to its right
EDGE = 8                           # px kept clear of the map/sidebar seam (LANCZOS reduction blends a few px)
GREY_SPREAD = 16                   # max channel spread that still reads as neutral grey (question render-Q4)
FAR = 7800.0                       # where a "removed" item is parked: far from everything in the fixture
SHEET_COLS, SHEET_ROWS = 4, 3      # spec: "12 layouts ... in a 4 by 3 grid"
BASE = json.loads(FIXTURE.read_text())


def run(*args):
    assert RENDER.exists(), "scripts/layout/render.py is leaf 3 of the S-247 cascade"
    return subprocess.run([sys.executable, str(RENDER), *map(str, args)], capture_output=True, text=True,
                          timeout=120, env={"PATH": "/usr/bin:/bin", "DISPLAY": ""})


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("render")


@pytest.fixture(scope="module")
def draw(work):
    """draw(key, mutate) -> RGB image of `render.py map` on a copy of the fixture changed by mutate(doc); cached."""
    cache = {}

    def _draw(key, mutate=None):
        if key not in cache:
            doc = copy.deepcopy(BASE)
            if mutate:
                mutate(doc)
            src, out = work / f"{key}.json", work / f"{key}.png"
            src.write_text(json.dumps(doc))
            r = run("map", src, out)
            assert r.returncode == 0 and out.is_file(), (key, r.returncode, r.stderr[-600:])
            cache[key] = Image.open(out).convert("RGB")
        return cache[key]
    return _draw


def home(x, y):
    return int(round(x / PX_WU)), int(round(y / PX_WU))


def boxes(x_wu, y_wu, half_px):
    """The same world point as a pixel box for a y-down and for a y-up picture (the spec fixes neither)."""
    cx, cy = home(x_wu, y_wu)
    return [(cx - half_px, cy - half_px, cx + half_px + 1, cy - half_px + 2 * half_px + 1),
            (cx - half_px, MAP - cy - half_px, cx + half_px + 1, MAP - cy + half_px + 1)]


def changed_pixels(a, b, box):
    d = ImageChops.difference(a.crop(box), b.crop(box)).convert("L")
    return sum(1 for v in d.tobytes() if v)


def mode_colour(img, cx, cy, half=2):
    px = [img.getpixel((x, y)) for x in range(cx - half, cx + half + 1) for y in range(cy - half, cy + half + 1)]
    return max(set(px), key=px.count)


def moved(index):
    def f(doc):
        doc["places"][index]["x"] = doc["places"][index]["y"] = FAR
    return f


# ---- the map picture --------------------------------------------------------------------------------------------------
def test_S_247_map_writes_a_png_with_a_sidebar_beside_the_map(work):
    """S-247 R-112-04 (criterion 8): `render.py map <json> <png>` exits 0 and writes a PNG at least the map's size
    (canvas / 20 wu per px = 400 px square) and wider than it (a sidebar on the right)."""
    out = work / "plain.png"
    r = run("map", FIXTURE, out)
    img = Image.open(out) if out.is_file() else None
    assert r.returncode == 0 and img is not None and img.format == "PNG" and img.width > MAP and img.height >= MAP, r.stderr[-500:]


@pytest.mark.parametrize("index", range(len(BASE["places"])), ids=[p["kind"] + "_" + p["side"] for p in BASE["places"]])
def test_S_247_every_place_is_drawn_where_it_is_at_20_wu_a_pixel(draw, index):
    """S-247 R-112-04 (criterion 8): moving one place far away changes the picture near its coordinates / 20 (within
    its pad radius), so places are drawn at DRAFT_PX_WU 20 wu per pixel."""
    p = BASE["places"][index]
    half = int(p["pad_r"] / PX_WU) + 2
    full, away = draw("full"), draw(f"away{index}", moved(index))
    assert max(changed_pixels(full, away, b) for b in boxes(p["x"], p["y"], half)) > 0


def test_S_247_side_a_side_b_and_neutral_places_have_their_own_colours(draw):
    """S-247 R-112-04 (criterion 8): the A base and the B base (on the centre line) are drawn in different colours,
    each differing from the ground under it; neutral resources are grey."""
    full = draw("full")
    ax, bx = home(1200.0, 4000.0), home(6000.0, 4000.0)
    ground_a, ground_b = draw("away2", moved(2)), draw("away1", moved(1))
    ca, cb = mode_colour(full, *ax), mode_colour(full, *bx)
    grey = [mode_colour(full, *home(3000.0, y)) for y in (2400.0, 5600.0)]
    assert ca != cb and ca != mode_colour(ground_a, *ax) and cb != mode_colour(ground_b, *bx) \
        and all(max(c) - min(c) <= GREY_SPREAD for c in grey)


def test_S_247_a_lane_is_a_strip_with_its_width_to_scale(draw):
    """S-247 R-112-04 (criterion 8): a 120 wu lane is a strip about 6 px wide; widening it to 600 wu (30 px) changes
    pixels 10 px either side of its centre line and none 25 px either side."""
    narrow, wide = draw("full"), draw("wide", lambda d: d["lanes"][0].__setitem__("width", 600.0))
    cx, cy = home(2200.0, 4000.0)
    near = [changed_pixels(narrow, wide, (cx, cy + dy, cx + 1, cy + dy + 1)) for dy in (-10, 10)]
    far = [changed_pixels(narrow, wide, (cx, cy + dy, cx + 1, cy + dy + 1)) for dy in (-25, 25)]
    assert near == [1, 1] and far == [0, 0]


def test_S_247_a_way_round_lane_is_dashed_and_a_route_lane_is_solid(draw):
    """S-247 R-112-04 (criterion 8): a way_round lane covers fewer pixels than the same lane drawn as a route (it is
    dashed) but still some; measured as the pixels that change when the lane is parked away."""
    def lane2(kind, parked):
        def f(doc):
            doc["lanes"][2]["kind"] = kind
            if parked:
                doc["lanes"][2]["pts"] = [[FAR - 800.0, FAR], [FAR - 600.0, FAR], [FAR - 200.0, FAR], [FAR, FAR]]
        return f

    def at(kind, parked):
        return draw(f"{kind}-{'away' if parked else 'on'}", lane2(kind, parked))
    seg = [b for b in boxes(3400.0, 3000.0, 1)]       # centre of the lane's horizontal middle segment
    box = [(150, b[1] - 5, 191, b[3] + 5) for b in seg]
    solid = [changed_pixels(at("route", False), at("route", True), b) for b in box]
    dashed = [changed_pixels(at("way_round", False), at("way_round", True), b) for b in box]
    side = solid.index(max(solid))
    assert 0 < dashed[side] < solid[side]


@pytest.mark.parametrize("what,x,y,half", [("chokes", 3500.0, 4000.0, 32), ("vantages", 3600.0, 5000.0, 22)])
def test_S_247_chokes_and_vantages_are_drawn(draw, what, x, y, half):
    """S-247 R-112-04 (criterion 8): a choke (its gap and hatched walls, wall_span 400 wu either side) and a vantage
    (triangle and radius circle, 400 wu) appear at their coordinates: removing the list changes the pixels there."""
    full, gone = draw("full"), draw(f"no_{what}", lambda d: d.__setitem__(what, []))
    assert max(changed_pixels(full, gone, b) for b in boxes(x, y, half)) > 0


def _sidebar_edit(kind):
    def f(doc):
        if kind == "drafts_value":
            doc["drafts"]["DRAFT_EQUAL_TOL"] = 0.35
        elif kind == "drafts_new":
            doc["drafts"]["DRAFT_BRAND_NEW_ONE"] = 7.0
        elif kind == "seed":
            doc["seed"] = 2
        elif kind == "check":
            doc["checks"]["bounds"] = False
        elif kind == "fairness":
            doc["fairness"]["dist_a_objective"] = 3999.0
    return f


@pytest.mark.parametrize("kind", ["drafts_value", "drafts_new", "seed", "check", "fairness"])
def test_S_247_the_sidebar_shows_the_drafts_seed_checks_and_distances(draw, kind):
    """S-247 R-112-04 (criterion 8): changing a drafts value, adding a draft, the seed, a check result or a route
    distance in the JSON changes the sidebar (right of the map) and leaves the map itself untouched."""
    a, b = draw("full"), draw(f"side_{kind}", _sidebar_edit(kind))
    h = min(a.height, b.height)
    side = changed_pixels(a, b, (MAP, 0, min(a.width, b.width), h))
    mapped = changed_pixels(a, b, (0, 0, MAP - EDGE, MAP))
    assert (side > 0, mapped) == (True, 0)


# ---- the sheet --------------------------------------------------------------------------------------------------------
def _sheet(work, name, mutate=None, drop=None):
    """12 fixture copies with seeds 1..12 in work/name/, run `sheet`, return (returncode, image)."""
    d = work / name
    d.mkdir(exist_ok=True)
    for s in range(1, 13):
        doc = copy.deepcopy(BASE)
        doc["seed"] = s
        if mutate:
            mutate(s, doc)
        if s != drop:
            (d / f"layout_assault_s{s}_separate.json").write_text(json.dumps(doc))
    out = work / f"{name}.png"
    r = run("sheet", d, out)
    return r.returncode, (Image.open(out).convert("RGB") if out.is_file() else None), r.stderr


def _cells(img):
    cw, ch = img.width // SHEET_COLS, img.height // SHEET_ROWS
    return [img.crop((c * cw + EDGE, r * ch + EDGE, (c + 1) * cw - EDGE, (r + 1) * ch - EDGE))
            for r in range(SHEET_ROWS) for c in range(SHEET_COLS)]


def _differing(a, b):
    return [i for i, (x, y) in enumerate(zip(_cells(a), _cells(b))) if ImageChops.difference(x, y).getbbox()]


def test_S_247_the_sheet_has_twelve_tiles_in_a_4_by_3_grid(work):
    """S-247 R-112-04 (criterion 9): 12 fixtures s1..s12 in a directory give exit 0 and one image wider than tall
    whose 4 x 3 cells are all drawn and all different (each tile carries its own seed number)."""
    rc, img, err = _sheet(work, "sheet_full")
    cells = _cells(img) if img else []
    assert rc == 0 and img is not None and img.width > img.height and len(cells) == 12 \
        and all(len(c.getcolors(c.width * c.height)) > 1 for c in cells) and len({c.tobytes() for c in cells}) == 12, err[-500:]


def test_S_247_a_missing_seed_leaves_one_empty_tile_and_exit_1(work):
    """S-247 R-112-04 (criterion 9): with s5 missing the sheet is still written, the exit status is 1, and exactly
    that one tile differs from the full sheet."""
    _, full, _ = _sheet(work, "sheet_full")
    rc, img, err = _sheet(work, "sheet_missing", drop=5)
    assert rc == 1 and img is not None and img.size == full.size and len(_differing(full, img)) == 1, err[-500:]


def test_S_247_a_failed_check_changes_only_its_own_tile(work):
    """S-247 R-112-04 (criterion 9): a layout with a check false (seed 9: 5/6) changes exactly its own tile, and not
    the tile that a missing seed 5 changes."""
    _, full, _ = _sheet(work, "sheet_full")
    _, missing, _ = _sheet(work, "sheet_missing", drop=5)
    _, failed, err = _sheet(work, "sheet_failed", mutate=lambda s, d: d["checks"].__setitem__("bounds", False) if s == 9 else None)
    one, other = _differing(full, failed), _differing(full, missing)
    assert failed is not None and len(one) == 1 and len(other) == 1 and one != other, err[-500:]


# ---- arguments and purity ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("args", [[], ["bogus"], ["map"], ["map", FIXTURE], ["sheet"], ["sheet", FIXTURE.parent], ["map", "a", "b", "c"]],
                         ids=["none", "bogus", "map0", "map1", "sheet0", "sheet1", "map3"])
def test_S_247_bad_arguments_exit_2_with_a_usage_line(args):
    """S-247 R-112-04 (criterion 10): no subcommand, an unknown one, or the wrong number of arguments exits 2 with a
    usage message on stderr."""
    r = run(*args)
    assert (r.returncode, "usage" in r.stderr.lower()) == (2, True)


def test_S_247_render_py_imports_only_pillow_and_the_stdlib_and_never_opens_a_window():
    """S-247 R-112-04 (criteria 8, 10): Python 3 with Pillow and no other import; no tkinter / webbrowser / .show();
    the scale is a module constant DRAFT_PX_WU = 20."""
    assert RENDER.exists(), "scripts/layout/render.py is leaf 3 of the S-247 cascade"
    tree = ast.parse(RENDER.read_text())
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            mods.add(n.module.split(".")[0])
    shows = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "show"]
    consts = {t.id: n.value.value for n in ast.walk(tree) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
              for t in n.targets if isinstance(t, ast.Name)}
    assert all(m in sys.stdlib_module_names or m == "PIL" for m in mods) and not ({"tkinter", "webbrowser"} & mods) \
        and shows == [] and consts.get("DRAFT_PX_WU") == 20
