"""
Interactive layout/map viewer. No gradients yet (Checkpoint A scaffolding).
CLI: python -m simulation.map_viewer <layout_json>
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
import math
import argparse

try:
    import pygame
except ImportError:
    print("pygame not installed — run: pip install pygame")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_AVAILABLE = True
except ImportError:
    print("Pillow not installed — run: pip install Pillow")
    sys.exit(1)

from map_gen_contracts import ZoneSpec, EdgeSpec, LayoutSpec
from layout_library import _parse_layout

# ── colors ───────────────────────────────────────────────────────────────────

BG = (18, 18, 24)
NODE_COLORS = {
    "staging":                (80, 200, 120),
    "transit":                (120, 140, 180),
    "chokepoint":             (220, 80,  80),
    "vantage":                (230, 200, 50),
    "hazard_zone_anchor":     (200, 100, 30),
    "objective":              (100, 160, 255),
    "reinforcement_structure":(200, 80, 200),
    "spawn_point":            (200, 60,  60),
    "flank_route":            (100, 200, 170),
    "extraction":             (80,  220, 220),
}
EDGE_COLORS = {
    "path":       (180, 180, 180),
    "flank":      (100, 220, 160),
    "restricted": (220, 120,  60),
}
EDGE_WIDTHS  = {"path": 2, "flank": 2, "restricted": 2}
EDGE_DASHES  = {"path": False, "flank": True, "restricted": True}

NODE_RADIUS = 12
FONT_SIZE   = 13
SMALL_SIZE  = 11
MARGIN      = 60


# ── Pillow text rendering ─────────────────────────────────────────────────────

def _make_font(size):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
    except Exception:
        return ImageFont.load_default()


_FONT       = None
_SMALL_FONT = None


def _get_fonts():
    global _FONT, _SMALL_FONT
    if _FONT is None:
        _FONT       = _make_font(FONT_SIZE)
        _SMALL_FONT = _make_font(SMALL_SIZE)
    return _FONT, _SMALL_FONT


def render_text(text, color, size="normal"):
    font, small = _get_fonts()
    f = font if size == "normal" else small
    # measure
    dummy = Image.new("RGBA", (1, 1))
    dd = ImageDraw.Draw(dummy)
    bbox = dd.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0] + 2
    h = bbox[3] - bbox[1] + 2
    img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((0, -bbox[1]), text, font=f, fill=(*color, 255))
    raw = img.tobytes()
    surf = pygame.image.frombuffer(raw, img.size, "RGBA")
    return surf


def text_size(text, size="normal"):
    font, small = _get_fonts()
    f = font if size == "normal" else small
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0] + 2, bbox[3] - bbox[1] + 2


# ── helpers ───────────────────────────────────────────────────────────────────

def ratio_to_screen(rx, ry, screen_w, screen_h):
    x = int(MARGIN + rx * (screen_w - 2 * MARGIN))
    y = int(MARGIN + ry * (screen_h - 2 * MARGIN))
    return x, y


def draw_dashed_line(surface, color, start, end, width=1, dash=8, gap=6):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    drawing = True
    while pos < length:
        seg = dash if drawing else gap
        next_pos = min(pos + seg, length)
        if drawing:
            p1 = (start[0] + ux * pos,      start[1] + uy * pos)
            p2 = (start[0] + ux * next_pos,  start[1] + uy * next_pos)
            pygame.draw.line(surface, color,
                             (int(p1[0]), int(p1[1])),
                             (int(p2[0]), int(p2[1])), width)
        pos = next_pos
        drawing = not drawing


def node_color(node_type):
    return NODE_COLORS.get(node_type, (200, 200, 200))


# ── main viewer ───────────────────────────────────────────────────────────────

def run_viewer(layout: LayoutSpec, screen_w=960, screen_h=800):
    pygame.init()
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
    pygame.display.set_caption(f"Map Viewer — {layout.name}")
    clock = pygame.time.Clock()

    zone_map = {z.zone_id: z for z in layout.zones}

    def screen_pos(z: ZoneSpec):
        w, h = screen.get_size()
        return ratio_to_screen(z.position_ratio[0], z.position_ratio[1], w, h)

    running = True
    while running:
        w, h = screen.get_size()
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        screen.fill(BG)

        # edges
        for edge in layout.edges:
            z_from = zone_map.get(edge.from_zone)
            z_to   = zone_map.get(edge.to_zone)
            if not z_from or not z_to:
                continue
            p1    = screen_pos(z_from)
            p2    = screen_pos(z_to)
            color = EDGE_COLORS.get(edge.edge_type, (150, 150, 150))
            width = EDGE_WIDTHS.get(edge.edge_type, 1)
            if EDGE_DASHES.get(edge.edge_type):
                draw_dashed_line(screen, color, p1, p2, width)
            else:
                pygame.draw.line(screen, color, p1, p2, width)

        # nodes + zone labels
        hovered_zone = None
        for zone in layout.zones:
            px, py = screen_pos(zone)
            color = node_color(zone.node_type)
            pygame.draw.circle(screen, color, (px, py), NODE_RADIUS)
            pygame.draw.circle(screen, (255, 255, 255), (px, py), NODE_RADIUS, 1)

            if abs(mx - px) <= NODE_RADIUS + 4 and abs(my - py) <= NODE_RADIUS + 4:
                hovered_zone = zone

            lbl = render_text(zone.zone_id, (200, 200, 200), "small")
            screen.blit(lbl, (px + NODE_RADIUS + 3, py - lbl.get_height() // 2))

        # node-type legend
        lx, ly = 8, 8
        for name, col in NODE_COLORS.items():
            pygame.draw.circle(screen, col, (lx + 6, ly + 6), 5)
            lbl = render_text(name, (170, 170, 170), "small")
            screen.blit(lbl, (lx + 15, ly))
            ly += 16

        # edge-type legend
        ly += 6
        for etype, col in EDGE_COLORS.items():
            pygame.draw.line(screen, col, (lx, ly + 6), (lx + 20, ly + 6), 2)
            lbl = render_text(etype, (170, 170, 170), "small")
            screen.blit(lbl, (lx + 24, ly))
            ly += 14

        # hover tooltip
        if hovered_zone:
            lines = [
                f"id: {hovered_zone.zone_id}",
                f"type: {hovered_zone.node_type}",
                f"pos: ({hovered_zone.position_ratio[0]:.2f}, {hovered_zone.position_ratio[1]:.2f})",
            ]
            for k, v in hovered_zone.properties.items():
                lines.append(f"  {k}: {v}")
            tw = max(text_size(l, "small")[0] for l in lines) + 10
            th = len(lines) * 14 + 8
            tx = min(mx + 14, w - tw - 4)
            ty = min(my + 14, h - th - 4)
            pygame.draw.rect(screen, (30, 30, 40),   (tx - 2, ty - 2, tw, th))
            pygame.draw.rect(screen, (80, 80, 100),  (tx - 2, ty - 2, tw, th), 1)
            for i, line in enumerate(lines):
                lbl = render_text(line, (220, 220, 220), "small")
                screen.blit(lbl, (tx + 3, ty + i * 14))

        # title bar
        title_text = (f"{layout.name}  [{layout.canvas_class}]"
                      f"  {len(layout.zones)} zones  {len(layout.edges)} edges")
        title = render_text(title_text, (150, 150, 170), "normal")
        screen.blit(title, (w // 2 - title.get_width() // 2, h - 22))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tactical layout viewer")
    parser.add_argument("layout_json", help="Path to layout JSON file")
    args = parser.parse_args()

    with open(args.layout_json) as f:
        data = json.load(f)
    layout = _parse_layout(data)
    run_viewer(layout)


if __name__ == "__main__":
    main()
