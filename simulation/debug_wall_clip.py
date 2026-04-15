"""
debug_wall_clip.py — Visualises the LOS-simplification wall-clip bug.

Reproduces the exact scenario from test_obstacle_navigation.py:
  - 2000×1000 canvas, navmesh cell=100 (20×10 grid)
  - Wall: rows 4–5, cols 3–18 (cell centers 350..1850 × 450/550)
  - Left corridor: cols 0–2 (x < 300)
  - Unit starts at (1000, 75), navigates to (1000, 925)
  - A* finds the corridor, _simplify_path produces a long diagonal
    from start to waypoint (250, 450) that clips through cell (4,3)
    at approx (300, 416) — a wall cell

What to watch:
  - White line: computed A* path (waypoints)
  - Green dot: unit
  - Cell tints: dark red = blocked, pale = open
  - Cell border turns BRIGHT RED when the unit physically occupies a blocked cell
  - Status bar shows current cell and whether it is walkable

Controls:  Space = pause/resume   + / - = speed   Q = quit
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pygame
except ImportError:
    print("pygame not installed")
    sys.exit(1)

from PIL import Image as _PILImage, ImageDraw as _PILDraw, ImageFont as _PILFont

_font_cache = {}

def _pil_text(text, color, size=12, bold=False):
    key = (text, color, size, bold)
    if key in _font_cache:
        return _font_cache[key]
    try:
        font = _PILFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
    except Exception:
        font = _PILFont.load_default()
    dummy = _PILImage.new("RGBA", (1, 1))
    bb = _PILDraw.Draw(dummy).textbbox((0, 0), text, font=font)
    w, h = bb[2] - bb[0] + 2, bb[3] - bb[1] + 2
    img = _PILImage.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    _PILDraw.Draw(img).text((0, -bb[1]), text, font=font, fill=(*color, 255))
    surf = pygame.image.frombuffer(img.tobytes(), img.size, "RGBA")
    _font_cache[key] = surf
    return surf

def blit_text(screen, text, pos, color=(200, 200, 210), size=12, bold=False):
    screen.blit(_pil_text(text, color, size, bold), pos)

import config
from tactical_map import TacticalMap, GradientSource
from unit import UnitStore, FIELD_X, FIELD_Y
import heapq
from movement import Navmesh, find_path, update_movement, _bresenham, _supercover

# ── path helpers (compute old/new paths from same raw A*) ────────────────────

def _astar_raw(nm, sx, sy, gx, gy):
    """A* without simplification — returns raw cell-centre waypoints."""
    SQRT2 = math.sqrt(2)
    sr, sc = nm.cell(sx, sy)
    gr, gc = nm.cell(gx, gy)
    if (sr, sc) == (gr, gc):
        return [(gx, gy)]
    if not nm.is_walkable(gr, gc):
        return [(gx, gy)]
    def h(r, c):
        dr, dc = abs(r - gr), abs(c - gc)
        return max(dr, dc) + (SQRT2 - 1) * min(dr, dc)
    open_set = [(h(sr, sc), 0.0, sr, sc)]
    g_score  = {(sr, sc): 0.0}
    came_from = {}
    while open_set:
        _, g, r, c = heapq.heappop(open_set)
        if (r, c) == (gr, gc):
            path, cur = [], (gr, gc)
            while cur in came_from:
                path.append(nm.cell_center(*cur))
                cur = came_from[cur]
            path.reverse()
            if path:
                path[-1] = (gx, gy)
            else:
                path = [(gx, gy)]
            return path
        if g > g_score.get((r, c), float('inf')):
            continue
        for nr, nc in nm.neighbors(r, c):
            d = SQRT2 if (nr != r and nc != c) else 1.0
            ng = g + d
            if ng < g_score.get((nr, nc), float('inf')):
                g_score[(nr, nc)] = ng
                came_from[(nr, nc)] = (r, c)
                heapq.heappush(open_set, (ng + h(nr, nc), ng, nr, nc))
    return [(gx, gy)]


def _simplify_with(nm, sx, sy, path, los_fn):
    if len(path) <= 1:
        return path
    full = [(sx, sy)] + path
    simplified, i = [], 0
    while i < len(full) - 1:
        furthest = i + 1
        for j in range(i + 2, len(full)):
            r1, c1 = nm.cell(*full[i])
            r2, c2 = nm.cell(*full[j])
            clear = all(nm.is_walkable(r, c) for r, c in los_fn(r1, c1, r2, c2))
            if clear:
                furthest = j
        simplified.append(full[furthest])
        i = furthest
    return simplified


# ── scenario (identical to test_obstacle_navigation) ──────────────────────────

CANVAS_W, CANVAS_H = 2000, 1000
CELL = config.NAVMESH_CELL_SIZE          # 100
WALL_COLS = list(range(3, 19))           # cols 3..18
WALL_ROWS = [4, 5]
SRC_RADIUS   = CELL * 0.55
SRC_INTENSITY = 1.0

START_X, START_Y = 1000.0,  75.0
GOAL_X,  GOAL_Y  = 1000.0, 925.0

def _build_map():
    sources = []
    for row in WALL_ROWS:
        for col in WALL_COLS:
            cx, cy = (col + 0.5) * CELL, (row + 0.5) * CELL
            sources.append(GradientSource(
                position=(cx, cy),
                property_type="obstacle_density",
                radius=SRC_RADIUS, intensity=SRC_INTENSITY, falloff="constant",
            ))
    return TacticalMap(width=CANVAS_W, height=CANVAS_H, gradient_sources=sources)

# ── pygame setup ──────────────────────────────────────────────────────────────

SW, SH    = 1200, 700
STATUS_H  = 50
MARGIN    = 12

BG          = (14, 14, 20)
STATUS_BG   = (20, 20, 30)
OPEN_CELL   = (30, 35, 45)
BLOCKED_CELL= (80, 20, 20)
WALL_BORDER = (160, 40, 40)
VIOLATION_CELL  = (255, 30, 30)
VIOLATION_FILL  = (180, 20, 20)
GRID_LINE   = (40, 44, 58)
OLD_PATH_COL = (230, 120,  40)   # orange — Bresenham (clips wall)
NEW_PATH_COL = ( 60, 210, 210)   # cyan   — Supercover (correct)
UNIT_COL    = (80, 220, 120)
UNIT_VIO    = (255, 60, 60)
TRAIL_COL   = (60, 160, 90)
GOAL_COL    = (80, 160, 255)
START_COL   = (200, 80, 200)
TEXT_COL    = (200, 200, 210)
DIM_COL     = (110, 110, 130)

SPEEDS = [1, 5, 20, 50]

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


def _w2s(wx, wy, tf):
    return (int(tf[0] + wx * tf[2]), int(tf[1] + wy * tf[2]))

def _make_tf(sw, sh):
    draw_w = sw - 2 * MARGIN
    draw_h = sh - STATUS_H - 2 * MARGIN
    scale  = min(draw_w / CANVAS_W, draw_h / CANVAS_H)
    off_x  = MARGIN + (draw_w - CANVAS_W * scale) / 2
    off_y  = MARGIN + (draw_h - CANVAS_H * scale) / 2
    return (off_x, off_y, scale)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SW, SH), pygame.RESIZABLE)
    pygame.display.set_caption("Wall-clip bug visualiser")
    clock  = pygame.time.Clock()

    tmap = _build_map()
    nm   = Navmesh.from_tactical_map(tmap)

    def reset():
        s = UnitStore()
        u = s.spawn("Vanguard", 0, START_X, START_Y)
        s.set_move_target(u, GOAL_X, GOAL_Y)
        return s, u, []

    store, uid, trail = reset()

    # Compute both paths from the same raw A* output so they're directly comparable.
    # old_path uses Bresenham LOS (clips wall corners).
    # new_path uses supercover LOS (safe). The simulation follows new_path.
    raw_path = _astar_raw(nm, START_X, START_Y, GOAL_X, GOAL_Y)
    old_path = _simplify_with(nm, START_X, START_Y, raw_path, _bresenham)
    new_path = _simplify_with(nm, START_X, START_Y, raw_path, _supercover)

    paused    = True   # start paused so user can read the layout
    speed_idx = 1
    violation_ticks = 0
    tick = 0

    sw, sh = screen.get_size()
    tf = _make_tf(sw, sh)

    running = True
    while running:
        sw, sh = screen.get_size()
        tf = _make_tf(sw, sh)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif k == pygame.K_SPACE:
                    paused = not paused
                elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    speed_idx = min(speed_idx + 1, len(SPEEDS) - 1)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_idx = max(speed_idx - 1, 0)
                elif k == pygame.K_r:
                    store, uid, trail = reset()
                    violation_ticks = 0
                    tick = 0
                    paused = True

        if not paused and store.has_move_target[uid]:
            for _ in range(SPEEDS[speed_idx]):
                update_movement(store, tmap, 0.1)
                tick += 1
                x = float(store.data[uid, FIELD_X])
                y = float(store.data[uid, FIELD_Y])
                r, c = nm.cell(x, y)
                in_wall = not nm.is_walkable(r, c)
                trail.append((x, y, in_wall))
                if in_wall:
                    violation_ticks += 1
                if not store.has_move_target[uid]:
                    paused = True
                    break

        # ── draw ──────────────────────────────────────────────────────────────
        screen.fill(BG)

        # navmesh cells
        cell_px = max(1, int(CELL * tf[2]))
        for row in range(nm.rows):
            for col in range(nm.cols):
                px, py = _w2s(col * CELL, row * CELL, tf)
                walkable = nm.is_walkable(row, col)
                fill = OPEN_CELL if walkable else BLOCKED_CELL
                rect = pygame.Rect(px, py, cell_px, cell_px)
                pygame.draw.rect(screen, fill, rect)
                border = WALL_BORDER if not walkable else GRID_LINE
                pygame.draw.rect(screen, border, rect, 1)

        # highlight current cell occupation
        x = float(store.data[uid, FIELD_X])
        y = float(store.data[uid, FIELD_Y])
        ur, uc = nm.cell(x, y)
        in_wall = not nm.is_walkable(ur, uc)
        if in_wall:
            px, py = _w2s(uc * CELL, ur * CELL, tf)
            pygame.draw.rect(screen, VIOLATION_FILL,
                             pygame.Rect(px, py, cell_px, cell_px))
            pygame.draw.rect(screen, VIOLATION_CELL,
                             pygame.Rect(px, py, cell_px, cell_px), 2)

        # trail
        for (tx, ty, tv) in trail[-400:]:
            sp = _w2s(tx, ty, tf)
            col_t = (220, 60, 60) if tv else TRAIL_COL
            pygame.draw.circle(screen, col_t, sp, 2)

        # Old path — Bresenham (orange, dashed)
        def _draw_path(pts_world, col, dash=True, wp_r=5):
            pts = [_w2s(START_X, START_Y, tf)] + [_w2s(wx, wy, tf) for wx, wy in pts_world]
            for i in range(len(pts) - 1):
                if dash:
                    _dashed_line(screen, col, pts[i], pts[i+1])
                else:
                    pygame.draw.line(screen, col, pts[i], pts[i+1], 2)
            for (wx, wy) in pts_world:
                sp = _w2s(wx, wy, tf)
                pygame.draw.circle(screen, col, sp, wp_r)
                pygame.draw.circle(screen, (255,255,255), sp, wp_r, 1)

        _draw_path(old_path, OLD_PATH_COL, dash=True,  wp_r=5)
        _draw_path(new_path, NEW_PATH_COL, dash=False, wp_r=5)

        # start / goal markers
        pygame.draw.circle(screen, START_COL,  _w2s(START_X, START_Y, tf), 7)
        pygame.draw.circle(screen, GOAL_COL,   _w2s(GOAL_X,  GOAL_Y,  tf), 7)

        # unit dot
        up = _w2s(x, y, tf)
        u_col = UNIT_VIO if in_wall else UNIT_COL
        pygame.draw.circle(screen, u_col, up, 6)
        pygame.draw.circle(screen, (255,255,255), up, 6, 1)

        # ── legend ────────────────────────────────────────────────────────────
        lx, ly = MARGIN + 4, MARGIN + 4
        for col_l, label in [(OLD_PATH_COL, f"Bresenham ({len(old_path)} wps) — clips wall"),
                             (NEW_PATH_COL, f"Supercover ({len(new_path)} wps) — correct")]:
            pygame.draw.line(screen, col_l, (lx, ly + 5), (lx + 20, ly + 5), 2)
            pygame.draw.circle(screen, col_l, (lx + 10, ly + 5), 4)
            blit_text(screen, label, (lx + 25, ly - 1), color=col_l, size=11)
            ly += 18

        # ── annotate the clip zone ─────────────────────────────────────────────
        clip_s = _w2s(300, 416, tf)
        pygame.draw.circle(screen, (255, 200, 0), clip_s, 4, 2)
        blit_text(screen, "clip ~(300,416) col3,row4", (clip_s[0] + 6, clip_s[1] - 8),
                  color=(255, 200, 0), size=11)

        # ── status bar ────────────────────────────────────────────────────────
        bar_y = sh - STATUS_H
        pygame.draw.rect(screen, STATUS_BG, (0, bar_y, sw, STATUS_H))
        pygame.draw.line(screen, (50,52,68), (0, bar_y), (sw, bar_y), 1)

        state     = "PAUSED — Space to run" if paused else f"×{SPEEDS[speed_idx]}"
        wps       = store.waypoints.get(uid, [])
        cell_info = f"cell(row={ur},col={uc}) {'WALL!' if in_wall else 'ok'}"
        vio_info  = f"wall violations: {violation_ticks} ticks"

        blit_text(screen, f"tick {tick:>5}",  (8,   bar_y + 6),  color=TEXT_COL, size=13, bold=True)
        blit_text(screen, cell_info,           (120, bar_y + 6),  color=(255,80,80) if in_wall else DIM_COL)
        blit_text(screen, vio_info,            (340, bar_y + 6),  color=(255,80,80) if violation_ticks else DIM_COL)
        blit_text(screen, f"wps left: {len(wps)}", (570, bar_y + 6), color=DIM_COL)
        blit_text(screen, f"[{state}]",        (sw-250, bar_y + 6), color=(230,200,80), size=13)
        blit_text(screen, "Space=pause  +/-=speed  R=restart  Q=quit",
                  (8, bar_y + 26), color=DIM_COL, size=11)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
