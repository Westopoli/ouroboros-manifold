"""S-247 renderer (R-112-04): draws an `om-layout-1` JSON (written by csrc/tools/layout_dump) as a flat picture for Westley's rounds.

python3 scripts/layout/render.py map <layout.json> <out.png>      one map, 20 wu a pixel, with a sidebar on the right
python3 scripts/layout/render.py sheet <dir> <out.png>            layout_assault_s1_<sides>.json .. s12 in a 4 by 3 grid

Python 3 and Pillow only; no window is ever opened. Everything is drawn at 2x and reduced once with LANCZOS (anti-aliasing).
Picture y runs downward, as the JSON's y does. Colours, label words and tile sizes are drafts for Westley's eye, not rules.
Spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md criteria 8 to 10. Tests: tests/layout/test_render.py.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DRAFT_PX_WU = 20.0      # DRAFT_PX_WU (spec "Named drafts"): world units per map pixel; Westley owns it
SS = 2                  # supersampling: drawn at 2x, reduced with LANCZOS
SIDEBAR_W = 260         # px; the sidebar's width is the renderer's to choose
LINE_H = 13             # px per sidebar line
SHEET_COLS, SHEET_ROWS, SHEET_SEEDS = 4, 3, 12
SHEET_SHRINK = 2        # a sheet tile is a map at DRAFT_PX_WU * SHEET_SHRINK wu a pixel (assumption, see leaf-03.ASSUMPTIONS.md)
SHEET_MARGIN = SHEET_GUTTER = 12
DEFAULT_CANVAS = 24000.0  # DRAFT_CANVAS_ASSAULT: sizes the empty tiles of a sheet in which no file could be read
DASH_ON, DASH_OFF = 10.0, 7.0   # px of a dashed line (way_round lanes, the vantage's line to its lane)
AXIS_STEP_DEG = 15.0    # choke axis_k is a count of 15-degree steps

GROUND = (238, 234, 224)
SIDE_BG = (250, 250, 247)
INK = (40, 40, 40)
SIDE_COLOUR = {"A": (40, 110, 225), "B": (220, 70, 50), "none": (128, 128, 128)}
GOOD, BAD = (20, 150, 40), (205, 30, 30)
FRAME = (150, 150, 150)
WALL = (110, 100, 95)
VANTAGE = (30, 120, 120)
LANE_COLOUR = {"route": (92, 78, 60), "objective_route": (58, 48, 40), "way_round": (140, 100, 50),
               "climb": (100, 125, 160), "hidden": (175, 170, 165)}
# district role (0 none, 1 home A, 2 home B, 3 near A, 4 near B, 5 contested, 6 objective) -> (tint colour, how much of it)
ROLE_TINT = {1: (SIDE_COLOUR["A"], 0.20), 2: (SIDE_COLOUR["B"], 0.20), 3: (SIDE_COLOUR["A"], 0.09),
             4: (SIDE_COLOUR["B"], 0.09), 5: ((200, 170, 60), 0.14), 6: ((230, 190, 30), 0.22)}
LABEL = {"objective": "objective", "base_home": "keep", "base_forward": "forward camp", "resource": "prize", "expansion": "expansion"}

USAGE = "usage: render.py map <layout.json> <out.png> | render.py sheet <dir> <out.png>"


def font(px):
    try:
        return ImageFont.load_default(size=px * SS)
    except TypeError:       # Pillow without a sized default: the bitmap font
        return ImageFont.load_default()


def mix(c, tint, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(c, tint))


def num(v):
    """A JSON number as short text: integers bare, otherwise up to two decimals."""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        return str(int(v)) if float(v).is_integer() else ("%.2f" % v).rstrip("0").rstrip(".")
    return str(v)


def dist_text(v):
    return "unreachable" if v < 0 else num(v)


# ---- drawing helpers (all coordinates in 2x pixels) -------------------------------------------------------------------
def stroke(draw, pts, w, colour, caps=True):
    """A polyline of width w: a quad per segment, round joints (and round ends when caps)."""
    r = w / 2.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        if d > 0:
            nx, ny = -(y1 - y0) / d * r, (x1 - x0) / d * r
            draw.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=colour)
    joints = pts if caps else pts[1:-1]
    for x, y in joints:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=colour)


def dashes(pts, on, off):
    """The pieces (point lists) of a dash pattern walked along a polyline."""
    out, cur, drawing, left = [], [pts[0]], True, on
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        at = 0.0
        while d - at > left:
            at += left
            p = (x0 + (x1 - x0) * at / d, y0 + (y1 - y0) * at / d)
            if drawing:
                out.append(cur + [p])
                cur = []
            else:
                cur = [p]
            drawing = not drawing
            left = on if drawing else off
        left -= d - at
        if drawing:
            cur.append((x1, y1))
    if drawing and len(cur) > 1:
        out.append(cur)
    return out


def dashed(draw, pts, w, colour, on=DASH_ON * SS, off=DASH_OFF * SS):
    for piece in dashes(pts, on, off):
        stroke(draw, piece, w, colour, caps=False)


def nearest_on(pts, x, y):
    best, at = None, (x, y)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        p = (x0 + dx * t, y0 + dy * t)
        d = math.hypot(p[0] - x, p[1] - y)
        if best is None or d < best:
            best, at = d, p
    return at


def hatched_rect(draw, c, u0, u1, half, ax, ay, colour, step):
    """A rectangle along the axis (ax, ay): u from u0 to u1 along it, half either side across it; outline and diagonal hatching."""
    px, py = -ay, ax

    def at(u, v):
        return (c[0] + ax * u + px * v, c[1] + ay * u + py * v)
    draw.polygon([at(u0, -half), at(u1, -half), at(u1, half), at(u0, half)], fill=mix(GROUND, colour, 0.25))
    s = u0 - 2 * half
    while s < u1:
        v0, v1 = max(-half, u0 - s - half), min(half, u1 - s - half)
        if v0 < v1:
            draw.line([at(s + v0 + half, v0), at(s + v1 + half, v1)], fill=colour, width=SS)
        s += step
    draw.line([at(u0, -half), at(u1, -half), at(u1, half), at(u0, half), at(u0, -half)], fill=colour, width=SS)


def star(cx, cy, outer, inner):
    return [(cx + (outer if i % 2 == 0 else inner) * math.sin(math.pi * i / 5),
             cy - (outer if i % 2 == 0 else inner) * math.cos(math.pi * i / 5)) for i in range(10)]


def marker(draw, kind, cx, cy, colour):
    """The place's shape: base square, objective star, resource diamond, expansion hollow circle (sizes in 1x px)."""
    s = SS
    if kind in ("base_home", "base_forward"):
        draw.rectangle([cx - 7 * s, cy - 7 * s, cx + 7 * s, cy + 7 * s], fill=colour)
    elif kind == "objective":
        draw.polygon(star(cx, cy, 11 * s, 4.5 * s), fill=colour)
    elif kind == "resource":
        draw.polygon([(cx, cy - 8 * s), (cx + 8 * s, cy), (cx, cy + 8 * s), (cx - 8 * s, cy)], fill=colour)
    else:
        draw.ellipse([cx - 7 * s, cy - 7 * s, cx + 7 * s, cy + 7 * s], outline=colour, width=3 * s)


# ---- the map ----------------------------------------------------------------------------------------------------------
def draw_map(doc, wu_per_px, labels=True):
    """The map of one layout at wu_per_px, drawn at 2x: an RGB image of (canvas / wu_per_px * 2) pixels square."""
    m = max(1, round(doc["canvas"] / wu_per_px))
    img = Image.new("RGB", (m * SS, m * SS), GROUND)
    draw = ImageDraw.Draw(img, "RGBA")
    f = font(11)

    def P(x, y):
        return (x / wu_per_px * SS, y / wu_per_px * SS)

    def L(wu):
        return wu / wu_per_px * SS

    def label(text, x, y, anchor="mt"):
        if labels:
            draw.text((x, y), text, fill=INK, font=f, anchor=anchor)

    grid = doc.get("district", [])
    for r, row in enumerate(grid):
        for c, role in enumerate(row):
            if role in ROLE_TINT:
                colour, amount = ROLE_TINT[role]
                draw.rectangle([c * m * SS / len(row), r * m * SS / len(grid), (c + 1) * m * SS / len(row) - 1,
                                (r + 1) * m * SS / len(grid) - 1], fill=mix(GROUND, colour, amount))

    for p in doc.get("places", []):          # the pad each place keeps free, faint, under everything
        cx, cy = P(p["x"], p["y"])
        r = L(p["pad_r"])
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SIDE_COLOUR[p["side"]] + (45,))

    lanes = doc.get("lanes", [])
    for lane in lanes:
        pts = [P(x, y) for x, y in lane["pts"]]
        w, colour = max(SS, L(lane["width"])), LANE_COLOUR.get(lane["kind"], LANE_COLOUR["route"])
        if lane["kind"] == "way_round":
            dashed(draw, pts, w, colour)
        else:
            stroke(draw, pts, w, colour)

    for ch in doc.get("chokes", []):
        cx, cy = P(ch["x"], ch["y"])
        a = math.radians(ch["axis_k"] * AXIS_STEP_DEG)
        ax, ay = math.cos(a), math.sin(a)
        half, gap, span = L(ch["length"]) / 2.0, L(ch["width"]) / 2.0, L(ch["wall_span"])
        for sign in (1, -1):
            c0 = (cx + ax * sign * gap, cy + ay * sign * gap)
            hatched_rect(draw, c0, 0, span, half, ax * sign, ay * sign, WALL, 4 * SS)
        label("choke", cx + 12 * SS, cy - 14 * SS, "lt")

    for v in doc.get("vantages", []):
        cx, cy = P(v["x"], v["y"])
        r = L(v["radius"])
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=VANTAGE, width=SS)
        if 0 <= v.get("overlooks", -1) < len(lanes):
            tx, ty = nearest_on([P(x, y) for x, y in lanes[v["overlooks"]]["pts"]], cx, cy)
            dashed(draw, [(cx, cy), (tx, ty)], SS, VANTAGE, 5 * SS, 4 * SS)
        t = 7 * SS
        draw.polygon([(cx, cy - t), (cx + t, cy + t * 0.7), (cx - t, cy + t * 0.7)], fill=VANTAGE)
        label("height", cx, cy + 9 * SS)

    for p in doc.get("places", []):
        cx, cy = P(p["x"], p["y"])
        marker(draw, p["kind"], cx, cy, SIDE_COLOUR[p["side"]])
        label(LABEL.get(p["kind"], p["kind"]), cx, cy + 13 * SS)
    return img


def sidebar_lines(doc):
    """[(text, colour)] for the sidebar: seed, archetype, sides, distances, checks green or red, then every draft."""
    fair, checks = doc.get("fairness", {}), doc.get("checks", {})
    lines = [("seed " + num(doc["seed"]), INK), ("archetype " + str(doc["archetype"]), INK), ("sides " + str(doc["sides"]), INK),
             ("candidate " + num(doc.get("candidate", 0)), INK), ("canvas " + num(doc["canvas"]) + " wu", INK), ("", INK),
             ("route distance (wu)", INK),
             ("A to objective " + dist_text(fair.get("dist_a_objective", -1)), INK),
             ("B to objective " + dist_text(fair.get("dist_b_objective", -1)), INK)]
    for side, key in (("A", "dist_a_res"), ("B", "dist_b_res")):
        for i, d in enumerate(fair.get(key, [])):
            lines.append(("%s to resource %d %s" % (side, i + 1, dist_text(d)), INK))
    lines += [("", INK), ("checks %d/%d" % (sum(bool(v) for v in checks.values()), len(checks)), INK)]
    lines += [(("%s  ok" if ok else "%s  FAIL") % name, GOOD if ok else BAD) for name, ok in checks.items()]
    lines += [("", INK), ("drafts", INK)] + [("%s  %s" % (k, num(v)), INK) for k, v in doc.get("drafts", {}).items()]
    return lines


def render_map(doc):
    m = round(doc["canvas"] / DRAFT_PX_WU)
    lines = sidebar_lines(doc)
    h = max(m, 2 * 8 + LINE_H * len(lines))
    full = Image.new("RGB", ((m + SIDEBAR_W) * SS, h * SS), SIDE_BG)
    full.paste(draw_map(doc, DRAFT_PX_WU), (0, 0))
    draw, f = ImageDraw.Draw(full), font(11)
    for i, (text, colour) in enumerate(lines):
        draw.text(((m + 10) * SS, (8 + i * LINE_H) * SS), text, fill=colour, font=f)
    return full.resize((m + SIDEBAR_W, h), Image.LANCZOS)


# ---- the sheet --------------------------------------------------------------------------------------------------------
def tile(doc, size, label_text, colour):
    """One sheet tile at 2x: the map (no sidebar) with a caption strip under it, or an empty tile when doc is None."""
    m = size
    cap = max(24, m // 8)
    img = Image.new("RGB", (m * SS, (m + cap) * SS), GROUND)
    draw = ImageDraw.Draw(img)
    if doc is not None:
        img.paste(draw_map(doc, doc["canvas"] / m, labels=False), (0, 0))
    else:
        draw.line([(0, 0), (m * SS, m * SS)], fill=(200, 196, 188), width=SS)
        draw.line([(m * SS, 0), (0, m * SS)], fill=(200, 196, 188), width=SS)
    draw.text((m * SS / 2, (m + cap / 2) * SS), label_text, fill=colour, font=font(11), anchor="mm")
    draw.rectangle([0, 0, m * SS - 1, (m + cap) * SS - 1], outline=FRAME, width=SS)   # one frame colour: a tile's pass or fail shows in its caption only
    return img


def pick_sides(d):
    """The sides mode whose files fill most of the sheet (ties: mirror, rotate, separate)."""
    count = {}
    for p in d.glob("layout_assault_s*_*.json"):
        hit = re.fullmatch(r"layout_assault_s(\d+)_(\w+)\.json", p.name)
        if hit and 1 <= int(hit.group(1)) <= SHEET_SEEDS:
            count[hit.group(2)] = count.get(hit.group(2), 0) + 1
    return max(("mirror", "rotate", "separate"), key=lambda s: count.get(s, 0)) if count else "separate"


def render_sheet(d):
    """(image, ok): the 12 layouts of the directory in a 4 by 3 grid; ok is False when any seed file is missing or unreadable."""
    sides, ok, docs = pick_sides(d), True, {}
    for n in range(1, SHEET_SEEDS + 1):
        path = d / ("layout_assault_s%d_%s.json" % (n, sides))
        try:
            docs[n] = json.loads(path.read_text())
        except (OSError, ValueError) as e:
            docs[n] = None
            ok = False
            print("render.py: s%d %s: %s" % (n, "missing" if isinstance(e, FileNotFoundError) else "unreadable", path), file=sys.stderr)
    first = next((x for x in docs.values() if x), None)
    size = round((first["canvas"] if first else DEFAULT_CANVAS) / (DRAFT_PX_WU * SHEET_SHRINK))
    cap = max(24, size // 8)
    tw, th = size, size + cap
    w = 2 * SHEET_MARGIN + SHEET_COLS * tw + (SHEET_COLS - 1) * SHEET_GUTTER
    h = 2 * SHEET_MARGIN + SHEET_ROWS * th + (SHEET_ROWS - 1) * SHEET_GUTTER
    sheet = Image.new("RGB", (w * SS, h * SS), GROUND)
    for n in range(1, SHEET_SEEDS + 1):
        doc, i = docs[n], n - 1
        if doc is None:
            t = tile(None, size, "s%d  missing" % n, INK)
        else:
            checks = doc.get("checks", {})
            passed = sum(bool(v) for v in checks.values())
            t = tile(doc, size, "s%s  %d/%d" % (num(doc.get("seed", n)), passed, len(checks)), GOOD if passed == len(checks) else BAD)
        x = SHEET_MARGIN + (i % SHEET_COLS) * (tw + SHEET_GUTTER)
        y = SHEET_MARGIN + (i // SHEET_COLS) * (th + SHEET_GUTTER)
        sheet.paste(t, (x * SS, y * SS))
    return sheet.resize((w, h), Image.LANCZOS), ok


# ---- command line (shape of scripts/skilllab/arena/page.py) -------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(prog="render.py", usage=USAGE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("map", usage="render.py map <layout.json> <out.png>")
    one.add_argument("layout")
    one.add_argument("out")
    grid = sub.add_parser("sheet", usage="render.py sheet <dir> <out.png>")
    grid.add_argument("dir")
    grid.add_argument("out")
    args = ap.parse_args(argv)
    if args.cmd == "map":
        try:
            doc = json.loads(Path(args.layout).read_text())
            img = render_map(doc)
        except (OSError, ValueError, KeyError) as e:
            print("render.py: cannot draw %s: %s" % (args.layout, e), file=sys.stderr)
            return 1
        img.save(args.out)
        return 0
    img, ok = render_sheet(Path(args.dir))
    img.save(args.out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
