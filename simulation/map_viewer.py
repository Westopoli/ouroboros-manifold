"""
map_viewer.py — Interactive map viewer and live mission runner.

Usage:
  # Live mission (default)
  python3 -m simulation.map_viewer [--archetype NAME] [--seed N] [--units N] [--canvas SIZE]

  # Static layout inspector
  python3 -m simulation.map_viewer --layout path/to/layout.json

Controls (live mode):
  Space       pause / resume
  + / -       speed up / slow down
  R           restart with same seed
  G           cycle gradient overlay
  L           cycle layer mask
  D           toggle drift paths
  Q / Esc     quit
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
import random
import argparse

try:
    import pygame
except ImportError:
    print("pygame not installed — run: pip install pygame")
    sys.exit(1)

try:
    import numpy as np
    _NP = True
except ImportError:
    _NP = False

try:
    from PIL import Image as _PIL_Image, ImageDraw as _PIL_Draw, ImageFont as _PIL_Font
    _PIL = True
except ImportError:
    _PIL = False

import config
from tactical_map import TacticalMap, SpineNode
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from reinforcement import ReinforcementStructure
from spine_drift import DriftingNode
from layout_library import load_all_layouts, _parse_layout
from map_gen_contracts import GeneratorInput, RegionState
from map_generator import generate_map


# ── constants ─────────────────────────────────────────────────────────────────

SCREEN_W, SCREEN_H = 1100, 860
STATUS_H = 52
MARGIN   = 10

BG          = (18, 18, 24)
GRID_COL    = (28, 30, 40)
STATUS_BG   = (22, 22, 32)
TEXT_COL    = (200, 200, 210)
DIM_COL     = (110, 110, 130)
PANEL_BG    = (24, 26, 36, 180)

NODE_COLORS = {
    "staging":                (80,  200, 120),
    "transit":                (120, 140, 180),
    "chokepoint":             (220,  80,  80),
    "vantage":                (230, 200,  50),
    "hazard_zone_anchor":     (200, 100,  30),
    "objective":              (100, 160, 255),
    "reinforcement_structure":(200,  80, 200),
    "spawn_point":            (200,  60,  60),
    "flank_route":            (100, 200, 170),
    "extraction":             ( 80, 220, 220),
}
EDGE_COLORS = {
    "path":       (160, 160, 180),
    "flank":      ( 90, 200, 150),
    "restricted": (200, 110,  50),
}
OWNER_COLORS = {
    -1: (160, 160, 160),   # neutral
     0: ( 80, 200, 120),   # player
     1: (220,  80,  80),   # enemy
}
FACTION_COLS = {0: (80, 200, 120), 1: (220, 80, 80)}
CATEGORY_SIZE = {"Strike": 2, "Line": 3, "Siege": 4}

GRADIENT_PROPS  = ["obstacle_density", "cover_density", "sensor_interference", "elevation"]
GRADIENT_COLORS = {
    "obstacle_density":    (220,  50,  50),
    "cover_density":       ( 50, 200,  80),
    "sensor_interference": (160,  60, 220),
    "elevation":           ( 60, 180, 220),
}
GRADIENT_ALPHA = 170

SPEEDS = [1, 5, 20, 50, 100]

MIXED_RATIO = {
    "Vanguard": 0.30, "Warden": 0.15, "Raider": 0.20,
    "Interceptor": 0.10, "Bombard": 0.15, "Bastion": 0.10,
}


# ── font helper (PIL-backed for crisp text) ───────────────────────────────────

_font_cache = {}

def _pil_text(text, color, size=12):
    if not _PIL:
        return None
    key = (text, color, size)
    if key in _font_cache:
        return _font_cache[key]
    try:
        font = _PIL_Font.truetype("/System/Library/Fonts/Menlo.ttc", size)
    except Exception:
        font = _PIL_Font.load_default()
    dummy = _PIL_Image.new("RGBA", (1, 1))
    dd = _PIL_Draw.Draw(dummy)
    bb = dd.textbbox((0, 0), text, font=font)
    w, h = bb[2] - bb[0] + 2, bb[3] - bb[1] + 2
    img = _PIL_Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    _PIL_Draw.Draw(img).text((0, -bb[1]), text, font=font, fill=(*color, 255))
    surf = pygame.image.frombuffer(img.tobytes(), img.size, "RGBA")
    _font_cache[key] = surf
    return surf


def blit_text(screen, text, pos, color=TEXT_COL, size=12):
    surf = _pil_text(text, color, size)
    if surf:
        screen.blit(surf, pos)
    else:
        # fallback: pygame default font
        f = pygame.font.SysFont("monospace", size)
        s = f.render(text, True, color)
        screen.blit(s, pos)


# ── coordinate transform ──────────────────────────────────────────────────────

class Transform:
    def __init__(self, map_w, map_h, screen_w, screen_h):
        self.update(map_w, map_h, screen_w, screen_h)

    def update(self, map_w, map_h, screen_w, screen_h):
        self.map_w = map_w
        self.map_h = map_h
        draw_w = screen_w - 2 * MARGIN
        draw_h = screen_h - STATUS_H - 2 * MARGIN
        scale = min(draw_w / map_w, draw_h / map_h)
        self.scale = scale
        self.off_x = MARGIN + (draw_w - map_w * scale) / 2
        self.off_y = MARGIN + (draw_h - map_h * scale) / 2
        self.vp_x = int(self.off_x)
        self.vp_y = int(self.off_y)
        self.vp_w = int(map_w * scale)
        self.vp_h = int(map_h * scale)

    def w2s(self, wx, wy):
        return (int(self.off_x + wx * self.scale),
                int(self.off_y + wy * self.scale))

    def s2w(self, sx, sy):
        return ((sx - self.off_x) / self.scale,
                (sy - self.off_y) / self.scale)


# ── gradient surface renderer (numpy) ────────────────────────────────────────

def _build_gradient_surf(tmap, prop, tf):
    """Pre-render gradient heatmap to SRCALPHA pygame Surface."""
    vw, vh = tf.vp_w, tf.vp_h
    if not _NP or vw <= 0 or vh <= 0:
        return None

    N = 6  # downsample: sample every N screen pixels
    cols = max(1, vw // N)
    rows = max(1, vh // N)

    # World coords for each sample
    wx = (np.arange(cols) + 0.5) / cols * tmap.width
    wy = (np.arange(rows) + 0.5) / rows * tmap.height
    WX, WY = np.meshgrid(wx, wy)   # both (rows, cols)

    total = np.zeros((rows, cols), dtype=np.float32)
    sources = [s for s in tmap.gradient_sources if s.property_type == prop]
    for src in sources:
        dx = WX - src.position[0]
        dy = WY - src.position[1]
        dist = np.sqrt(dx * dx + dy * dy)
        t = dist / max(src.radius, 1e-6)
        if src.falloff == "quadratic":
            falloff = (1.0 - t) ** 2
        else:
            falloff = 1.0 - t
        total += src.intensity * np.where(t < 1.0, falloff, 0.0)

    total = np.clip(total, 0.0, 1.0)   # (rows, cols)

    r, g, b = GRADIENT_COLORS[prop]
    alpha = (total * GRADIENT_ALPHA).astype(np.uint8)   # (rows, cols)

    # pygame surfarray wants (width, height) = (cols, rows), indexed [x, y]
    rgba = np.zeros((cols, rows, 4), dtype=np.uint8)
    rgba[:, :, 0] = r
    rgba[:, :, 1] = g
    rgba[:, :, 2] = b
    rgba[:, :, 3] = alpha.T   # transpose: (cols, rows)

    small = pygame.Surface((cols, rows), pygame.SRCALPHA)
    pygame.surfarray.blit_array(small, rgba[:, :, :3])
    pygame.surfarray.pixels_alpha(small)[:, :] = rgba[:, :, 3]

    return pygame.transform.scale(small, (vw, vh))


def _build_layer_surf(tmap, layer_idx, tf):
    vw, vh = tf.vp_w, tf.vp_h
    if not _NP or vw <= 0 or vh <= 0:
        return None

    N = 8
    cols = max(1, vw // N)
    rows = max(1, vh // N)

    wx = (np.arange(cols) + 0.5) / cols * tmap.width
    wy = (np.arange(rows) + 0.5) / rows * tmap.height
    WX, WY = np.meshgrid(wx, wy)

    prop = f"layer_block_{layer_idx}"
    total = np.zeros((rows, cols), dtype=np.float32)
    sources = [s for s in tmap.gradient_sources if s.property_type == prop]
    for src in sources:
        dx = WX - src.position[0]
        dy = WY - src.position[1]
        dist = np.sqrt(dx * dx + dy * dy)
        t = dist / max(src.radius, 1e-6)
        falloff = 1.0 - t
        total += src.intensity * np.where(t < 1.0, falloff, 0.0)

    blocked = np.clip(total, 0.0, 1.0) >= 0.5

    rgba = np.zeros((cols, rows, 4), dtype=np.uint8)
    rgba[:, :, 0] = np.where(blocked.T, 220, 60)
    rgba[:, :, 1] = np.where(blocked.T, 60,  200)
    rgba[:, :, 2] = 80
    rgba[:, :, 3] = 120

    small = pygame.Surface((cols, rows), pygame.SRCALPHA)
    pygame.surfarray.blit_array(small, rgba[:, :, :3])
    pygame.surfarray.pixels_alpha(small)[:, :] = rgba[:, :, 3]

    return pygame.transform.scale(small, (vw, vh))


# ── drawing helpers ───────────────────────────────────────────────────────────

def _dashed_line(surface, color, p1, p2, width=1, dash=8, gap=5):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    pos, drawing = 0.0, True
    while pos < length:
        seg = dash if drawing else gap
        nxt = min(pos + seg, length)
        if drawing:
            a = (int(p1[0] + ux * pos), int(p1[1] + uy * pos))
            b = (int(p1[0] + ux * nxt), int(p1[1] + uy * nxt))
            pygame.draw.line(surface, color, a, b, width)
        pos, drawing = nxt, not drawing


def _capture_arc(surface, cx, cy, radius, progress, owner_col):
    """Draw capture progress as an arc overlay around a structure."""
    if progress <= 0:
        return
    rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    angle = int(progress * 360)
    pygame.draw.arc(surface, (100, 180, 255), rect,
                    math.radians(90), math.radians(90 - angle), 3)


# ── map drawing ───────────────────────────────────────────────────────────────

def draw_map(screen, tmap, tf, engine=None,
             gradient_surf=None, layer_surf=None,
             show_drift_paths=True, drift_tick=0):

    # Map background
    pygame.draw.rect(screen, (22, 24, 32),
                     (tf.vp_x, tf.vp_y, tf.vp_w, tf.vp_h))

    # Gradient overlay
    if gradient_surf:
        screen.blit(gradient_surf, (tf.vp_x, tf.vp_y))

    # Layer overlay
    if layer_surf:
        screen.blit(layer_surf, (tf.vp_x, tf.vp_y))

    # Edges
    for na, nb, etype in tmap.edges:
        p1 = tf.w2s(*na.position)
        p2 = tf.w2s(*nb.position)
        col = EDGE_COLORS.get(etype, (130, 130, 150))
        if etype in ("flank", "restricted"):
            _dashed_line(screen, col, p1, p2, width=1)
        else:
            pygame.draw.line(screen, col, p1, p2, 1)

    # Drift paths
    if show_drift_paths:
        for dn in tmap.drifting_nodes:
            pts = [tf.w2s(*wp) for wp in dn.waypoints]
            if len(pts) > 1:
                col = NODE_COLORS.get(dn.node_type, (100, 160, 255))
                dim = tuple(max(0, c // 3) for c in col)
                for i in range(len(pts) - 1):
                    _dashed_line(screen, dim, pts[i], pts[i + 1], width=1)
                if dn.mode == "loop":
                    _dashed_line(screen, dim, pts[-1], pts[0], width=1)
            # Current drift position
            cur = tf.w2s(*dn.position_at(drift_tick))
            dcol = NODE_COLORS.get(dn.node_type, (100, 160, 255))
            pygame.draw.circle(screen, dcol, cur, 6)
            pygame.draw.circle(screen, (255, 255, 255), cur, 6, 1)

    # Spine nodes
    for sn in tmap.spine_nodes:
        px, py = tf.w2s(*sn.position)
        col = NODE_COLORS.get(sn.node_type, (160, 160, 160))
        r = max(3, int(7 * tf.scale / (tmap.width / 8000)))
        pygame.draw.circle(screen, col, (px, py), r)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), r, 1)

    # Reinforcement structures
    if engine:
        for s in engine.reinforcement_structures:
            px, py = tf.w2s(*s.position)
            owner_col = OWNER_COLORS.get(s.owner_faction, (200, 80, 200))
            cr = max(4, int(10 * tf.scale / (tmap.width / 8000)))
            # Capture radius ring (very faint)
            cap_r = int(s.capture_radius * tf.scale)
            if cap_r > 3:
                pygame.draw.circle(screen, (60, 60, 80), (px, py), cap_r, 1)
            # Structure body
            pygame.draw.circle(screen, owner_col, (px, py), cr)
            pygame.draw.circle(screen, (255, 255, 255), (px, py), cr, 1)
            # Capture progress arc
            if s.capture_progress > 0 and cr > 3:
                _capture_arc(screen, px, py, cr + 4, s.capture_progress, owner_col)

    # Units
    if engine:
        store = engine.store
        for uid in store.active_ids():
            x = store.data[uid, FIELD_X]
            y = store.data[uid, FIELD_Y]
            px, py = tf.w2s(x, y)
            faction = int(store.faction[uid])
            col = FACTION_COLS.get(faction, (200, 200, 200))
            cat = store.category[uid]
            from unit import CATEGORY_NAMES
            cat_name = CATEGORY_NAMES.get(cat, "Line")
            r = CATEGORY_SIZE.get(cat_name, 2)
            pygame.draw.circle(screen, col, (px, py), r)

    # Map border
    pygame.draw.rect(screen, (50, 52, 68),
                     (tf.vp_x, tf.vp_y, tf.vp_w, tf.vp_h), 1)


# ── status bar ────────────────────────────────────────────────────────────────

def draw_status(screen, sw, sh, engine, speed_idx, paused,
                gradient_mode, layer_mode, chosen_layout):
    bar_y = sh - STATUS_H
    pygame.draw.rect(screen, STATUS_BG, (0, bar_y, sw, STATUS_H))
    pygame.draw.line(screen, (50, 52, 68), (0, bar_y), (sw, bar_y), 1)

    tick = engine.tick if engine else 0
    active = list(engine.store.active_ids()) if engine else []
    n_p = sum(1 for u in active if engine.store.faction[u] == 0)
    n_e = sum(1 for u in active if engine.store.faction[u] == 1)
    structs = engine.reinforcement_structures if engine else []
    sp = SPEEDS[speed_idx]

    state = "PAUSED" if paused else f"×{sp}"
    grad  = gradient_mode or "off"
    lay   = str(layer_mode) if layer_mode is not None else "off"

    blit_text(screen, f"tick {tick:>6}", (8, bar_y + 6),  color=(180, 180, 200), size=13)
    blit_text(screen, f"▶ {n_p:>3}", (130, bar_y + 6),  color=( 80, 200, 120), size=13)
    blit_text(screen, f"◀ {n_e:>3}", (210, bar_y + 6),  color=(220,  80,  80), size=13)
    blit_text(screen, f"structs {len(structs)}",
              (295, bar_y + 6), color=(200,  80, 200), size=13)
    blit_text(screen, f"layout: {chosen_layout}",
              (8, bar_y + 26), color=DIM_COL, size=11)
    blit_text(screen, f"gradient: {grad}",
              (270, bar_y + 26), color=DIM_COL, size=11)
    blit_text(screen, f"layer: {lay}",
              (420, bar_y + 26), color=DIM_COL, size=11)

    blit_text(screen, f"[{state}]",
              (sw - 180, bar_y + 6), color=(230, 200, 80), size=13)
    blit_text(screen,
              "Space=pause  G=gradient  L=layer  D=drift  +/-=speed  R=restart  Q=quit",
              (sw - 600, bar_y + 26), color=DIM_COL, size=10)


# ── spawn helpers ─────────────────────────────────────────────────────────────

def _spawn_force(store, faction, cx, cy, count, rng):
    roster = []
    for ut, frac in MIXED_RATIO.items():
        roster.extend([ut] * max(1, round(count * frac)))
    while len(roster) > count: roster.pop(rng.randrange(len(roster)))
    while len(roster) < count: roster.append(rng.choice(list(MIXED_RATIO)))
    rng.shuffle(roster)
    cols = max(5, int(math.sqrt(count)) + 1)
    uids = []
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uid = store.spawn(ut, faction, x, y)
        if uid >= 0:
            uids.append(uid)
    return uids


def _setup_live(archetype, seed, unit_count, canvas_size):
    layout_lib = load_all_layouts()
    result = generate_map(GeneratorInput(
        archetype=archetype,
        region_state=RegionState(
            stability=0.60, capacity=0.70,
            economy=55.0, tension=50.0, military=60.0, population=55.0,
            region_id="viewer_region", tier=2,
        ),
        canvas_size=canvas_size,
        seed=seed,
    ), layout_lib)

    tmap = result.tactical_map
    rng  = random.Random(seed)

    # Add drifting objective (first objective spine node)
    obj_nodes = tmap.get_spine_nodes_by_type("objective")
    if obj_nodes:
        sn = obj_nodes[0]
        px, py = sn.position
        pad = tmap.width * 0.10
        wp  = [(max(pad, px - 1000), py), (min(tmap.width - pad, px + 1000), py)]
        tmap.drifting_nodes = [DriftingNode(
            "obj_drift", "objective", sn, wp, period_ticks=800, mode="ping_pong"
        )]

    # Convert reinforcement_structure spine nodes to runtime structures
    structs = []
    owner_map = {"player": 0, "neutral": -1, "enemy": 1}
    for i, sn in enumerate(tmap.get_spine_nodes_by_type("reinforcement_structure")):
        ow = owner_map.get(sn.properties.get("initial_owner", "neutral"), -1)
        structs.append(ReinforcementStructure(
            structure_uid=i, position=sn.position, layer=0,
            hp=float(config.REINFORCEMENT_STRUCTURE_HP),
            max_hp=float(config.REINFORCEMENT_STRUCTURE_HP),
            owner_faction=ow, capture_progress=0.0,
            production_timer_sec=0.0,
            production_target_unit_type=rng.choice(["Vanguard", "Raider"]),
            capture_radius=config.REINFORCEMENT_CAPTURE_RADIUS,
        ))

    engine = TacticalEngine(tmap, seed=seed)
    engine.reinforcement_structures = structs
    engine.enable_reinforcement = True

    # Spawn on staging nodes if available, else fixed positions
    staging = tmap.get_spine_nodes_by_type("staging")
    if len(staging) >= 2:
        px0, py0 = staging[0].position
        px1, py1 = staging[-1].position
    else:
        px0, py0 = tmap.width * 0.1, tmap.height * 0.1
        px1, py1 = tmap.width * 0.9, tmap.height * 0.9

    p_uids = _spawn_force(engine.store, 0, px0, py0, unit_count, rng)
    e_uids = _spawn_force(engine.store, 1, px1, py1, unit_count, rng)

    q = engine.command_queue
    q.add(Command(tick=0, type="attack_move", unit_ids=p_uids,
                  params={"target_x": px1, "target_y": py1}))
    q.add(Command(tick=0, type="attack_move", unit_ids=e_uids,
                  params={"target_x": px0, "target_y": py0}))

    return engine, result.chosen_layout_id


# ── live viewer ───────────────────────────────────────────────────────────────

def run_live(archetype="defensive_stand", seed=0xBEEF_CAFE,
             unit_count=60, canvas_size="medium"):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Ouroboros — Live Mission Viewer")
    clock = pygame.time.Clock()

    print(f"Generating map (archetype={archetype}, seed={seed:#x}, {canvas_size})...")
    engine, chosen_layout = _setup_live(archetype, seed, unit_count, canvas_size)
    tmap = engine.map

    sw, sh = screen.get_size()
    tf = Transform(tmap.width, tmap.height, sw, sh)

    print("Pre-rendering gradient surfaces...")
    grad_surfs  = {p: _build_gradient_surf(tmap, p, tf) for p in GRADIENT_PROPS}
    layer_surfs = {i: _build_layer_surf(tmap, i, tf) for i in range(tmap.layers)}
    print("Ready.")

    paused       = False
    speed_idx    = 1   # start at ×5
    grad_idx     = -1  # -1 = off
    layer_idx    = -1  # -1 = off
    show_drift   = True
    gradient_mode = None
    layer_mode    = None
    _last_size   = (sw, sh)

    running = True
    while running:
        sw, sh = screen.get_size()
        if (sw, sh) != _last_size:
            tf.update(tmap.width, tmap.height, sw, sh)
            grad_surfs  = {p: _build_gradient_surf(tmap, p, tf) for p in GRADIENT_PROPS}
            layer_surfs = {i: _build_layer_surf(tmap, i, tf) for i in range(tmap.layers)}
            _last_size  = (sw, sh)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif k == pygame.K_SPACE:
                    paused = not paused
                elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    speed_idx = min(speed_idx + 1, len(SPEEDS) - 1)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_idx = max(speed_idx - 1, 0)
                elif k == pygame.K_r:
                    engine, chosen_layout = _setup_live(archetype, seed, unit_count, canvas_size)
                    tmap = engine.map
                    tf.update(tmap.width, tmap.height, sw, sh)
                    grad_surfs  = {p: _build_gradient_surf(tmap, p, tf) for p in GRADIENT_PROPS}
                    layer_surfs = {i: _build_layer_surf(tmap, i, tf) for i in range(tmap.layers)}
                elif k == pygame.K_g:
                    grad_idx = (grad_idx + 1) % (len(GRADIENT_PROPS) + 1) - 1
                    # cycles: -1, 0, 1, 2, 3, -1, ...
                    if grad_idx < -1: grad_idx = len(GRADIENT_PROPS) - 1
                    gradient_mode = GRADIENT_PROPS[grad_idx] if grad_idx >= 0 else None
                elif k == pygame.K_l:
                    layer_idx = (layer_idx + 1) % (tmap.layers + 1) - 1
                    if layer_idx < -1: layer_idx = tmap.layers - 1
                    layer_mode = layer_idx if layer_idx >= 0 else None
                elif k == pygame.K_d:
                    show_drift = not show_drift

        if not paused and not engine.is_terminal():
            for _ in range(SPEEDS[speed_idx]):
                engine.step()
                if engine.is_terminal():
                    paused = True
                    break

        screen.fill(BG)

        g_surf = grad_surfs.get(gradient_mode) if gradient_mode else None
        l_surf = layer_surfs.get(layer_mode) if layer_mode is not None else None

        draw_map(screen, tmap, tf, engine=engine,
                 gradient_surf=g_surf, layer_surf=l_surf,
                 show_drift_paths=show_drift,
                 drift_tick=engine.tick)

        # Node type legend (top-right corner)
        lx = sw - 170
        ly = MARGIN + 4
        panel = pygame.Surface((162, len(NODE_COLORS) * 15 + 10), pygame.SRCALPHA)
        panel.fill(PANEL_BG)
        screen.blit(panel, (lx - 4, ly - 2))
        for name, col in NODE_COLORS.items():
            pygame.draw.circle(screen, col, (lx + 5, ly + 5), 4)
            blit_text(screen, name, (lx + 13, ly - 1), color=DIM_COL, size=10)
            ly += 15

        draw_status(screen, sw, sh, engine, speed_idx, paused,
                    gradient_mode, layer_mode, chosen_layout)

        if engine.is_terminal():
            active = list(engine.store.active_ids())
            n_p = sum(1 for u in active if engine.store.faction[u] == 0)
            msg = "PLAYER WINS" if n_p > 0 else "ENEMY WINS"
            col = (80, 220, 120) if n_p > 0 else (220, 80, 80)
            blit_text(screen, msg, (sw // 2 - 50, sh // 2 - 20), color=col, size=22)
            blit_text(screen, "R to restart", (sw // 2 - 46, sh // 2 + 10),
                      color=DIM_COL, size=13)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# ── static layout viewer (Checkpoint A behavior, retained) ───────────────────

def run_static(layout_json_path):
    import json
    with open(layout_json_path) as f:
        data = json.load(f)
    layout = _parse_layout(data)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption(f"Map Viewer — {layout.name}")
    clock  = pygame.time.Clock()
    zone_map = {z.zone_id: z for z in layout.zones}

    running = True
    while running:
        sw, sh = screen.get_size()
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        draw_w = sw - 2 * MARGIN
        draw_h = sh - STATUS_H - 2 * MARGIN
        def sratio(rx, ry):
            return (int(MARGIN + rx * draw_w), int(MARGIN + ry * draw_h))

        screen.fill(BG)

        for edge in layout.edges:
            zf, zt = zone_map.get(edge.from_zone), zone_map.get(edge.to_zone)
            if not zf or not zt: continue
            p1, p2 = sratio(*zf.position_ratio), sratio(*zt.position_ratio)
            col = EDGE_COLORS.get(edge.edge_type, (130, 130, 150))
            if edge.edge_type in ("flank", "restricted"):
                _dashed_line(screen, col, p1, p2)
            else:
                pygame.draw.line(screen, col, p1, p2, 1)

        hovered = None
        for zone in layout.zones:
            px, py = sratio(*zone.position_ratio)
            col    = NODE_COLORS.get(zone.node_type, (160, 160, 160))
            pygame.draw.circle(screen, col, (px, py), 10)
            pygame.draw.circle(screen, (255, 255, 255), (px, py), 10, 1)
            if abs(mx - px) <= 14 and abs(my - py) <= 14:
                hovered = zone
            blit_text(screen, zone.zone_id, (px + 13, py - 6), color=DIM_COL, size=10)

        if hovered:
            lines = [f"{hovered.zone_id}", f"type: {hovered.node_type}",
                     f"pos: ({hovered.position_ratio[0]:.2f}, {hovered.position_ratio[1]:.2f})"]
            lines += [f"  {k}: {v}" for k, v in hovered.properties.items()]
            tw = max(len(l) * 7 for l in lines) + 10
            th = len(lines) * 14 + 8
            tx, ty = min(mx + 14, sw - tw - 4), min(my + 14, sh - th - 4)
            pygame.draw.rect(screen, (28, 28, 40), (tx - 2, ty - 2, tw, th))
            pygame.draw.rect(screen, (80, 80, 110), (tx - 2, ty - 2, tw, th), 1)
            for i, line in enumerate(lines):
                blit_text(screen, line, (tx + 3, ty + i * 14), size=11)

        # Legend
        lx, ly = 8, 8
        for name, col in NODE_COLORS.items():
            pygame.draw.circle(screen, col, (lx + 5, ly + 5), 4)
            blit_text(screen, name, (lx + 13, ly - 1), color=DIM_COL, size=10)
            ly += 15

        title = f"{layout.name}  [{layout.canvas_class}]  {len(layout.zones)} zones  {len(layout.edges)} edges"
        blit_text(screen, title, (sw // 2 - 200, sh - STATUS_H + 16),
                  color=DIM_COL, size=12)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ouroboros map viewer")
    parser.add_argument("--layout",   default=None, help="Path to layout JSON (static view)")
    parser.add_argument("--archetype",default="defensive_stand")
    parser.add_argument("--seed",     default=0xBEEF_CAFE, type=lambda x: int(x, 0))
    parser.add_argument("--units",    default=60, type=int)
    parser.add_argument("--canvas",   default="medium",
                        choices=["small", "medium", "large"])
    # legacy positional arg (Checkpoint A)
    parser.add_argument("layout_json", nargs="?", default=None)
    args = parser.parse_args()

    layout_path = args.layout or args.layout_json
    if layout_path:
        run_static(layout_path)
    else:
        run_live(archetype=args.archetype, seed=args.seed,
                 unit_count=args.units, canvas_size=args.canvas)


if __name__ == "__main__":
    main()
