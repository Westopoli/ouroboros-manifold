import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import math
import hashlib

from layout_library import load_all_layouts
from layout_instantiator import instantiate_layout, edge_length
from PIL import Image, ImageDraw

CANVAS_SIZES_ORDER = ["small", "medium", "large"]
TEST_LAYOUT_ID = "layout_01_fortress_ridge"
TEST_SEEDS = [0x1a2b3c, 0xdeadbe, 0x7f00aa, 0x000001, 0xffffff]

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


def inst_fingerprint(inst):
    positions = sorted(
        (n.properties.get("zone_id", "?"), round(n.position[0], 1), round(n.position[1], 1))
        for n in inst.spine_nodes
    )
    return hashlib.md5(str(positions).encode()).hexdigest()[:12]


def draw_inst_png(inst, img_size=(400, 400), margin=30):
    img = Image.new("RGB", img_size, (18, 18, 24))
    draw = ImageDraw.Draw(img)

    W, H = img_size
    CW, CH = inst.canvas_w, inst.canvas_h

    def to_px(x, y):
        px = int(margin + (x / CW) * (W - 2 * margin))
        py = int(margin + (y / CH) * (H - 2 * margin))
        return px, py

    for edge in inst.edges:
        n1 = inst.node_id_map.get(edge.from_zone)
        n2 = inst.node_id_map.get(edge.to_zone)
        if n1 and n2:
            draw.line([to_px(*n1.position), to_px(*n2.position)],
                      fill=EDGE_COLORS.get(edge.edge_type, (120, 120, 120)), width=1)

    for node in inst.spine_nodes:
        px, py = to_px(*node.position)
        color = NODE_COLORS.get(node.node_type, (180, 180, 180))
        r = 5
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)

    # canvas border
    draw.rectangle([margin, margin, W - margin, H - margin],
                   outline=(40, 40, 60), width=1)

    return img


def make_canvas_size_sheet(library, layout_id, seed, out_path):
    layout = library[layout_id]
    sizes = CANVAS_SIZES_ORDER
    img_w, img_h, lh = 400, 400, 22
    sheet = Image.new("RGB", (len(sizes) * img_w, img_h + lh), (10, 10, 16))
    draw = ImageDraw.Draw(sheet)

    for i, cs in enumerate(sizes):
        inst = instantiate_layout(layout, cs, seed)
        thumb = draw_inst_png(inst, (img_w, img_h))
        sheet.paste(thumb, (i * img_w, 0))
        draw.rectangle([i * img_w, img_h, (i + 1) * img_w, img_h + lh], fill=(22, 22, 32))
        label = f"{layout_id}  [{cs}]  seed={hex(seed)}"
        draw.text((i * img_w + 6, img_h + 4), label, fill=(160, 160, 190))

    sheet.save(out_path)


def make_seed_variety_sheet(library, layout_id, canvas_size, seeds, out_path):
    layout = library[layout_id]
    img_w, img_h, lh = 320, 320, 22
    cols = len(seeds)
    sheet = Image.new("RGB", (cols * img_w, img_h + lh), (10, 10, 16))
    draw = ImageDraw.Draw(sheet)

    for i, seed in enumerate(seeds):
        inst = instantiate_layout(layout, canvas_size, seed)
        thumb = draw_inst_png(inst, (img_w, img_h))
        sheet.paste(thumb, (i * img_w, 0))
        draw.rectangle([i * img_w, img_h, (i + 1) * img_w, img_h + lh], fill=(22, 22, 32))
        draw.text((i * img_w + 6, img_h + 4), f"seed={hex(seed)}", fill=(160, 160, 190))

    sheet.save(out_path)


def main():
    print("=== Stage 7 Checkpoint D: Layout Instantiation ===\n")

    library = load_all_layouts()
    layout = library[TEST_LAYOUT_ID]

    # ── Canvas size comparison ──
    BASE_SEED = TEST_SEEDS[0]
    print(f"Layout: {TEST_LAYOUT_ID}  base_seed={hex(BASE_SEED)}\n")
    print(f"{'canvas':<8}  {'dims':^16}  {'zones':>5}  {'min_edge':>10}  {'max_edge':>10}  {'mean_edge':>10}")
    print("-" * 70)
    for cs in CANVAS_SIZES_ORDER:
        inst = instantiate_layout(layout, cs, BASE_SEED)
        lengths = [edge_length(inst, e) for e in inst.edges]
        lengths = [l for l in lengths if l is not None]
        print(f"{cs:<8}  {inst.canvas_w}x{inst.canvas_h:>5}  {len(inst.spine_nodes):>5}  "
              f"{min(lengths):>10.0f}  {max(lengths):>10.0f}  {sum(lengths)/len(lengths):>10.0f}")
    print()

    # ── Per-canvas position sample (medium) ──
    inst_med = instantiate_layout(layout, "medium", BASE_SEED)
    print(f"Zone positions at medium canvas (seed={hex(BASE_SEED)}):")
    print(f"  {'zone_id':<32}  {'node_type':<24}  {'x':>8}  {'y':>8}")
    print(f"  {'-'*32}  {'-'*24}  {'-'*8}  {'-'*8}")
    for node in inst_med.spine_nodes:
        zid = node.properties.get("zone_id", "?")
        print(f"  {zid:<32}  {node.node_type:<24}  {node.position[0]:>8.1f}  {node.position[1]:>8.1f}")
    print()

    # ── Determinism check ──
    print("Determinism check — same seed must produce identical fingerprint:")
    for cs in CANVAS_SIZES_ORDER:
        run1 = inst_fingerprint(instantiate_layout(layout, cs, BASE_SEED))
        run2 = inst_fingerprint(instantiate_layout(layout, cs, BASE_SEED))
        status = "PASS" if run1 == run2 else "FAIL"
        print(f"  {cs:<8}  run1={run1}  run2={run2}  {status}")
    print()

    # ── Seed variety check ──
    print(f"Seed variety — medium canvas, {len(TEST_SEEDS)} seeds:")
    fingerprints = set()
    print(f"  {'seed':<12}  {'fingerprint':<14}  {'unique?'}")
    print(f"  {'-'*12}  {'-'*14}  -------")
    for seed in TEST_SEEDS:
        fp = inst_fingerprint(instantiate_layout(layout, "medium", seed))
        is_new = fp not in fingerprints
        fingerprints.add(fp)
        print(f"  {hex(seed):<12}  {fp:<14}  {'YES' if is_new else 'COLLISION'}")
    print(f"  Distinct layouts: {len(fingerprints)}/{len(TEST_SEEDS)}")
    print()

    # ── Jitter bound verification ──
    print("Jitter bound check — positions within expected range after jitter:")
    import config as cfg
    inst_check = instantiate_layout(layout, "medium", BASE_SEED)
    cw, ch = inst_check.canvas_w, inst_check.canvas_h
    jx = cfg.LAYOUT_JITTER_PERCENT * cw
    jy = cfg.LAYOUT_JITTER_PERCENT * ch
    violations = []
    for zone in layout.zones:
        node = inst_check.node_id_map[zone.zone_id]
        base_x = zone.position_ratio[0] * cw
        base_y = zone.position_ratio[1] * ch
        dx = abs(node.position[0] - base_x)
        dy = abs(node.position[1] - base_y)
        scale = 0.5 if zone.node_type == "chokepoint" else 1.0
        if dx > jx * scale + 1 or dy > jy * scale + 1:  # +1 for float epsilon
            violations.append(zone.zone_id)
    if violations:
        print(f"  FAIL — jitter out of bounds: {violations}")
    else:
        print(f"  PASS — all {len(layout.zones)} zones within ±{cfg.LAYOUT_JITTER_PERCENT*100:.0f}% "
              f"(chokepoints ±{cfg.LAYOUT_JITTER_PERCENT*50:.1f}%)")
    print()

    # ── PNGs ──
    out_dir = os.path.join(os.path.dirname(__file__),
                           "tuning_output", "stage7", "checkpoint_d")
    os.makedirs(out_dir, exist_ok=True)

    path_sizes = os.path.join(out_dir, "canvas_sizes.png")
    make_canvas_size_sheet(library, TEST_LAYOUT_ID, BASE_SEED, path_sizes)
    print(f"Canvas size comparison → {path_sizes}")

    path_seeds = os.path.join(out_dir, "seed_variety.png")
    make_seed_variety_sheet(library, TEST_LAYOUT_ID, "medium", TEST_SEEDS, path_seeds)
    print(f"Seed variety          → {path_seeds}")


if __name__ == "__main__":
    main()
