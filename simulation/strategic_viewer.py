#!/usr/bin/env python3
"""
Strategic viewer — replay a strategic sim dump produced by run_strategic_viewer.py.

Usage: python3 strategic_viewer.py <dump.jsonl>

Controls:
  Space       play/pause
  ← / →       step one tick
  Home / End  jump to start/end
  [ / ]       speed down/up
  R           reset camera
  V           toggle radar overlay
  F           toggle faction track mode  (Checkpoint 7)
  ESC         quit

  Mouse pan, scroll-wheel zoom, click-to-pick region
"""

import sys
import os
import json
import math

try:
    import pygame
except ImportError:
    print("strategic_viewer requires pygame: pip install pygame", file=sys.stderr)
    sys.exit(1)

_ft = None
_has_freetype = False

try:
    from PIL import Image as _PILImage, ImageDraw as _PILDraw, ImageFont as _PILFont
    _has_pil = True
except ImportError:
    _has_pil = False

try:
    import networkx as nx
    _has_nx = True
except ImportError:
    _has_nx = False

# ── Layout ────────────────────────────────────────────────────────────────────

WINDOW_W    = 1400
WINDOW_H    = 900
SIDEBAR_W   = 320
CONTROLS_H  = 50
EVENT_LOG_H = 120
MAP_W       = WINDOW_W - SIDEBAR_W
MAP_H       = WINDOW_H - CONTROLS_H - EVENT_LOG_H

BG_COLOR        = (13, 13, 18)
CONTROLS_BG     = (22, 22, 30)
SIDEBAR_BG      = (18, 18, 26)
SIDEBAR_BORDER  = (45, 45, 60)
SCRUBBER_BG     = (50, 50, 65)
SCRUBBER_FG     = (90, 130, 210)
SCRUBBER_H      = 10
SCRUBBER_PAD_X  = 12
TEXT_COLOR      = (175, 175, 188)
DIM_COLOR       = (90, 90, 105)
SELECTED_COLOR  = (255, 215, 50)
UNOWNED_COLOR   = (70, 70, 85)
EDGE_COLOR      = (55, 55, 72)
EVENT_LOG_BG    = (16, 16, 24)
EVENT_LOG_BORDER = (40, 40, 55)
EVENT_HOVER_BG  = (35, 35, 50)

NODE_R_MIN  = 18
NODE_R_MAX  = 42
ZOOM_STEP   = 1.15
ZOOM_MIN    = 0.1
ZOOM_MAX    = 15.0
SPEEDS      = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
DEFAULT_SPEED_IDX = 2
TICK_DURATION = 0.12   # seconds per tick at 1x speed


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ── Dump loading ──────────────────────────────────────────────────────────────

def load_dump(path):
    header = None
    ticks  = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj["type"] == "header":
                header = obj
            elif obj["type"] == "tick":
                ticks.append(obj)
    if header is None:
        print("ERROR: no header in dump", file=sys.stderr)
        sys.exit(1)
    if not ticks:
        print("ERROR: no tick lines in dump", file=sys.stderr)
        sys.exit(1)
    return header, ticks


# ── Auto-layout ───────────────────────────────────────────────────────────────

def compute_layout(header):
    """Return {region_id: (x, y)} in world-space [0..1000, 0..1000]."""
    region_ids = [r["id"] for r in header["regions"]]

    # Use hand-authored coords if all present
    if all(r.get("layout") for r in header["regions"]):
        return {r["id"]: tuple(r["layout"]) for r in header["regions"]}

    if _has_nx:
        G = nx.Graph()
        G.add_nodes_from(region_ids)
        for a, b, _ in header["adjacency"]:
            G.add_edge(a, b)
        pos = nx.spring_layout(G, seed=42, k=2.0 / max(1, math.sqrt(len(region_ids))))
        # spring_layout returns coords in [-1, 1]; remap to [50, 950]
        return {rid: (
            (pos[rid][0] + 1) / 2 * 900 + 50,
            (pos[rid][1] + 1) / 2 * 900 + 50,
        ) for rid in region_ids}

    # Fallback: circle layout
    n = len(region_ids)
    return {rid: (
        500 + 400 * math.cos(2 * math.pi * i / max(n, 1)),
        500 + 400 * math.sin(2 * math.pi * i / max(n, 1)),
    ) for i, rid in enumerate(region_ids)}


# ── Camera ────────────────────────────────────────────────────────────────────

def world_to_screen(wx, wy, cam_x, cam_y, zoom):
    sx = (wx - cam_x) * zoom + MAP_W / 2
    sy = (wy - cam_y) * zoom + MAP_H / 2
    return int(sx), int(sy)


def screen_to_world(sx, sy, cam_x, cam_y, zoom):
    wx = (sx - MAP_W / 2) / zoom + cam_x
    wy = (sy - MAP_H / 2) / zoom + cam_y
    return wx, wy


def zoom_toward(cam_x, cam_y, zoom, sx, sy, factor):
    wx, wy = screen_to_world(sx, sy, cam_x, cam_y, zoom)
    new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom * factor))
    new_cam_x = wx - (sx - MAP_W / 2) / new_zoom
    new_cam_y = wy - (sy - MAP_H / 2) / new_zoom
    return new_cam_x, new_cam_y, new_zoom


def default_camera(layout):
    xs = [p[0] for p in layout.values()]
    ys = [p[1] for p in layout.values()]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1)
    zoom = min(MAP_W, MAP_H) * 0.75 / span
    return cx, cy, zoom


# ── Node geometry ─────────────────────────────────────────────────────────────

def node_radius(composites):
    cap = composites.get("capacity", 0)
    t = max(0.0, min(1.0, cap / 100.0))
    return NODE_R_MIN + int((NODE_R_MAX - NODE_R_MIN) * t)


def node_fill_color(faction_color_rgb, composites):
    """Dim faction color by stability."""
    stab = composites.get("stability", 0)
    t = max(0.0, min(1.0, stab / 100.0))
    dark = (15, 15, 22)
    return lerp_color(dark, faction_color_rgb, 0.25 + 0.75 * t)


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_edge(surface, pos_a, pos_b, a_id, b_id, friction, cam_x, cam_y, zoom):
    sx1, sy1 = world_to_screen(*pos_a, cam_x, cam_y, zoom)
    sx2, sy2 = world_to_screen(*pos_b, cam_x, cam_y, zoom)
    f_a = friction.get(a_id, {}).get("tension", 0)
    f_b = friction.get(b_id, {}).get("tension", 0)
    f   = max(f_a, f_b)
    if f > 0:
        # normalize: BORDER_FRICTION_TENSION is ~0.3/tick; clamp at 2.0 for full red
        t     = min(1.0, f / 2.0)
        color = (int(55 + 200 * t), int(55 * (1 - t)), int(72 * (1 - t)))
        width = max(1, int(1 + 3 * t))
    else:
        color = EDGE_COLOR
        width = 1
    pygame.draw.line(surface, color, (sx1, sy1), (sx2, sy2), width)


def draw_node(surface, rid, pos, tick_data, faction_colors, selected_rid, cam_x, cam_y, zoom,
              event_rids=None):
    rdata = tick_data["regions"].get(rid, {})
    fid   = rdata.get("faction_id")
    comp  = rdata.get("composites", {})
    fields = rdata.get("fields", {})

    base_color = faction_colors.get(fid, UNOWNED_COLOR)
    fill       = node_fill_color(base_color, comp)
    r          = node_radius(comp)

    sx, sy = world_to_screen(*pos, cam_x, cam_y, zoom)
    r_px   = max(6, int(r * zoom))

    pygame.draw.circle(surface, fill,       (sx, sy), r_px)
    pygame.draw.circle(surface, base_color, (sx, sy), r_px, 2)

    # Tension inner ring
    tension = fields.get("tension", 0)
    if tension > 5:
        ring_t = int(max(1, min(5, tension / 20.0)))
        alpha  = int(80 + 175 * tension / 100)
        inner_r = max(3, r_px - ring_t - 2)
        ring_surf = pygame.Surface((r_px * 2 + 4, r_px * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (220, 60, 60, alpha),
                           (r_px + 2, r_px + 2), inner_r, ring_t)
        surface.blit(ring_surf, (sx - r_px - 2, sy - r_px - 2))

    if event_rids and rid in event_rids:
        pulse_surf = pygame.Surface((r_px * 2 + 16, r_px * 2 + 16), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surf, (255, 240, 100, 160),
                           (r_px + 8, r_px + 8), r_px + 6, 3)
        surface.blit(pulse_surf, (sx - r_px - 8, sy - r_px - 8))

    if rid == selected_rid:
        pygame.draw.circle(surface, SELECTED_COLOR, (sx, sy), r_px + 4, 2)


def draw_radar(surface, rid, pos, tick_data, cam_x, cam_y, zoom):
    """4-arm star: military(up), economy(right), population(down), tension(left)."""
    rdata  = tick_data["regions"].get(rid, {})
    fields = rdata.get("fields", {})
    if not fields:
        return

    sx, sy = world_to_screen(*pos, cam_x, cam_y, zoom)
    r_base = max(6, int(NODE_R_MAX * zoom))

    arms = [
        ("military",   0,    (100, 160, 255)),
        ("economy",    90,   (80,  210, 120)),
        ("population", 180,  (200, 180, 80)),
        ("tension",    270,  (220, 80,  80)),
    ]

    for field, deg, color in arms:
        val = fields.get(field, 0) / 100.0
        length = int(r_base * val)
        if length < 2:
            continue
        angle = math.radians(deg - 90)
        ex = sx + int(length * math.cos(angle))
        ey = sy + int(length * math.sin(angle))
        pygame.draw.line(surface, color, (sx, sy), (ex, ey), max(1, int(2 * zoom)))


def draw_region_label(surface, font, rid, name, pos, cam_x, cam_y, zoom):
    sx, sy = world_to_screen(*pos, cam_x, cam_y, zoom)
    char_w = 7
    tw = len(name) * char_w
    render_text(surface, font, name, (sx - tw // 2, sy + max(6, int(NODE_R_MAX * zoom)) + 4))


# ── Map ───────────────────────────────────────────────────────────────────────

def draw_map(surface, tick_data, header, layout, faction_colors,
             cam_x, cam_y, zoom, selected_rid, radar_on, font):
    surface.fill(BG_COLOR)

    friction   = tick_data.get("friction", {})
    event_rids = {e["region_id"] for e in tick_data.get("events", []) if e.get("region_id")}

    # Edges first
    for a_id, b_id, _ in header["adjacency"]:
        if a_id in layout and b_id in layout:
            draw_edge(surface, layout[a_id], layout[b_id], a_id, b_id, friction, cam_x, cam_y, zoom)

    # Nodes
    for r in header["regions"]:
        rid = r["id"]
        if rid not in layout:
            continue
        draw_node(surface, rid, layout[rid], tick_data, faction_colors,
                  selected_rid, cam_x, cam_y, zoom, event_rids=event_rids)
        if radar_on:
            draw_radar(surface, rid, layout[rid], tick_data, cam_x, cam_y, zoom)

    # Labels
    for r in header["regions"]:
        rid = r["id"]
        if rid in layout:
            draw_region_label(surface, font, rid, r["name"], layout[rid],
                              cam_x, cam_y, zoom)


# ── Controls strip ────────────────────────────────────────────────────────────

def draw_event_log(surface, font, event_index, current_idx, region_names, hover_row):
    """Draw the event log panel. Returns list of (y0, y1, event_index_pos) for click detection."""
    ey = MAP_H
    pygame.draw.rect(surface, EVENT_LOG_BG, (0, ey, MAP_W, EVENT_LOG_H))
    pygame.draw.line(surface, EVENT_LOG_BORDER, (0, ey), (MAP_W, ey))

    # Collect events up to current tick, most recent first
    visible = [(i, t, rid, etype)
               for i, t, rid, etype in event_index
               if i <= current_idx][-10:]
    visible = list(reversed(visible))

    pad = 10
    lh  = 16
    y   = ey + 6
    rows = []
    for pos, (tick_idx, tick_num, rid, etype) in enumerate(visible):
        rname = region_names.get(rid, rid)
        text  = f"t{tick_num:>4}  {rname:<18}  {etype}"
        if pos == hover_row:
            pygame.draw.rect(surface, EVENT_HOVER_BG, (0, y - 2, MAP_W, lh + 2))
        render_text(surface, font, text, (pad, y), DIM_COLOR if pos > 0 else TEXT_COLOR)
        rows.append((y - 2, y + lh, tick_idx, rid))
        y += lh

    return rows


def draw_controls(surface, font, current_idx, total, playing, speed_idx, tick_num, radar_on):
    cy = MAP_H + EVENT_LOG_H
    pygame.draw.rect(surface, CONTROLS_BG, (0, cy, WINDOW_W, CONTROLS_H))

    bx = SCRUBBER_PAD_X
    by = cy + 6
    bw = WINDOW_W - SCRUBBER_PAD_X * 2
    pygame.draw.rect(surface, SCRUBBER_BG, (bx, by, bw, SCRUBBER_H), border_radius=4)
    if total > 1:
        fill_w = int(bw * current_idx / (total - 1))
        if fill_w > 0:
            pygame.draw.rect(surface, SCRUBBER_FG, (bx, by, fill_w, SCRUBBER_H), border_radius=4)
    thumb_x = bx + int(bw * current_idx / max(total - 1, 1))
    pygame.draw.circle(surface, (190, 215, 255), (thumb_x, by + SCRUBBER_H // 2), 7)

    state = ">" if playing else "||"
    speed = f"{SPEEDS[speed_idx]:g}x"
    radar = "ON" if radar_on else "off"
    hint  = (f"{state}  tick {tick_num} / {total - 1}  |  {speed}  |  "
             f"radar[V]:{radar}   Space play  ←→ step  [/] speed  F faction  Tab cycle  R reset  ESC quit")
    render_text(surface, font, hint, (bx, cy + 26))


# ── Sidebar ───────────────────────────────────────────────────────────────────

def draw_sparkline(surface, ticks, current_idx, rid, field, x, y, w, h, color):
    window = ticks[max(0, current_idx - 59): current_idx + 1]
    vals = [t["regions"].get(rid, {}).get("fields", {}).get(field, 0) for t in window]
    if len(vals) < 2:
        return
    lo, hi = min(vals), max(vals)
    span = hi - lo if hi != lo else 1.0
    pts = [
        (x + int(i * w / (len(vals) - 1)),
         y + h - int((v - lo) / span * h))
        for i, v in enumerate(vals)
    ]
    pygame.draw.lines(surface, color, False, pts, 1)


def draw_faction_sidebar(surface, font, tick_data, ticks, current_idx,
                         tracked_fid, faction_colors, faction_names, faction_ids):
    pygame.draw.rect(surface, SIDEBAR_BG, (0, 0, SIDEBAR_W, MAP_H))
    pygame.draw.line(surface, SIDEBAR_BORDER, (0, 0), (0, MAP_H))

    pad = 12
    x   = pad
    y   = 16
    lh  = 18
    bh  = 10
    bw  = SIDEBAR_W - pad * 2

    def line(text, color=TEXT_COLOR):
        nonlocal y
        render_text(surface, font, text, (x, y), color)
        y += lh

    def bar(value, max_val, color):
        nonlocal y
        fill = int(bw * max(0, min(value, max_val)) / max(max_val, 1))
        pygame.draw.rect(surface, (40, 40, 55), (x, y, bw, bh), border_radius=3)
        if fill > 0:
            pygame.draw.rect(surface, color, (x, y, fill, bh), border_radius=3)
        y += bh + 4

    def gap(px=6):
        nonlocal y
        y += px

    if not tracked_fid:
        line("no factions in this scenario", DIM_COLOR)
        return

    fcolor = faction_colors.get(tracked_fid, TEXT_COLOR)
    fname  = faction_names.get(tracked_fid, tracked_fid)
    fdata  = tick_data["factions"].get(tracked_fid, {})

    line(f"[F] Faction view  Tab to cycle", DIM_COLOR)
    gap(4)
    line(fname, fcolor)

    idx_str = f"{faction_ids.index(tracked_fid) + 1}/{len(faction_ids)}" if tracked_fid in faction_ids else ""
    line(f"Archetype: {tracked_fid}  {idx_str}", DIM_COLOR)
    gap()

    line(f"Regions: {fdata.get('region_count', 0)}")
    line(f"Tech:    {fdata.get('tech_level', 0):.3f}")
    line(f"Budget:  {fdata.get('budget', 0):.1f}")
    gap()

    totals = fdata.get("totals", {})
    max_total = 100 * max(fdata.get("region_count", 1), 1)
    for field, color in (("military", (100, 160, 255)),
                         ("economy",  (80, 210, 120)),
                         ("population", (200, 180, 80))):
        val = totals.get(field, 0)
        line(f"{field.capitalize():<12} {val:6.1f}", color)
        bar(val, max_total, color)

    gap()
    line("── Tech sparkline ──", DIM_COLOR)
    tech_vals = [t["factions"].get(tracked_fid, {}).get("tech_level", 0)
                 for t in ticks[max(0, current_idx - 59): current_idx + 1]]
    if len(tech_vals) >= 2:
        lo, hi = min(tech_vals), max(tech_vals)
        span = hi - lo if hi != lo else 1.0
        sh = 30
        pts = [(x + int(i * bw / (len(tech_vals) - 1)),
                y + sh - int((v - lo) / span * sh))
               for i, v in enumerate(tech_vals)]
        pygame.draw.lines(surface, (100, 200, 160), False, pts, 1)
        line(f"  {lo:.3f} → {hi:.3f}", DIM_COLOR)
        y += sh + 4
    else:
        y += lh

    gap()
    line("── Diplomacy ──", DIM_COLOR)
    stances = fdata.get("stances", {})
    if stances:
        for other_fid, stance in stances.items():
            color = (220, 80, 80) if stance == "hostile" else (80, 210, 120) if stance == "cooperative" else DIM_COLOR
            line(f"  {faction_names.get(other_fid, other_fid):<16} {stance}", color)
    else:
        line("  no diplomatic stances", DIM_COLOR)


def draw_sidebar(surface, font, tick_data, header, selected_rid, faction_colors, faction_names,
                 ticks=None, current_idx=0):
    pygame.draw.rect(surface, SIDEBAR_BG, (0, 0, SIDEBAR_W, MAP_H))
    pygame.draw.line(surface, SIDEBAR_BORDER, (0, 0), (0, MAP_H))

    pad  = 12
    x    = pad
    y    = 16
    lh   = 18   # line height
    bh   = 10   # bar height
    bw   = SIDEBAR_W - pad * 2

    def line(text, color=TEXT_COLOR, indent=0):
        nonlocal y
        render_text(surface, font, text, (x + indent, y), color)
        y += lh

    def bar(value, max_val=100, color=(90, 130, 200)):
        nonlocal y
        fill = int(bw * max(0, min(value, max_val)) / max_val)
        pygame.draw.rect(surface, (40, 40, 55), (x, y, bw, bh), border_radius=3)
        if fill > 0:
            pygame.draw.rect(surface, color, (x, y, fill, bh), border_radius=3)
        y += bh + 4

    def gap(px=6):
        nonlocal y
        y += px

    def sparkline(field, color):
        nonlocal y
        if ticks:
            draw_sparkline(surface, ticks, current_idx, selected_rid, field, x, y, bw, 24, color)
        y += 28

    if selected_rid is None:
        line("click a region to inspect", DIM_COLOR)
        return

    rdata  = tick_data["regions"].get(selected_rid)
    if rdata is None:
        line(f"{selected_rid} — no data", DIM_COLOR)
        return

    # Region header
    region_meta = next((r for r in header["regions"] if r["id"] == selected_rid), {})
    fid    = rdata.get("faction_id")
    fname  = faction_names.get(fid, "Unclaimed") if fid else "Unclaimed"
    fcolor = faction_colors.get(fid, TEXT_COLOR)

    line(region_meta.get("name", selected_rid), (230, 230, 245))
    line(f"Tier: {region_meta.get('tier', '?')}   Owner: {fname}", fcolor)
    gap()

    fields   = rdata.get("fields", {})
    composites = rdata.get("composites", {})

    FIELD_COLORS = {
        "military":   (100, 160, 255),
        "economy":    (80,  210, 120),
        "tension":    (220, 80,  80),
        "population": (200, 180, 80),
    }

    for field in ("military", "economy", "tension", "population"):
        val = fields.get(field, 0)
        line(f"{field.capitalize():12s} {val:5.1f}", FIELD_COLORS[field])
        bar(val, color=FIELD_COLORS[field])
        sparkline(field, FIELD_COLORS[field])

    gap()
    line("── Composites ──", DIM_COLOR)
    for comp in ("stability", "capacity"):
        val = composites.get(comp, 0)
        line(f"{comp.capitalize():12s} {val:5.1f}")
        bar(val)

    gap()
    # Faction tech
    if fid:
        fdata = tick_data["factions"].get(fid, {})
        tech  = fdata.get("tech_level", 0)
        line(f"Faction tech:  {tech:.3f}", DIM_COLOR)


# ── Region picking ────────────────────────────────────────────────────────────

def pick_region(layout, tick_data, click_sx, click_sy, cam_x, cam_y, zoom):
    best_rid  = None
    best_dist = 1e9
    for rid, pos in layout.items():
        rdata = tick_data["regions"].get(rid, {})
        comp  = rdata.get("composites", {})
        r_px  = max(6, int(node_radius(comp) * zoom))
        sx, sy = world_to_screen(*pos, cam_x, cam_y, zoom)
        d = math.hypot(click_sx - sx, click_sy - sy)
        if d <= r_px + 4 and d < best_dist:
            best_dist = d
            best_rid  = rid
    return best_rid


def render_text(surface, font, text, pos, color=TEXT_COLOR):
    if font == "pil" and _has_pil:
        w = max(10, len(text) * 7 + 8)
        img = _PILImage.new("RGBA", (w, 16), (0, 0, 0, 0))
        _PILDraw.Draw(img).text((2, 2), text, fill=(*color, 255))
        surface.blit(pygame.image.fromstring(img.tobytes(), img.size, "RGBA"), pos)
    elif font is not None:
        font.render_to(surface, pos, text, color)


def tick_from_scrubber_x(mx, total):
    bx = SCRUBBER_PAD_X
    bw = WINDOW_W - SCRUBBER_PAD_X * 2
    frac = max(0.0, min(1.0, (mx - bx) / bw))
    return int(frac * (total - 1))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 strategic_viewer.py <dump.jsonl>", file=sys.stderr)
        sys.exit(1)

    header, ticks = load_dump(sys.argv[1])
    scenario = header.get("scenario", os.path.basename(sys.argv[1]))

    faction_colors = {
        fid: hex_to_rgb(info["color"])
        for fid, info in header.get("factions", {}).items()
    }
    faction_names = {
        fid: info["name"]
        for fid, info in header.get("factions", {}).items()
    }

    layout = compute_layout(header)
    region_names = {r["id"]: r["name"] for r in header["regions"]}

    # Build flat event index: [(tick_idx, tick_num, region_id, event_type), ...]
    event_index = []
    for i, tick in enumerate(ticks):
        for evt in tick.get("events", []):
            if evt.get("region_id"):
                event_index.append((i, tick["tick"], evt["region_id"], evt["type"]))

    pygame.init()

    font = "pil" if _has_pil else None

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(
        f"strategic_viewer — {scenario}  |  {len(ticks)} ticks  |  "
        f"{len(header['regions'])} regions"
    )
    clock = pygame.time.Clock()

    map_surf     = pygame.Surface((MAP_W, MAP_H))
    sidebar_surf = pygame.Surface((SIDEBAR_W, MAP_H))

    cam_x, cam_y, zoom = default_camera(layout)
    default_cam = (cam_x, cam_y, zoom)

    current_idx  = 0
    playing      = False
    speed_idx    = DEFAULT_SPEED_IDX
    accum        = 0.0
    total        = len(ticks)
    radar_on       = False
    selected_rid   = None
    scrubbing      = False
    panning        = False
    pan_last       = (0, 0)
    drag_moved     = False
    hover_row      = -1
    event_log_rows = []   # filled each frame by draw_event_log
    faction_mode   = False
    faction_ids    = sorted(faction_colors.keys())
    tracked_fid    = faction_ids[0] if faction_ids else None

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                    accum = 0.0
                elif event.key == pygame.K_RIGHT:
                    playing = False
                    current_idx = min(total - 1, current_idx + 1)
                elif event.key == pygame.K_LEFT:
                    playing = False
                    current_idx = max(0, current_idx - 1)
                elif event.key == pygame.K_HOME:
                    playing = False
                    current_idx = 0
                elif event.key == pygame.K_END:
                    playing = False
                    current_idx = total - 1
                elif event.key == pygame.K_RIGHTBRACKET:
                    speed_idx = min(len(SPEEDS) - 1, speed_idx + 1)
                elif event.key == pygame.K_LEFTBRACKET:
                    speed_idx = max(0, speed_idx - 1)
                elif event.key == pygame.K_r:
                    cam_x, cam_y, zoom = default_cam
                elif event.key == pygame.K_v:
                    radar_on = not radar_on
                elif event.key == pygame.K_f:
                    faction_mode = not faction_mode
                    if faction_mode and selected_rid:
                        fid = ticks[current_idx]["regions"].get(selected_rid, {}).get("faction_id")
                        if fid and fid in faction_ids:
                            tracked_fid = fid
                elif event.key == pygame.K_TAB and faction_mode and faction_ids:
                    idx = faction_ids.index(tracked_fid) if tracked_fid in faction_ids else 0
                    tracked_fid = faction_ids[(idx + 1) % len(faction_ids)]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if my >= MAP_H + EVENT_LOG_H and my < MAP_H + EVENT_LOG_H + CONTROLS_H:
                    scrubbing = True
                    playing = False
                    current_idx = tick_from_scrubber_x(mx, total)
                elif mx < MAP_W and my < MAP_H and event.button == 1:
                    panning = True
                    drag_moved = False
                    pan_last = (mx, my)
                elif event.button == 3:
                    selected_rid = None

            elif event.type == pygame.MOUSEBUTTONUP:
                scrubbing = False
                if event.button == 1:
                    mx, my = event.pos
                    if MAP_H <= my < MAP_H + EVENT_LOG_H and mx < MAP_W:
                        for y0, y1, tick_idx, rid in event_log_rows:
                            if y0 <= my < y1:
                                current_idx = tick_idx
                                playing = False
                                if rid in layout:
                                    cam_x, cam_y = layout[rid]
                                break
                    elif panning and not drag_moved and mx < MAP_W and my < MAP_H:
                        rid = pick_region(layout, ticks[current_idx],
                                          mx, my, cam_x, cam_y, zoom)
                        selected_rid = rid
                    panning = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if MAP_H <= my < MAP_H + EVENT_LOG_H and mx < MAP_W:
                    hover_row = -1
                    for row_i, (y0, y1, _, _) in enumerate(event_log_rows):
                        if y0 <= my < y1:
                            hover_row = row_i
                            break
                else:
                    hover_row = -1
                if scrubbing:
                    current_idx = tick_from_scrubber_x(mx, total)
                elif panning:
                    ddx = mx - pan_last[0]
                    ddy = my - pan_last[1]
                    if abs(ddx) > 2 or abs(ddy) > 2:
                        drag_moved = True
                    cam_x -= ddx / zoom
                    cam_y -= ddy / zoom
                    pan_last = (mx, my)

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if mx < MAP_W and my < MAP_H:
                    factor = ZOOM_STEP if event.y > 0 else 1.0 / ZOOM_STEP
                    cam_x, cam_y, zoom = zoom_toward(cam_x, cam_y, zoom, mx, my, factor)

        if playing:
            accum += dt * SPEEDS[speed_idx]
            steps = int(accum / TICK_DURATION)
            if steps > 0:
                accum -= steps * TICK_DURATION
                current_idx += steps
                if current_idx >= total:
                    current_idx = total - 1
                    playing = False

        tick_data = ticks[current_idx]

        draw_map(map_surf, tick_data, header, layout, faction_colors,
                 cam_x, cam_y, zoom, selected_rid, radar_on, font)
        screen.blit(map_surf, (0, 0))

        if faction_mode:
            draw_faction_sidebar(sidebar_surf, font, tick_data, ticks, current_idx,
                                 tracked_fid, faction_colors, faction_names, faction_ids)
        else:
            draw_sidebar(sidebar_surf, font, tick_data, header, selected_rid,
                         faction_colors, faction_names, ticks=ticks, current_idx=current_idx)
        screen.blit(sidebar_surf, (MAP_W, 0))

        event_log_rows = draw_event_log(screen, font, event_index, current_idx,
                                        region_names, hover_row)

        draw_controls(screen, font, current_idx, total, playing, speed_idx,
                      tick_data["tick"], radar_on)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
