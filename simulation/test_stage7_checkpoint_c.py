import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from layout_library import load_all_layouts
from archetype_filters import ARCHETYPE_FILTERS, evaluate_filter

from PIL import Image, ImageDraw

ARCHETYPE_ORDER = [
    "defensive_stand", "assault", "multi_front_defense", "counterinsurgency",
    "siege_breaking", "reconquest", "suppression", "evacuation", "raid", "rear_guard",
]

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
    "path":       (160, 160, 160),
    "flank":      (80, 200, 140),
    "restricted": (200, 110, 50),
}


def draw_layout_thumbnail(layout, size=(280, 220), margin=20):
    img = Image.new("RGB", size, (18, 18, 24))
    draw = ImageDraw.Draw(img)

    def to_px(rx, ry):
        return (int(margin + rx * (size[0] - 2 * margin)),
                int(margin + ry * (size[1] - 2 * margin)))

    zone_map = {z.zone_id: z for z in layout.zones}
    for edge in layout.edges:
        z1 = zone_map.get(edge.from_zone)
        z2 = zone_map.get(edge.to_zone)
        if z1 and z2:
            draw.line([to_px(*z1.position_ratio), to_px(*z2.position_ratio)],
                      fill=EDGE_COLORS.get(edge.edge_type, (120, 120, 120)), width=1)

    for zone in layout.zones:
        px, py = to_px(*zone.position_ratio)
        color = NODE_COLORS.get(zone.node_type, (180, 180, 180))
        r = 5
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)

    return img


def make_contact_sheet(library, out_path, cols=4):
    layouts = list(library.values())
    rows = (len(layouts) + cols - 1) // cols
    tw, th, lh = 300, 220, 26
    sheet = Image.new("RGB", (cols * tw, rows * (th + lh)), (10, 10, 16))
    draw = ImageDraw.Draw(sheet)

    for i, layout in enumerate(layouts):
        col, row = i % cols, i // cols
        ox, oy = col * tw, row * (th + lh)
        sheet.paste(draw_layout_thumbnail(layout, size=(tw, th)), (ox, oy))
        draw.rectangle([ox, oy, ox + tw - 1, oy + th - 1], outline=(50, 50, 70), width=1)
        ly = oy + th
        draw.rectangle([ox, ly, ox + tw, ly + lh], fill=(22, 22, 32))
        draw.text((ox + 5, ly + 5), layout.name, fill=(180, 180, 200))
        draw.text((ox + tw - 68, ly + 5), f"[{layout.canvas_class}]", fill=(90, 110, 130))

    sheet.save(out_path)


def main():
    print("=== Stage 7 Checkpoint C: Full Layout Library + Compatibility Matrix ===\n")

    library = load_all_layouts()
    layout_ids = sorted(library.keys())
    print(f"Layouts loaded: {len(library)}")
    for lid in layout_ids:
        l = library[lid]
        print(f"  {lid:<42} [{l.canvas_class:<6}] zones={len(l.zones):>2}  "
              f"edges={len(l.edges):>2}  tags={list(l.tags)}")
    print()

    # ── 8×10 compatibility matrix ──
    PROTO = {"defensive_stand", "assault", "multi_front_defense", "counterinsurgency"}
    print("8×10 Compatibility Matrix  (P=pass, .=fail)")
    arch_short = [a[:13] for a in ARCHETYPE_ORDER]
    header = f"  {'layout':<42}  " + " ".join(f"{s:<13}" for s in arch_short)
    print(header)
    print("  " + "-" * max(len(header) - 2, 80))

    matrix = {}
    for lid in layout_ids:
        layout = library[lid]
        row = {a: evaluate_filter(ARCHETYPE_FILTERS[a], layout) for a in ARCHETYPE_ORDER}
        matrix[lid] = row
        cols = " ".join(f"{'P' if row[a] else '.':<13}" for a in ARCHETYPE_ORDER)
        print(f"  {lid:<42}  {cols}")
    print()

    # ── Per-archetype coverage ──
    print("Per-archetype coverage:")
    all_ok = True
    for arch in ARCHETYPE_ORDER:
        matching = [lid for lid, row in matrix.items() if row[arch]]
        kind = "prototype" if arch in PROTO else "stub    "
        ok = bool(matching)
        if not ok:
            all_ok = False
        status = "" if ok else "  ← NO COVERAGE"
        print(f"  {arch:<28} ({kind}): {len(matching):>2}  {status}")
        for lid in matching:
            print(f"      {lid}")
    print()

    # ── Cross-pollination ──
    multi = {lid: [a for a in ARCHETYPE_ORDER if matrix[lid][a]] for lid in layout_ids}
    cross_count = sum(1 for v in multi.values() if len(v) >= 2)
    print(f"Cross-pollination (layouts matching ≥2 prototype archetypes): "
          f"{sum(1 for lid in layout_ids if sum(matrix[lid][a] for a in PROTO) >= 2)}/8  "
          f"(≥2 any archetype: {cross_count}/8)")
    for lid in layout_ids:
        a_list = multi[lid]
        proto_list = [a for a in a_list if a in PROTO]
        print(f"  {lid:<42} proto={len(proto_list)}  total={len(a_list)}")
    print()

    # ── Contact sheet ──
    out_dir = os.path.join(os.path.dirname(__file__),
                           "tuning_output", "stage7", "checkpoint_c")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "contact_sheet.png")
    make_contact_sheet(library, out_path)
    print(f"Contact sheet → {out_path}")

    if all_ok:
        print("\nAll prototype archetypes covered. Checkpoint C PASS.")
    else:
        print("\nMissing coverage detected. Checkpoint C FAIL.")


if __name__ == "__main__":
    main()
