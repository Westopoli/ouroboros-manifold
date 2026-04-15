import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from layout_library import load_all_layouts
from layout_instantiator import instantiate_layout
from gradient_placer import place_gradients
from tactical_map import TacticalMap, GradientSource, SpineNode
from PIL import Image, ImageDraw

PROPERTIES = ["obstacle_density", "cover_density", "elevation", "sensor_interference"]

PROP_COLORS = {
    "obstacle_density":    (220, 80,  80),
    "cover_density":       (80,  200, 120),
    "elevation":           (230, 200, 50),
    "sensor_interference": (200, 100, 30),
}

NODE_COLORS = {
    "staging":                (80, 200, 120),
    "transit":                (120, 140, 180),
    "chokepoint":             (220, 80,  80),
    "vantage":                (230, 200, 50),
    "hazard_zone_anchor":     (200, 100, 30),
    "objective":              (100, 160, 255),
    "reinforcement_structure":(200, 80,  200),
    "spawn_point":            (200, 60,  60),
    "flank_route":            (100, 200, 170),
    "extraction":             (80,  220, 220),
}

# Expected dominant gradient per node type — used for assertion
EXPECTED_DOMINANT = {
    "chokepoint":         "obstacle_density",
    "staging":            "cover_density",
    "vantage":            "elevation",
    "hazard_zone_anchor": "sensor_interference",
    "flank_route":        None,   # two properties, no single dominant; checked separately
}

SEED = 0x1a2b3c
IMG_SIZE = 400
HEATMAP_GRID = 40   # sample resolution for heatmap


def build_tactical_map(inst, sources):
    tm = TacticalMap(
        width=inst.canvas_w,
        height=inst.canvas_h,
        gradient_sources=sources,
        spine_nodes=inst.spine_nodes,
        layers=5,
    )
    return tm


def sample_at_node(tm, node, prop):
    x, y = node.position
    return getattr(tm, prop)(x, y)


def draw_heatmap_overlay(inst, tm, prop, img_size=IMG_SIZE, margin=20):
    W, H = img_size, img_size
    CW, CH = inst.canvas_w, inst.canvas_h
    img = Image.new("RGB", (W, H), (18, 18, 24))
    draw = ImageDraw.Draw(img)

    # Draw gradient heatmap
    step = img_size // HEATMAP_GRID
    prop_fn = getattr(tm, prop)
    base_color = PROP_COLORS[prop]
    for gy in range(HEATMAP_GRID):
        for gx in range(HEATMAP_GRID):
            cx = (gx + 0.5) / HEATMAP_GRID * CW
            cy = (gy + 0.5) / HEATMAP_GRID * CH
            val = prop_fn(cx, cy)
            alpha = int(val * 200)
            r = min(255, int(base_color[0] * val + 18 * (1 - val)))
            g = min(255, int(base_color[1] * val + 18 * (1 - val)))
            b = min(255, int(base_color[2] * val + 18 * (1 - val)))
            px0 = margin + int(gx / HEATMAP_GRID * (W - 2 * margin))
            py0 = margin + int(gy / HEATMAP_GRID * (H - 2 * margin))
            px1 = margin + int((gx + 1) / HEATMAP_GRID * (W - 2 * margin))
            py1 = margin + int((gy + 1) / HEATMAP_GRID * (H - 2 * margin))
            draw.rectangle([px0, py0, px1, py1], fill=(r, g, b))

    def to_px(x, y):
        return (int(margin + (x / CW) * (W - 2 * margin)),
                int(margin + (y / CH) * (H - 2 * margin)))

    # Draw spine nodes on top
    for node in inst.spine_nodes:
        px, py = to_px(*node.position)
        color = NODE_COLORS.get(node.node_type, (180, 180, 180))
        r = 4
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)
        draw.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=1)

    return img


def make_layout_heatmap_sheet(inst, tm, layout_id, out_path):
    lh = 22
    w, h = IMG_SIZE, IMG_SIZE
    sheet = Image.new("RGB", (len(PROPERTIES) * w, h + lh), (10, 10, 16))
    draw = ImageDraw.Draw(sheet)
    for i, prop in enumerate(PROPERTIES):
        thumb = draw_heatmap_overlay(inst, tm, prop)
        sheet.paste(thumb, (i * w, 0))
        draw.rectangle([i * w, h, (i + 1) * w, h + lh], fill=(22, 22, 32))
        draw.text((i * w + 6, h + 4), prop, fill=PROP_COLORS[prop])
    sheet.save(out_path)


def main():
    print("=== Stage 7 Checkpoint E: Gradient Placer ===\n")

    library = load_all_layouts()
    anomalies = []

    for layout_id in sorted(library.keys()):
        layout = library[layout_id]
        inst = instantiate_layout(layout, "medium", SEED)
        sources = place_gradients(inst)
        tm = build_tactical_map(inst, sources)

        # Count sources by property
        counts = {p: 0 for p in PROPERTIES}
        for s in sources:
            if s.property_type in counts:
                counts[s.property_type] += 1

        print(f"{layout_id}")
        print(f"  sources: total={len(sources)}  " +
              "  ".join(f"{p.split('_')[0]}={counts[p]}" for p in PROPERTIES))

        # Sample at each spine node and check expected dominance
        node_issues = []
        for node in inst.spine_nodes:
            nt = node.properties.get("zone_id", node.node_type)
            expected = EXPECTED_DOMINANT.get(node.node_type)
            if expected is None:
                continue
            val = sample_at_node(tm, node, expected)
            # Assert the expected property is non-trivially present at its anchor node
            if val < 0.05:
                node_issues.append(f"{nt} ({node.node_type}): {expected}={val:.3f} — too low")

        # flank_route: both obstacle_density and cover_density should be > 0 at node
        for node in inst.spine_nodes:
            if node.node_type == "flank_route":
                zid = node.properties.get("zone_id", "?")
                obs = sample_at_node(tm, node, "obstacle_density")
                cov = sample_at_node(tm, node, "cover_density")
                if obs < 0.05 or cov < 0.05:
                    node_issues.append(
                        f"{zid} (flank_route): obs={obs:.3f} cov={cov:.3f} — expected both > 0"
                    )

        if node_issues:
            for issue in node_issues:
                print(f"  ANOMALY: {issue}")
            anomalies.extend(node_issues)

        # Print sampled values per node type
        for node in inst.spine_nodes:
            if node.node_type in EXPECTED_DOMINANT:
                zid = node.properties.get("zone_id", "?")
                vals = {p: f"{sample_at_node(tm, node, p):.3f}" for p in PROPERTIES}
                print(f"  {zid:<32} ({node.node_type:<20}) "
                      + "  ".join(f"{p[:3]}={vals[p]}" for p in PROPERTIES))

        print()

    if anomalies:
        print(f"ANOMALIES ({len(anomalies)}):")
        for a in anomalies:
            print(f"  {a}")
    else:
        print("No anomalies detected.")

    # PNGs
    out_dir = os.path.join(os.path.dirname(__file__),
                           "tuning_output", "stage7", "checkpoint_e")
    os.makedirs(out_dir, exist_ok=True)

    print()
    for layout_id in sorted(library.keys()):
        layout = library[layout_id]
        inst = instantiate_layout(layout, "medium", SEED)
        sources = place_gradients(inst)
        tm = build_tactical_map(inst, sources)
        out_path = os.path.join(out_dir, f"{layout_id}.png")
        make_layout_heatmap_sheet(inst, tm, layout_id, out_path)
        print(f"  {out_path}")

    print(f"\nCheckpoint E PNGs → {out_dir}")


if __name__ == "__main__":
    main()
