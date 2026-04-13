import sys
import json
import math

try:
    import pygame
except ImportError:
    print("sim_viewer requires pygame: pip install pygame", file=sys.stderr)
    sys.exit(1)

try:
    import pygame.freetype
    _has_freetype = True
except Exception:
    _has_freetype = False

try:
    from PIL import Image, ImageDraw
    _has_pil = True
except ImportError:
    _has_pil = False


WINDOW_W = 1280
WINDOW_H = 960
CONTROLS_H = 50
INSPECTOR_H = 80
MAP_AREA_H = WINDOW_H - CONTROLS_H - INSPECTOR_H
BG_COLOR = (15, 15, 20)
CONTROLS_BG = (28, 28, 36)
INSPECTOR_BG = (22, 22, 30)
INSPECTOR_BORDER = (50, 50, 65)
SCRUBBER_BG = (55, 55, 70)
SCRUBBER_FG = (100, 140, 220)
SCRUBBER_H = 10
SCRUBBER_PAD_X = 12
SCRUBBER_Y_OFF = 8
TEXT_COLOR = (180, 180, 190)
DIM_COLOR = (100, 100, 115)
SELECTED_COLOR = (255, 220, 60)
MIN_UNIT_RADIUS_PX = 3
CLICK_RADIUS_PX = 10
ZOOM_STEP = 1.15
ZOOM_MIN = 0.05
ZOOM_MAX = 20.0
SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
DEFAULT_SPEED_IDX = 2
ABILITY_STATES = {0: "inactive", 1: "windup", 2: "active", 3: "telegraph"}
DENSITY_CELL = 100  # world units per density cell


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def load_dump(path):
    import os
    size = 0
    try:
        size = os.path.getsize(path)
    except OSError:
        pass

    show_progress = size > 50 * 1024 * 1024
    if show_progress:
        print(f"Loading {size / 1024 / 1024:.1f} MB dump...", file=sys.stderr)

    header = None
    ticks = []
    with open(path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj["type"] == "header":
                header = obj
            elif obj["type"] == "tick":
                ticks.append(obj)
            if show_progress and i % 500 == 0:
                print(f"  {i} lines...", end="\r", file=sys.stderr)

    if show_progress:
        print(f"  Loaded {len(ticks)} ticks.        ", file=sys.stderr)

    if header is None:
        print("ERROR: no header line found in dump", file=sys.stderr)
        sys.exit(1)
    if header.get("version", 0) != 1:
        print(f"ERROR: unsupported format version {header.get('version')}", file=sys.stderr)
        sys.exit(1)
    if not ticks:
        print("ERROR: dump contains no tick lines", file=sys.stderr)
        sys.exit(1)

    return header, ticks


# ── Camera ────────────────────────────────────────────────────────────────────

def fit_zoom(map_w, map_h):
    return min(WINDOW_W / map_w, MAP_AREA_H / map_h)


def world_to_screen(wx, wy, cam_x, cam_y, zoom):
    sx = (wx - cam_x) * zoom + WINDOW_W / 2
    sy = (wy - cam_y) * zoom + MAP_AREA_H / 2
    return int(sx), int(sy)


def screen_to_world(sx, sy, cam_x, cam_y, zoom):
    wx = (sx - WINDOW_W / 2) / zoom + cam_x
    wy = (sy - MAP_AREA_H / 2) / zoom + cam_y
    return wx, wy


def zoom_toward(cam_x, cam_y, zoom, cursor_sx, cursor_sy, factor):
    wx, wy = screen_to_world(cursor_sx, cursor_sy, cam_x, cam_y, zoom)
    new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom * factor))
    new_cam_x = wx - (cursor_sx - WINDOW_W / 2) / new_zoom
    new_cam_y = wy - (cursor_sy - MAP_AREA_H / 2) / new_zoom
    return new_cam_x, new_cam_y, new_zoom


# ── Unit picking ──────────────────────────────────────────────────────────────

def pick_unit(tick_data, click_sx, click_sy, cam_x, cam_y, zoom):
    best_uid = None
    best_dist = CLICK_RADIUS_PX
    for unit in tick_data["units"]:
        sx, sy = world_to_screen(unit["x"], unit["y"], cam_x, cam_y, zoom)
        d = math.hypot(click_sx - sx, click_sy - sy)
        if d < best_dist:
            best_dist = d
            best_uid = unit["uid"]
    return best_uid


def find_unit(tick_data, uid):
    for unit in tick_data["units"]:
        if unit["uid"] == uid:
            return unit
    return None


# ── Overlays ──────────────────────────────────────────────────────────────────

def draw_overlay_targets(surface, tick_data, cam_x, cam_y, zoom):
    uid_to_unit = {u["uid"]: u for u in tick_data["units"]}
    for unit in tick_data["units"]:
        tgt_uid = unit.get("target_uid", -1)
        if tgt_uid < 0 or tgt_uid not in uid_to_unit:
            continue
        tgt = uid_to_unit[tgt_uid]
        sx1, sy1 = world_to_screen(unit["x"], unit["y"], cam_x, cam_y, zoom)
        sx2, sy2 = world_to_screen(tgt["x"], tgt["y"], cam_x, cam_y, zoom)
        pygame.draw.line(surface, (200, 200, 60, 120), (sx1, sy1), (sx2, sy2), 1)


def draw_overlay_velocity(surface, tick_data, cam_x, cam_y, zoom):
    for unit in tick_data["units"]:
        vx = unit.get("vx", 0.0)
        vy = unit.get("vy", 0.0)
        if abs(vx) < 0.01 and abs(vy) < 0.01:
            continue
        sx, sy = world_to_screen(unit["x"], unit["y"], cam_x, cam_y, zoom)
        ex, ey = world_to_screen(unit["x"] + vx, unit["y"] + vy, cam_x, cam_y, zoom)
        pygame.draw.line(surface, (100, 220, 100), (sx, sy), (ex, ey), 2)


def draw_overlay_density(surface, tick_data, cam_x, cam_y, zoom, map_w, map_h):
    cols = math.ceil(map_w / DENSITY_CELL)
    rows = math.ceil(map_h / DENSITY_CELL)
    counts = {}
    for unit in tick_data["units"]:
        c = int(unit["x"] / DENSITY_CELL)
        r = int(unit["y"] / DENSITY_CELL)
        counts[(r, c)] = counts.get((r, c), 0) + 1

    if not counts:
        return

    max_count = max(counts.values())
    cell_px = max(1, int(DENSITY_CELL * zoom))
    heat = pygame.Surface((WINDOW_W, MAP_AREA_H), pygame.SRCALPHA)

    for (r, c), n in counts.items():
        wx = c * DENSITY_CELL
        wy = r * DENSITY_CELL
        sx, sy = world_to_screen(wx, wy, cam_x, cam_y, zoom)
        alpha = int(180 * n / max_count)
        intensity = int(255 * n / max_count)
        pygame.draw.rect(heat, (intensity, 40, 40, alpha), (sx, sy, cell_px, cell_px))

    surface.blit(heat, (0, 0))


def draw_overlay_hp(surface, tick_data, cam_x, cam_y, zoom, collision_radius):
    unit_radius_px = max(MIN_UNIT_RADIUS_PX, int(collision_radius * zoom))
    bar_w = max(6, unit_radius_px * 2)
    bar_h = max(2, unit_radius_px // 2)

    for unit in tick_data["units"]:
        sx, sy = world_to_screen(unit["x"], unit["y"], cam_x, cam_y, zoom)
        if not (-bar_w <= sx <= WINDOW_W + bar_w and 0 <= sy <= MAP_AREA_H):
            continue
        ratio = unit["hp"] / max(unit["max_hp"], 1)
        bx = sx - bar_w // 2
        by = sy - unit_radius_px - bar_h - 2
        pygame.draw.rect(surface, (60, 60, 60), (bx, by, bar_w, bar_h))
        fill = max(1, int(bar_w * ratio))
        color = (80, 200, 80) if ratio > 0.5 else (220, 180, 40) if ratio > 0.25 else (220, 60, 60)
        pygame.draw.rect(surface, color, (bx, by, fill, bar_h))


def draw_overlay_grid(surface, cam_x, cam_y, zoom, map_w, map_h):
    cols = math.ceil(map_w / DENSITY_CELL)
    rows = math.ceil(map_h / DENSITY_CELL)
    color = (50, 50, 70)
    for c in range(cols + 1):
        sx, _ = world_to_screen(c * DENSITY_CELL, 0, cam_x, cam_y, zoom)
        if 0 <= sx <= WINDOW_W:
            pygame.draw.line(surface, color, (sx, 0), (sx, MAP_AREA_H))
    for r in range(rows + 1):
        _, sy = world_to_screen(0, r * DENSITY_CELL, cam_x, cam_y, zoom)
        if 0 <= sy <= MAP_AREA_H:
            pygame.draw.line(surface, color, (0, sy), (WINDOW_W, sy))


def draw_overlay_bbox(surface, tick_data, faction_colors, cam_x, cam_y, zoom):
    bounds = {}
    for unit in tick_data["units"]:
        fid = unit["faction"]
        x, y = unit["x"], unit["y"]
        if fid not in bounds:
            bounds[fid] = [x, y, x, y]
        else:
            b = bounds[fid]
            b[0] = min(b[0], x)
            b[1] = min(b[1], y)
            b[2] = max(b[2], x)
            b[3] = max(b[3], y)

    for fid, (x0, y0, x1, y1) in bounds.items():
        color = faction_colors.get(fid, (180, 180, 180))
        sx0, sy0 = world_to_screen(x0, y0, cam_x, cam_y, zoom)
        sx1, sy1 = world_to_screen(x1, y1, cam_x, cam_y, zoom)
        pygame.draw.rect(surface, color, (sx0, sy0, sx1 - sx0, sy1 - sy0), 1)


# ── Core drawing ──────────────────────────────────────────────────────────────

def draw_map(surface, tick_data, faction_colors, cam_x, cam_y, zoom,
             collision_radius, selected_uid, overlays, map_w, map_h):
    surface.fill(BG_COLOR)

    if "G" in overlays:
        draw_overlay_grid(surface, cam_x, cam_y, zoom, map_w, map_h)
    if "D" in overlays:
        draw_overlay_density(surface, tick_data, cam_x, cam_y, zoom, map_w, map_h)

    unit_radius_px = max(MIN_UNIT_RADIUS_PX, int(collision_radius * zoom))
    for unit in tick_data["units"]:
        sx, sy = world_to_screen(unit["x"], unit["y"], cam_x, cam_y, zoom)
        if -unit_radius_px - 8 <= sx <= WINDOW_W + unit_radius_px + 8 \
                and -unit_radius_px - 8 <= sy <= MAP_AREA_H + unit_radius_px + 8:
            color = faction_colors.get(unit["faction"], (180, 180, 180))
            pygame.draw.circle(surface, color, (sx, sy), unit_radius_px)
            if unit["uid"] == selected_uid:
                pygame.draw.circle(surface, SELECTED_COLOR, (sx, sy), unit_radius_px + 4, 2)

    if "T" in overlays:
        draw_overlay_targets(surface, tick_data, cam_x, cam_y, zoom)
    if "V" in overlays:
        draw_overlay_velocity(surface, tick_data, cam_x, cam_y, zoom)
    if "H" in overlays:
        draw_overlay_hp(surface, tick_data, cam_x, cam_y, zoom, collision_radius)
    if "B" in overlays:
        draw_overlay_bbox(surface, tick_data, faction_colors, cam_x, cam_y, zoom)


def draw_controls(surface, font, font_type, current_idx, total, playing, speed_idx,
                  tick_data, overlays):
    cy = MAP_AREA_H
    pygame.draw.rect(surface, CONTROLS_BG, (0, cy, WINDOW_W, CONTROLS_H))

    bar_x = SCRUBBER_PAD_X
    bar_y = cy + SCRUBBER_Y_OFF
    bar_w = WINDOW_W - SCRUBBER_PAD_X * 2
    pygame.draw.rect(surface, SCRUBBER_BG, (bar_x, bar_y, bar_w, SCRUBBER_H), border_radius=4)
    if total > 1:
        fill_w = int(bar_w * current_idx / (total - 1))
        if fill_w > 0:
            pygame.draw.rect(surface, SCRUBBER_FG, (bar_x, bar_y, fill_w, SCRUBBER_H), border_radius=4)
    thumb_x = bar_x + int(bar_w * current_idx / max(total - 1, 1))
    pygame.draw.circle(surface, (200, 220, 255), (thumb_x, bar_y + SCRUBBER_H // 2), 7)

    tick_num = tick_data["tick"]
    total_ms = sum(tick_data.get("subsystem_ms", {}).values())
    state_str = ">" if playing else "||"
    speed_str = f"{SPEEDS[speed_idx]:g}x"
    active_overlays = " ".join(sorted(overlays)) if overlays else "none"
    render_text(surface, font, font_type,
                f"{state_str}  tick {tick_num} / {total}  |  {speed_str}  |  {total_ms:.1f}ms  |"
                f"  overlays [{active_overlays}]  V T D H G B toggle  R reset  F focus  ESC quit",
                (bar_x, cy + 28))


def draw_inspector(surface, font, font_type, tick_data, selected_uid, faction_names):
    iy = MAP_AREA_H + CONTROLS_H
    pygame.draw.rect(surface, INSPECTOR_BG, (0, iy, WINDOW_W, INSPECTOR_H))
    pygame.draw.line(surface, INSPECTOR_BORDER, (0, iy), (WINDOW_W, iy))

    pad = SCRUBBER_PAD_X

    if selected_uid is None:
        render_text(surface, font, font_type, "click a unit to inspect", (pad, iy + 14), DIM_COLOR)
        return

    unit = find_unit(tick_data, selected_uid)
    if unit is None:
        render_text(surface, font, font_type, f"UID {selected_uid} — dead this tick", (pad, iy + 14), DIM_COLOR)
        return

    faction_name = faction_names.get(unit["faction"], str(unit["faction"]))
    ability_str = ABILITY_STATES.get(unit.get("ability_state", 0), "unknown")
    vx = unit.get("vx", 0.0)
    vy = unit.get("vy", 0.0)
    speed = math.hypot(vx, vy)

    tgt_uid = unit.get("target_uid", -1)
    if tgt_uid >= 0:
        tgt = find_unit(tick_data, tgt_uid)
        if tgt:
            dist = math.hypot(unit["x"] - tgt["x"], unit["y"] - tgt["y"])
            tgt_str = f"{tgt_uid} ({tgt['type']}, {dist:.0f}wu)"
        else:
            tgt_str = f"{tgt_uid} (dead)"
    else:
        tgt_str = "none"

    render_text(surface, font, font_type,
                f"UID: {unit['uid']}    Type: {unit['type']}    Faction: {faction_name}    Layer: {unit.get('layer', 0)}",
                (pad, iy + 10))
    render_text(surface, font, font_type,
                f"Pos: ({unit['x']:.1f}, {unit['y']:.1f})    Vel: ({vx:.1f}, {vy:.1f})    Speed: {speed:.1f} wu/s",
                (pad, iy + 30))
    render_text(surface, font, font_type,
                f"HP: {unit['hp']} / {unit['max_hp']}    Target: {tgt_str}    Ability: {ability_str}",
                (pad, iy + 50))


def render_text(surface, font, font_type, text, pos, color=TEXT_COLOR):
    if font_type == "freetype":
        font.render_to(surface, pos, text, color)
    elif font_type == "basic":
        surf = font.render(text, True, color)
        surface.blit(surf, pos)
    elif font_type == "pil" and _has_pil:
        w = max(10, len(text) * 8 + 8)
        img = Image.new("RGBA", (w, 20), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((2, 2), text, fill=(*color, 255))
        surface.blit(pygame.image.fromstring(img.tobytes(), img.size, "RGBA"), pos)


def tick_from_scrubber_x(mx, total):
    bar_x = SCRUBBER_PAD_X
    bar_w = WINDOW_W - SCRUBBER_PAD_X * 2
    frac = max(0.0, min(1.0, (mx - bar_x) / bar_w))
    return int(frac * (total - 1))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sim_viewer.py <dump.jsonl>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    header, ticks = load_dump(path)

    map_w = header["map"]["width"]
    map_h = header["map"]["height"]
    map_name = header["map"].get("name", "unknown")
    scenario = header.get("scenario", path)
    collision_radius = header.get("config", {}).get("UNIT_COLLISION_RADIUS", 15)
    tick_duration = header.get("tick_duration_seconds", 0.05)

    faction_colors = {}
    faction_names = {}
    for fid_str, info in header.get("factions", {}).items():
        fid = int(fid_str)
        faction_colors[fid] = hex_to_rgb(info["color"])
        faction_names[fid] = info["name"]

    pygame.init()

    font = None
    font_type = None

    if _has_freetype:
        try:
            import os
            pygame.freetype.init()
            bundled = os.path.join(os.path.dirname(pygame.__file__), "freesansbold.ttf")
            if os.path.exists(bundled):
                font = pygame.freetype.Font(bundled, 13)
                font_type = "freetype"
        except Exception:
            pass

    if font is None and _has_pil:
        font = None
        font_type = "pil"

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(f"sim_viewer — {scenario}  [{map_name} {map_w}×{map_h}]  {len(ticks)} ticks")
    clock = pygame.time.Clock()

    zoom = fit_zoom(map_w, map_h)
    cam_x = map_w / 2.0
    cam_y = map_h / 2.0

    current_idx = 0
    playing = False
    speed_idx = DEFAULT_SPEED_IDX
    accum = 0.0
    total = len(ticks)
    overlays = {"T", "D", "H", "B", "V"}

    selected_uid = None
    scrubbing = False
    panning = False
    pan_last_sx = 0
    pan_last_sy = 0
    drag_moved = False

    OVERLAY_KEYS = {
        pygame.K_v: "V",
        pygame.K_t: "T",
        pygame.K_d: "D",
        pygame.K_h: "H",
        pygame.K_g: "G",
        pygame.K_b: "B",
    }

    running = True
    while running:
        dt_real = clock.tick(60) / 1000.0

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
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_EQUALS, pygame.K_PLUS):
                    speed_idx = min(len(SPEEDS) - 1, speed_idx + 1)
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_MINUS):
                    speed_idx = max(0, speed_idx - 1)
                elif event.key == pygame.K_r:
                    zoom = fit_zoom(map_w, map_h)
                    cam_x = map_w / 2.0
                    cam_y = map_h / 2.0
                elif event.key == pygame.K_f and selected_uid is not None:
                    unit = find_unit(ticks[current_idx], selected_uid)
                    if unit:
                        cam_x = unit["x"]
                        cam_y = unit["y"]
                elif event.key in OVERLAY_KEYS:
                    key = OVERLAY_KEYS[event.key]
                    if key in overlays:
                        overlays.remove(key)
                    else:
                        overlays.add(key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if my >= MAP_AREA_H and my < MAP_AREA_H + CONTROLS_H:
                    scrubbing = True
                    playing = False
                    current_idx = tick_from_scrubber_x(mx, total)
                elif my < MAP_AREA_H and event.button == 1:
                    panning = True
                    drag_moved = False
                    pan_last_sx, pan_last_sy = mx, my

            elif event.type == pygame.MOUSEBUTTONUP:
                scrubbing = False
                if event.button == 1:
                    mx, my = event.pos
                    if panning and not drag_moved and my < MAP_AREA_H:
                        uid = pick_unit(ticks[current_idx], mx, my, cam_x, cam_y, zoom)
                        selected_uid = uid
                    panning = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if scrubbing:
                    current_idx = tick_from_scrubber_x(mx, total)
                elif panning:
                    ddx = mx - pan_last_sx
                    ddy = my - pan_last_sy
                    if abs(ddx) > 2 or abs(ddy) > 2:
                        drag_moved = True
                    cam_x -= ddx / zoom
                    cam_y -= ddy / zoom
                    pan_last_sx, pan_last_sy = mx, my

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if my < MAP_AREA_H:
                    factor = ZOOM_STEP if event.y > 0 else 1.0 / ZOOM_STEP
                    cam_x, cam_y, zoom = zoom_toward(cam_x, cam_y, zoom, mx, my, factor)

        if playing:
            accum += dt_real * SPEEDS[speed_idx]
            ticks_to_advance = int(accum / tick_duration)
            if ticks_to_advance > 0:
                accum -= ticks_to_advance * tick_duration
                current_idx += ticks_to_advance
                if current_idx >= total:
                    current_idx = total - 1
                    playing = False

        draw_map(screen, ticks[current_idx], faction_colors, cam_x, cam_y, zoom,
                 collision_radius, selected_uid, overlays, map_w, map_h)
        draw_controls(screen, font, font_type, current_idx, total, playing, speed_idx,
                      ticks[current_idx], overlays)
        draw_inspector(screen, font, font_type, ticks[current_idx], selected_uid, faction_names)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
