import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from layout_library import load_all_layouts
from layout_instantiator import instantiate_layout
from layer_masks import place_layer_masks
from tactical_map import TacticalMap
from PIL import Image, ImageDraw
import config

SEED = 0x1a2b3c
IMG_SIZE = 400
SAMPLE_GRID = 40

ACCESSIBLE_COLOR  = (60, 140, 220)
BLOCKED_COLOR     = (30,  30,  48)
BACKGROUND_COLOR  = (18,  18,  24)

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


def build_map_with_masks(inst, mask_sources):
    return TacticalMap(
        width=inst.canvas_w,
        height=inst.canvas_h,
        gradient_sources=mask_sources,
        spine_nodes=inst.spine_nodes,
        layers=config.LAYER_COUNT,
    )


def draw_layer_overlay(inst, tm, layer, img_size=IMG_SIZE, margin=20):
    W, H = img_size, img_size
    CW, CH = inst.canvas_w, inst.canvas_h
    img = Image.new("RGB", (W, H), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    step_x = (W - 2 * margin) / SAMPLE_GRID
    step_y = (H - 2 * margin) / SAMPLE_GRID

    for gy in range(SAMPLE_GRID):
        for gx in range(SAMPLE_GRID):
            cx = (gx + 0.5) / SAMPLE_GRID * CW
            cy = (gy + 0.5) / SAMPLE_GRID * CH
            accessible = tm.layer_accessibility(cx, cy, layer)
            color = ACCESSIBLE_COLOR if accessible else BLOCKED_COLOR
            px0 = margin + int(gx / SAMPLE_GRID * (W - 2 * margin))
            py0 = margin + int(gy / SAMPLE_GRID * (H - 2 * margin))
            px1 = margin + int((gx + 1) / SAMPLE_GRID * (W - 2 * margin))
            py1 = margin + int((gy + 1) / SAMPLE_GRID * (H - 2 * margin))
            draw.rectangle([px0, py0, px1, py1], fill=color)

    def to_px(x, y):
        return (int(margin + (x / CW) * (W - 2 * margin)),
                int(margin + (y / CH) * (H - 2 * margin)))

    for node in inst.spine_nodes:
        px, py = to_px(*node.position)
        color = NODE_COLORS.get(node.node_type, (180, 180, 180))
        r = 4
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)
        draw.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=1)
        if node.properties.get("layer_restrictions") is not None:
            draw.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3],
                         outline=(255, 220, 0), width=1)

    return img


def make_layer_sheet(inst, tm, layout_id, out_path):
    lh = 22
    w, h = IMG_SIZE, IMG_SIZE
    n = config.LAYER_COUNT
    sheet = Image.new("RGB", (n * w, h + lh), (10, 10, 16))
    draw = ImageDraw.Draw(sheet)
    for layer in range(n):
        thumb = draw_layer_overlay(inst, tm, layer)
        sheet.paste(thumb, (layer * w, 0))
        draw.rectangle([layer * w, h, (layer + 1) * w, h + lh], fill=(22, 22, 32))
        draw.text((layer * w + 6, h + 4), f"layer {layer}", fill=(120, 180, 255))
    sheet.save(out_path)


def main():
    print("=== Stage 7 Checkpoint F: Layer Accessibility Masks ===\n")

    library = load_all_layouts()
    failures = []

    for layout_id in sorted(library.keys()):
        layout = library[layout_id]
        inst = instantiate_layout(layout, "medium", SEED)
        mask_sources = place_layer_masks(inst)
        tm = build_map_with_masks(inst, mask_sources)

        # Summarise which zones carry restrictions
        restricted_zones = [
            (n.properties.get("zone_id", n.node_type), n.node_type,
             n.properties["layer_restrictions"])
            for n in inst.spine_nodes
            if n.properties.get("layer_restrictions") is not None
        ]
        zone_ids = [n.properties.get("zone_id", "?") for n in inst.spine_nodes
                    if n.properties.get("layer_restrictions") is not None]

        print(f"{layout_id}")
        if restricted_zones:
            for zid, nt, restr in restricted_zones:
                blocked = sorted(set(range(config.LAYER_COUNT)) - set(restr))
                print(f"  {zid} ({nt}): accessible={restr}  blocked={blocked}")
        else:
            print(f"  (no layer restrictions — all zones default all-accessible)")

        # Sample grid pass rates per layer
        total_cells = SAMPLE_GRID * SAMPLE_GRID
        CW, CH = inst.canvas_w, inst.canvas_h
        layer_pass = [0] * config.LAYER_COUNT
        for gy in range(SAMPLE_GRID):
            for gx in range(SAMPLE_GRID):
                cx = (gx + 0.5) / SAMPLE_GRID * CW
                cy = (gy + 0.5) / SAMPLE_GRID * CH
                for layer in range(config.LAYER_COUNT):
                    if tm.layer_accessibility(cx, cy, layer):
                        layer_pass[layer] += 1

        pass_rates = [layer_pass[l] / total_cells for l in range(config.LAYER_COUNT)]
        rate_str = "  ".join(f"L{l}={pass_rates[l]*100:.1f}%" for l in range(config.LAYER_COUNT))
        print(f"  pass rates: {rate_str}")

        # Assertions: verify restrictions are honoured at the restricting nodes
        for node in inst.spine_nodes:
            restr = node.properties.get("layer_restrictions")
            if restr is None:
                continue
            zid = node.properties.get("zone_id", node.node_type)
            x, y = node.position
            accessible_set = set(restr)
            blocked_set = set(range(config.LAYER_COUNT)) - accessible_set
            for layer in blocked_set:
                if tm.layer_accessibility(x, y, layer):
                    msg = f"{zid}: layer {layer} should be blocked at node but is accessible"
                    failures.append(msg)
                    print(f"  FAIL: {msg}")
            for layer in accessible_set:
                if not tm.layer_accessibility(x, y, layer):
                    msg = f"{zid}: layer {layer} should be accessible at node but is blocked"
                    failures.append(msg)
                    print(f"  FAIL: {msg}")

        # Assert default zones (no restrictions) are accessible on all layers
        for node in inst.spine_nodes:
            if node.properties.get("layer_restrictions") is not None:
                continue
            zid = node.properties.get("zone_id", node.node_type)
            x, y = node.position
            for layer in range(config.LAYER_COUNT):
                if not tm.layer_accessibility(x, y, layer):
                    msg = f"{zid}: layer {layer} blocked at unrestricted node"
                    failures.append(msg)
                    print(f"  FAIL: {msg}")

        print()

    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    else:
        print("All layer restriction assertions passed.")

    # PNGs
    out_dir = os.path.join(os.path.dirname(__file__),
                           "tuning_output", "stage7", "checkpoint_f")
    os.makedirs(out_dir, exist_ok=True)

    print()
    for layout_id in sorted(library.keys()):
        layout = library[layout_id]
        inst = instantiate_layout(layout, "medium", SEED)
        mask_sources = place_layer_masks(inst)
        tm = build_map_with_masks(inst, mask_sources)
        out_path = os.path.join(out_dir, f"{layout_id}.png")
        make_layer_sheet(inst, tm, layout_id, out_path)
        print(f"  {out_path}")

    print(f"\nCheckpoint F PNGs → {out_dir}")


if __name__ == "__main__":
    main()
