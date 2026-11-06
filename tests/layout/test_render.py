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
Only what the spec's criteria 8 and 9 pin is asserted; the thresholds below are this file's, loose, and named.
Not checked by any test (Westley's eye, or no spec figure): the label wording, round joints, the hatching pattern, the
dashed line to the overlooked lane, how faint a district tint is, that the place shapes are a star, square, diamond and
hollow circle, and the words on a missing seed's empty tile (the tests only prove it is not a blank box).
Red until scripts/layout/render.py exists. At most 40 assertions in this file (counted by `assert` statements).
"""
import ast
import copy
import json
import math
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
TILE_MIN = 50                      # px: a run of non-background columns or rows narrower than this is not a tile
TONE = 40                          # min green-over-red (or red-over-green) channel gap that reads as a green or red mark
REACH_MIN, REACH_MAX = 40, 90      # px: a wall_span 1200 wu (60 px) or radius 1200 wu (60 px) change reaches this far
SCALE_TOL = 2                      # px: slack on the distance between two places (pad shapes are a few px across)
AA_TONES = 4                       # distinct colours in a 13 x 13 window over a slanted lane edge: ground, lane and 2 blends
CELL_INK = 0.005                   # fraction of a sheet tile that must differ from the sheet's background colour
DASH_TONE = 40                     # min grey-level change that counts as "the lane is here"; the 2x draw and LANCZOS reduction
                                   # leave ringing of a few grey levels past a dash, which a zero threshold reads as solid
                                   # (checked with PIL: dash/gap 6/3, 8/4, 8/6, 10/6 px read dashed at 16..100, solid at 0)
RUN_X = (180, 370)                 # px: the stretch of the dash test's long lane (x 3,600..7,400 wu) clear of every other item
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


def tone_change(a, b, at):
    """Grey-level difference of one pixel between two pictures."""
    return ImageChops.difference(a.crop(at + (at[0] + 1, at[1] + 1)), b.crop(at + (at[0] + 1, at[1] + 1))).convert("L").getpixel((0, 0))


def padded(img, size):
    """img on a canvas of the given size, the extra filled with img's own sidebar background (its most common colour
    right of the map), so a renderer that grows taller for a longer sidebar compares with one that does not."""
    side = img.crop((MAP, 0, img.width, img.height))
    bg = max(side.getcolors(side.width * side.height))[1]
    out = Image.new("RGB", size, bg)
    out.paste(img, (0, 0))
    return out


def sidebar_pair(a, b):
    """a and b padded to the larger of their sizes."""
    size = (max(a.width, b.width), max(a.height, b.height))
    return padded(a, size), padded(b, size)


def mode_colour(img, cx, cy, half=2):
    px = [img.getpixel((x, y)) for x in range(cx - half, cx + half + 1) for y in range(cy - half, cy + half + 1)]
    return max(set(px), key=px.count)


def moved(*indexes):
    def f(doc):
        for index in indexes:
            doc["places"][index]["x"] = doc["places"][index]["y"] = FAR
    return f


def gap(p, q):
    return max(abs(i - j) for i, j in zip(p, q))


def ink(img, other, box):
    """The pixel of img, inside box, where img and other differ most: the core of a thin shape, not its blended edge
    (None when they do not differ there)."""
    at = max(((x, y) for x in range(box[0], box[2]) for y in range(box[1], box[3])),
             key=lambda q: gap(img.getpixel(q), other.getpixel(q)))
    return img.getpixel(at) if img.getpixel(at) != other.getpixel(at) else None


def reach(a, b, cx, cy):
    """Largest distance in px from (cx, cy) to any pixel of the map area where a and b differ (-1 when none)."""
    box = (0, 0, MAP - EDGE, MAP)
    bb = ImageChops.difference(a.crop(box), b.crop(box)).getbbox()
    return -1 if bb is None else max(abs(bb[0] - cx), abs(bb[2] - 1 - cx), abs(bb[1] - cy), abs(bb[3] - 1 - cy))


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


def _swap_sides(doc):
    """Both bases and both expansions change side; kinds, shapes and places stay."""
    for i, side in ((1, "A"), (2, "B"), (5, "B"), (6, "A")):
        doc["places"][i]["side"] = side


def centroid(draw, full, index):
    """Centre in px of a side-coloured fixture place, found by its colour: among the pixels that change when the place is
    moved away, those whose saturation (max channel minus min) is at least half the strongest are the place's own
    colour (ground tints, black or grey label ink and blended edges are paler); their mean position is its centre."""
    p = BASE["places"][index]
    away = draw(f"away{index}", moved(index))
    box = max(boxes(p["x"], p["y"], int(p["pad_r"] / PX_WU) + 2), key=lambda b: changed_pixels(full, away, b))
    px = [((x, y), max(full.getpixel((x, y))) - min(full.getpixel((x, y)))) for x in range(box[0], box[2])
          for y in range(box[1], box[3]) if full.getpixel((x, y)) != away.getpixel((x, y))]
    top = max((s for _, s in px), default=0)
    own = [q for q, s in px if s * 2 >= top]
    return (sum(x for x, _ in own) / len(own), sum(y for _, y in own) / len(own)) if own and top else (math.inf, math.inf)


def test_S_247_places_are_apart_by_their_distance_in_wu_over_20(draw):
    """S-247 R-112-04 (criterion 8: 20 wu per pixel): the centres of the A base and the B expansion, and of the B base
    and the A expansion, are as many pixels apart, horizontally and vertically, as their distance in wu over 20 (within
    SCALE_TOL px; absolute distances, so the y direction is not fixed)."""
    full = draw("full")
    c = {i: centroid(draw, full, i) for i in (1, 2, 5, 6)}       # B base, A base, A expansion, B expansion
    dist = lambda a, b: (abs(a[0] - b[0]), abs(a[1] - b[1]))
    want = lambda i, j: tuple(abs(BASE["places"][i][k] - BASE["places"][j][k]) / PX_WU for k in ("x", "y"))
    assert all(abs(g - w) <= SCALE_TOL for i, j in ((2, 6), (1, 5)) for g, w in zip(dist(c[i], c[j]), want(i, j)))


def test_S_247_side_a_side_b_and_neutral_places_have_their_own_colours(draw):
    """S-247 R-112-04 (criterion 8): colour follows the side, not the kind: swapping the sides of the two bases changes
    both; the two expansions (same kind, A and B) are drawn in different colours and trade them when their sides swap (each
    one's core pixel in the swapped picture is nearer the other's colour in the full one than its own is);
    the neutral resources are grey, differ from both side colours and from the ground under them."""
    full, swap, no_res = draw("full"), draw("swap", _swap_sides), draw("away_res", moved(3, 4))
    ex = [max(boxes(p["x"], p["y"], int(p["pad_r"] / PX_WU) + 2), key=lambda b: changed_pixels(full, swap, b))
          for p in BASE["places"][5:7]]
    c = [(ink(full, swap, b), ink(swap, full, b)) for b in ex]
    bases = [changed_pixels(full, swap, boxes(x, 4000.0, 14)[0]) for x in (1200.0, 6000.0)]
    ca, cb = mode_colour(full, *home(1200.0, 4000.0)), mode_colour(full, *home(6000.0, 4000.0))
    grey = [(mode_colour(full, *home(3000.0, y)), mode_colour(no_res, *home(3000.0, y))) for y in (2400.0, 5600.0)]
    (a_full, a_swap), (b_full, b_swap) = c if None not in c[0] + c[1] else ((ca,) * 2, (ca,) * 2)   # None: fails below
    assert min(bases) > 0 and None not in c[0] + c[1] and gap(a_full, b_full) > 0 \
        and gap(a_full, b_swap) < gap(a_full, b_full) and gap(b_full, a_swap) < gap(b_full, a_full) \
        and all(max(g) - min(g) <= GREY_SPREAD and g != ca and g != cb and g != ground for g, ground in grey) \
        and ca != cb and max(ca) - min(ca) > GREY_SPREAD and max(cb) - min(cb) > GREY_SPREAD


def test_S_247_a_lane_is_a_strip_with_its_width_to_scale(draw):
    """S-247 R-112-04 (criterion 8): a 120 wu lane is a strip about 6 px wide; widening it to 600 wu (30 px) changes
    pixels 10 px either side of its centre line and none 25 px either side."""
    narrow, wide = draw("full"), draw("wide", lambda d: d["lanes"][0].__setitem__("width", 600.0))
    cx, cy = home(2200.0, 4000.0)
    near = [changed_pixels(narrow, wide, (cx, cy + dy, cx + 1, cy + dy + 1)) for dy in (-10, 10)]
    far = [changed_pixels(narrow, wide, (cx, cy + dy, cx + 1, cy + dy + 1)) for dy in (-25, 25)]
    assert near == [1, 1] and far == [0, 0]


def test_S_247_a_way_round_lane_is_dashed_and_a_route_lane_is_solid(draw):
    """S-247 R-112-04 (criterion 8): along the centre row of a long straight lane, the pixels the lane changes are one
    unbroken run for a route and at least two runs with unchanged pixels between them for a way_round (dashed)."""
    def lane2(kind, parked):
        def f(doc):
            doc["lanes"][2]["kind"] = kind
            doc["lanes"][2]["pts"] = [[FAR - 800.0, FAR], [FAR, FAR]] if parked else [[400.0, 3000.0], [7600.0, 3000.0]]
        return f

    def runs(kind):
        on, off = draw(f"{kind}-long", lane2(kind, False)), draw(f"{kind}-parked", lane2(kind, True))
        rows = [home(0.0, 3000.0)[1], MAP - home(0.0, 3000.0)[1]]       # the centre row, picture y-down or y-up
        flags = [[tone_change(on, off, (x, r)) > DASH_TONE for x in range(*RUN_X)] for r in rows]
        f = max(flags, key=sum)
        return sum(1 for i, v in enumerate(f) if v and (i == 0 or not f[i - 1])), f
    (route_runs, route_flags), (dashed_runs, _) = runs("route"), runs("way_round")
    assert route_runs == 1 and all(route_flags) and dashed_runs >= 2


@pytest.mark.parametrize("what,x,y,half", [("chokes", 3500.0, 4000.0, 32), ("vantages", 3600.0, 5000.0, 22)])
def test_S_247_chokes_and_vantages_are_drawn(draw, what, x, y, half):
    """S-247 R-112-04 (criterion 8): a choke (its gap and hatched walls, wall_span 400 wu either side) and a vantage
    (triangle and radius circle, 400 wu) appear at their coordinates: removing the list changes the pixels there."""
    full, gone = draw("full"), draw(f"no_{what}", lambda d: d.__setitem__(what, []))
    assert max(changed_pixels(full, gone, b) for b in boxes(x, y, half)) > 0


@pytest.mark.parametrize("what,key,x,y", [("chokes", "wall_span", 3500.0, 4000.0), ("vantages", "radius", 3600.0, 5000.0)])
def test_S_247_wall_span_and_vantage_radius_are_drawn_to_scale(draw, what, key, x, y):
    """S-247 R-112-04 (criterion 8): tripling a choke's wall_span (400 to 1,200 wu) or a vantage's radius (400 to
    1,200 wu) changes the map out to about 60 px from the choke or vantage (REACH_MIN..REACH_MAX) and no farther."""
    full, big = draw("full"), draw(f"big_{key}", lambda d: d[what][0].__setitem__(key, 1200.0))
    cx, cy = home(x, y)
    assert any(REACH_MIN <= reach(full, big, cx, c) <= REACH_MAX for c in (cy, MAP - cy))


def test_S_247_district_roles_are_faint_tints_and_a_places_kind_changes_its_drawing(draw):
    """S-247 R-112-04 (criterion 8): changing a district's role (near A to near B, the map's corner cell) changes the
    picture in that cell; changing the objective's kind to resource changes the picture at the objective and at no
    other place (the kind drives the drawing; that the shapes are a star, square, diamond and hollow circle is for
    Westley's eye: a different label or colour alone would pass here)."""
    full, tint = draw("full"), draw("tint", lambda d: d["district"][0].__setitem__(0, 4))
    swapped = draw("shape", lambda d: d["places"][0].__setitem__("kind", "resource"))
    cell = [(0, 0, 50, 50), (0, MAP - 50, 50, MAP)]
    obj = max(changed_pixels(full, swapped, b) for b in boxes(4400.0, 4000.0, 14))
    others = [max(changed_pixels(full, swapped, b) for b in boxes(p["x"], p["y"], int(p["pad_r"] / PX_WU) + 2))
              for p in BASE["places"][1:]]
    assert max(changed_pixels(full, tint, b) for b in cell) > 0 and obj > 0 and others == [0] * len(others)


def test_S_247_lane_edges_are_anti_aliased_and_render_py_reduces_with_lanczos(draw):
    """S-247 R-112-04 (criterion 8: "drawn at 2x then reduced with LANCZOS"): the edge of a slanted lane carries blended
    tones (at least AA_TONES colours in a small window over it), and render.py names LANCZOS."""
    img = draw("full")
    px, py = home(2720.0, 3520.0)       # 30 % along the slanted lane from (2600, 4000) to (3000, 2400); no district edge near
    tones = [len({img.getpixel((x, y)) for x in range(px - 6, px + 7) for y in range(y0 - 6, y0 + 7)}) for y0 in (py, MAP - py)]
    names = {n.attr for n in ast.walk(ast.parse(RENDER.read_text())) if isinstance(n, ast.Attribute)} \
        | {n.id for n in ast.walk(ast.parse(RENDER.read_text())) if isinstance(n, ast.Name)}
    assert max(tones) >= AA_TONES and "LANCZOS" in names


def _sidebar_edit(kind):
    def f(doc):
        if kind == "drafts_value":
            doc["drafts"]["DRAFT_EQUAL_TOL"] = 0.35
        elif kind == "drafts_new":
            doc["drafts"]["DRAFT_BRAND_NEW_ONE"] = 7.0
        elif kind == "seed":
            doc["seed"] = 2
        elif kind == "archetype":
            doc["archetype"] = "ambush"
        elif kind == "sides":
            doc["sides"] = "mirror"
        elif kind == "check":
            doc["checks"]["bounds"] = False
        elif kind == "fairness":
            doc["fairness"]["dist_a_objective"] = 3999.0
        elif kind == "dist_b_objective":
            doc["fairness"]["dist_b_objective"] = 2222.0
        elif kind == "dist_a_res":
            doc["fairness"]["dist_a_res"] = [4321.0, 1940.0]
        elif kind == "dist_b_res":
            doc["fairness"]["dist_b_res"] = [3520.0, 777.0]
    return f


@pytest.mark.parametrize("kind", ["drafts_value", "drafts_new", "seed", "archetype", "sides", "check", "fairness",
                                  "dist_b_objective", "dist_a_res", "dist_b_res"])
def test_S_247_the_sidebar_shows_the_drafts_seed_checks_and_distances(draw, kind):
    """S-247 R-112-04 (criterion 8): changing a drafts value, adding a draft, the seed, the archetype, the sides mode, a
    check result or any one of the route distances in the JSON changes the sidebar (right of the map) and leaves the
    map itself untouched."""
    a, b = sidebar_pair(draw("full"), draw(f"side_{kind}", _sidebar_edit(kind)))
    side = changed_pixels(a, b, (MAP, 0, a.width, a.height))
    mapped = changed_pixels(a, b, (0, 0, MAP - EDGE, MAP))
    assert (side > 0, mapped) == (True, 0)


def test_S_247_a_passing_check_is_green_and_a_failing_one_red(draw):
    """S-247 R-112-04 (criterion 8: "each check green or red"): among the sidebar pixels that change when one check
    goes from true to false, the passing picture's are green-dominant and the failing picture's red-dominant."""
    ok, bad = sidebar_pair(draw("full"), draw("side_check", _sidebar_edit("check")))
    box = (MAP, 0, ok.width, ok.height)

    def tones(a, b):
        px = [a.getpixel((x, y)) for x in range(box[0], box[2]) for y in range(box[1], box[3])
              if a.getpixel((x, y)) != b.getpixel((x, y))]
        return sum(1 for r, g, _ in px if g - r > TONE), sum(1 for r, g, _ in px if r - g > TONE)
    (ok_green, ok_red), (bad_green, bad_red) = tones(ok, bad), tones(bad, ok)
    assert ok_green > ok_red and bad_red > bad_green


# ---- the sheet --------------------------------------------------------------------------------------------------------
def _sheet(work, name, mutate=None, drop=None, sides="separate"):
    """12 fixture copies with seeds 1..12 in work/name/ as layout_assault_s<N>_<sides>.json, run `sheet`, return
    (returncode, image, stderr)."""
    d = work / name
    d.mkdir(exist_ok=True)
    for s in range(1, 13):
        doc = copy.deepcopy(BASE)
        doc["seed"], doc["sides"] = s, sides
        if mutate:
            mutate(s, doc)
        if s != drop:
            (d / f"layout_assault_s{s}_{sides}.json").write_text(json.dumps(doc))
    out = work / f"{name}.png"
    r = run("sheet", d, out)
    return r.returncode, (Image.open(out).convert("RGB") if out.is_file() else None), r.stderr


def _runs(flags):
    """(start, end) of each stretch of True in flags that is at least TILE_MIN long."""
    out, start = [], None
    for i, f in enumerate(flags + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= TILE_MIN:
                out.append((start, i))
            start = None
    return out


def _boxes(img):
    """The 12 tile boxes, row-major. Located by the non-background content of the sheet: 4 column stretches and the last
    3 row stretches (a title strip above is allowed), whatever the margins and gutters. A sheet whose tiles touch has no
    gap to find; it falls back to the equal 4 x 3 split of the image, which is then exactly right."""
    bg = max(img.getcolors(img.width * img.height))[1]
    ink_ = ImageChops.difference(img, Image.new("RGB", img.size, bg)).convert("L").point(lambda v: 255 if v else 0)
    cols = _runs([ink_.crop((x, 0, x + 1, img.height)).getbbox() is not None for x in range(img.width)])
    rows = _runs([ink_.crop((0, y, img.width, y + 1)).getbbox() is not None for y in range(img.height)])
    if len(cols) == SHEET_COLS and len(rows) >= SHEET_ROWS:
        return [(c0, r0, c1, r1) for r0, r1 in rows[-SHEET_ROWS:] for c0, c1 in cols]
    cw, ch = img.width // SHEET_COLS, img.height // SHEET_ROWS
    return [(c * cw, r * ch, (c + 1) * cw, (r + 1) * ch) for r in range(SHEET_ROWS) for c in range(SHEET_COLS)]


def _cells(img, boxes=None):
    return [img.crop(b) for b in (boxes or _boxes(img))]


def _differing(a, b):
    """Indexes of the tiles (located in a) in which b differs from a, and any change outside every tile counts as one
    more entry, -1."""
    boxes = _boxes(a)
    hit = [i for i, (x, y) in enumerate(zip(_cells(a, boxes), _cells(b, boxes))) if ImageChops.difference(x, y).getbbox()]
    outside = ImageChops.difference(a, b)
    for box in boxes:
        outside.paste((0, 0, 0), box)
    return hit + ([-1] if outside.getbbox() else [])


def _inked(img):
    """Fraction of each cell that is not the sheet's most common colour (its background)."""
    bg = max(img.getcolors(img.width * img.height))[1]
    return [sum(n for n, c in cell.getcolors(cell.width * cell.height) if c != bg) / (cell.width * cell.height)
            for cell in _cells(img)]


def test_S_247_the_sheet_has_twelve_tiles_in_a_4_by_3_grid(work):
    """S-247 R-112-04 (criterion 9): 12 fixtures s1..s12 in a directory give exit 0 and one image wider than tall
    whose 4 x 3 cells (equal split of the image) each hold drawn content (not just background) and all differ (each
    tile carries its own seed number); the same holds for the files named with another sides mode."""
    rc, img, err = _sheet(work, "sheet_full")
    rc2, img2, _ = _sheet(work, "sheet_mirror", sides="mirror")
    cells = _cells(img) if img else []
    assert rc == 0 and rc2 == 0 and img is not None and img2 is not None and img.width > img.height and len(cells) == 12 \
        and min(_inked(img)) >= CELL_INK and min(_inked(img2)) >= CELL_INK \
        and len({c.tobytes() for c in cells}) == 12, err[-500:]


def test_S_247_each_tile_holds_its_own_map(work):
    """S-247 R-112-04 (criterion 9: each tile a map without the sidebar): widening one lane of seed 3's layout changes
    exactly one tile, and inside it only above the lowest tenth (the caption strip under the map is not touched)."""
    _, full, _ = _sheet(work, "sheet_full")
    _, wide, err = _sheet(work, "sheet_wide", mutate=lambda s, d: d["lanes"][0].__setitem__("width", 600.0) if s == 3 else None)
    one = _differing(full, wide)
    tile = _boxes(full)[one[0]] if len(one) == 1 and one[0] >= 0 else None
    box = ImageChops.difference(full.crop(tile), wide.crop(tile)).getbbox() if tile else None
    assert wide is not None and tile is not None and box is not None and box[3] <= (tile[3] - tile[1]) * 0.9, err[-500:]


def test_S_247_a_missing_seed_leaves_one_labelled_empty_tile_and_exit_1(work):
    """S-247 R-112-04 (criterion 9): with s5 missing the sheet is still written, the exit status is 1, exactly that one
    tile differs from the full sheet and it is not blank (it carries a label)."""
    _, full, _ = _sheet(work, "sheet_full")
    rc, img, err = _sheet(work, "sheet_missing", drop=5)
    gone = _differing(full, img) if img else []
    cell = img.crop(_boxes(full)[gone[0]]) if len(gone) == 1 and gone[0] >= 0 else None
    assert rc == 1 and img is not None and img.size == full.size and len(gone) == 1 \
        and cell is not None and len(cell.getcolors(cell.width * cell.height)) > 1, err[-500:]


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
    consts.update({n.target.id: n.value.value for n in ast.walk(tree) if isinstance(n, ast.AnnAssign)
                   and isinstance(n.target, ast.Name) and isinstance(n.value, ast.Constant)})   # DRAFT_PX_WU: float = 20.0
    assert all(m in sys.stdlib_module_names or m == "PIL" for m in mods) and not ({"tkinter", "webbrowser"} & mods) \
        and shows == [] and consts.get("DRAFT_PX_WU") == 20
