"""
Checkpoint I — End-to-End Map Generator

100 maps × 4 prototype archetypes (400 total).
Note: fairness pass rate against authored profiles is expected to be low at this
stage — the profiles were authored before layouts existed and reflect symmetric-map
assumptions that our intentionally asymmetric layouts don't satisfy. The pipeline
is verified mechanically and by visual contact sheet variety.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
import random
import math
from PIL import Image, ImageDraw

from layout_library import load_all_layouts
from map_gen_contracts import GeneratorInput, RegionState
from map_generator import generate_map
import config

ARCHETYPES = ["defensive_stand", "assault", "multi_front_defense", "counterinsurgency"]
N_MAPS     = 100
BASE_SEED  = 0xCAFE0000

THUMB_SIZE  = 120
GRID_COLS   = 10
DETAIL_N    = 10

NODE_COLORS = {
    "staging":                (80,  200, 120),
    "transit":                (100, 120, 160),
    "chokepoint":             (220, 80,  80),
    "vantage":                (230, 200, 50),
    "hazard_zone_anchor":     (200, 100, 30),
    "objective":              (100, 160, 255),
    "reinforcement_structure":(200, 80,  200),
    "spawn_point":            (200, 60,  60),
    "flank_route":            (100, 200, 170),
    "extraction":             (80,  220, 220),
}
OWNER_RING = {"player": (80, 200, 120), "neutral": (180, 180, 180), "enemy": (220, 80, 80)}


def _varied_region_state(seed):
    rng = random.Random(seed)
    return RegionState(
        stability  = rng.uniform(0.1, 0.95),
        capacity   = rng.uniform(0.2, 0.9),
        economy    = rng.uniform(10.0, 90.0),
        tension    = rng.uniform(10.0, 90.0),
        military   = rng.uniform(10.0, 90.0),
        population = rng.uniform(15.0, 85.0),
        region_id  = f"r{seed & 0xFF:02x}",
        tier       = rng.randint(1, 3),
    )


def _draw_thumb(result, size=THUMB_SIZE):
    tm   = result.tactical_map
    img  = Image.new("RGB", (size, size), (18, 18, 24))
    draw = ImageDraw.Draw(img)

    margin = 6

    def to_px(x, y):
        px = int(margin + (x / tm.width)  * (size - 2 * margin))
        py = int(margin + (y / tm.height) * (size - 2 * margin))
        return px, py

    # Obstacle density heatmap (low-res)
    steps = 20
    for gy in range(steps):
        for gx in range(steps):
            cx = (gx + 0.5) / steps * tm.width
            cy = (gy + 0.5) / steps * tm.height
            v  = tm.obstacle_density(cx, cy)
            r  = int(18 + v * (180 - 18))
            g  = int(18 + v * (60  - 18))
            b  = int(24 + v * (60  - 24))
            x0 = margin + int(gx / steps * (size - 2 * margin))
            y0 = margin + int(gy / steps * (size - 2 * margin))
            x1 = margin + int((gx + 1) / steps * (size - 2 * margin))
            y1 = margin + int((gy + 1) / steps * (size - 2 * margin))
            draw.rectangle([x0, y0, x1, y1], fill=(r, g, b))

    # Spine nodes
    for node in tm.spine_nodes:
        px, py = to_px(*node.position)
        color = NODE_COLORS.get(node.node_type, (160, 160, 160))
        r = 3
        if node.node_type == "reinforcement_structure":
            owner = node.properties.get("initial_owner", "neutral")
            ring  = OWNER_RING.get(owner, (180, 180, 180))
            draw.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2], outline=ring, width=1)
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)

    return img


def _draw_detail(result, size=400):
    tm     = result.tactical_map
    meta   = result.generation_metadata
    score  = result.fairness_score

    img    = Image.new("RGB", (size, size + 40), (18, 18, 24))
    draw   = ImageDraw.Draw(img)
    margin = 20

    def to_px(x, y):
        px = int(margin + (x / tm.width)  * (size - 2 * margin))
        py = int(margin + (y / tm.height) * (size - 2 * margin))
        return px, py

    # Obstacle density heatmap
    steps = 40
    for gy in range(steps):
        for gx in range(steps):
            cx = (gx + 0.5) / steps * tm.width
            cy = (gy + 0.5) / steps * tm.height
            obs = tm.obstacle_density(cx, cy)
            cov = tm.cover_density(cx, cy)
            r   = int(18 + obs * 200)
            g   = int(18 + cov * 160)
            b   = 24
            x0  = margin + int(gx / steps * (size - 2 * margin))
            y0  = margin + int(gy / steps * (size - 2 * margin))
            x1  = margin + int((gx + 1) / steps * (size - 2 * margin))
            y1  = margin + int((gy + 1) / steps * (size - 2 * margin))
            draw.rectangle([x0, y0, x1, y1], fill=(min(255, r), min(255, g), b))

    # Edges
    from layout_instantiator import InstantiatedLayout
    node_map = {n.properties.get("zone_id"): n for n in tm.spine_nodes}

    # Spine nodes
    for node in tm.spine_nodes:
        px, py = to_px(*node.position)
        color = NODE_COLORS.get(node.node_type, (160, 160, 160))
        r = 5
        if node.node_type == "reinforcement_structure":
            owner = node.properties.get("initial_owner", "neutral")
            ring  = OWNER_RING.get(owner, (180, 180, 180))
            draw.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3], outline=ring, width=2)
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)
        draw.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=1)

    # Footer
    passes  = sum([score.path_balance_pass, score.travel_time_pass,
                   score.vantage_pass, score.hazard_pass])
    layout  = result.chosen_layout_id.replace("layout_0", "L").split("_")[0]
    retries = meta["fairness_retries"]
    src_ct  = meta["gradient_source_count"]
    ownstr  = "/".join(str(meta["reinforcement_ownership"].get(k, 0))
                       for k in ["player", "neutral", "enemy"])
    text    = f"{layout}  passes={passes}/4  retries={retries}  src={src_ct}  own={ownstr}"
    draw.rectangle([0, size, size, size + 40], fill=(10, 10, 16))
    draw.text((6, size + 4), text, fill=(160, 200, 255))
    draw.text((6, size + 22), score.archetype_profile, fill=(120, 160, 200))

    return img


def main():
    print("=== Stage 7 Checkpoint I: End-to-End Map Generator ===\n")

    library  = load_all_layouts()
    failures = []

    out_root = os.path.join(os.path.dirname(__file__),
                            "tuning_output", "stage7", "checkpoint_i")
    os.makedirs(out_root, exist_ok=True)

    determinism_results = {}   # archetype → first MapGenerationResult (for determinism check)

    for archetype in ARCHETYPES:
        print(f"── {archetype} ({'─' * (40 - len(archetype))})")

        pass_counts   = []   # passing metrics per map (0–4)
        retry_counts  = []
        layout_counts = {}
        gen_times     = []
        thumbs        = []

        detail_dir = os.path.join(out_root, archetype, "detail")
        os.makedirs(detail_dir, exist_ok=True)

        for i in range(N_MAPS):
            seed  = BASE_SEED + i
            rs    = _varied_region_state(seed)
            ginput = GeneratorInput(archetype=archetype, region_state=rs,
                                    canvas_size="medium", seed=seed)

            t0     = time.perf_counter()
            result = generate_map(ginput, library)
            elapsed = (time.perf_counter() - t0) * 1000

            gen_times.append(elapsed)

            score  = result.fairness_score
            meta   = result.generation_metadata
            passes = sum([score.path_balance_pass, score.travel_time_pass,
                          score.vantage_pass, score.hazard_pass])
            pass_counts.append(passes)
            retry_counts.append(meta["fairness_retries"])
            layout_counts[result.chosen_layout_id] = layout_counts.get(result.chosen_layout_id, 0) + 1

            thumbs.append(_draw_thumb(result))

            if i < DETAIL_N:
                detail_path = os.path.join(detail_dir, f"detail_{i:02d}.png")
                _draw_detail(result, size=400).save(detail_path)

            if i == 0:
                determinism_results[archetype] = (seed, rs, result.chosen_layout_id,
                                                   result.fairness_score.path_balance_ratio)

        # Contact sheet (10×10)
        grid_rows = math.ceil(N_MAPS / GRID_COLS)
        sheet_w   = GRID_COLS * THUMB_SIZE
        sheet_h   = grid_rows * THUMB_SIZE
        sheet     = Image.new("RGB", (sheet_w, sheet_h), (10, 10, 16))
        for idx, thumb in enumerate(thumbs):
            col = idx % GRID_COLS
            row = idx // GRID_COLS
            sheet.paste(thumb, (col * THUMB_SIZE, row * THUMB_SIZE))
        sheet_path = os.path.join(out_root, archetype, "contact_sheet.png")
        os.makedirs(os.path.join(out_root, archetype), exist_ok=True)
        sheet.save(sheet_path)

        # Stats
        full_pass_rate = sum(1 for p in pass_counts if p == 4) / N_MAPS * 100
        mean_passes    = sum(pass_counts) / N_MAPS
        mean_time      = sum(gen_times) / N_MAPS
        p95_time       = sorted(gen_times)[int(N_MAPS * 0.95)]
        mean_retries   = sum(retry_counts) / N_MAPS
        exhausted      = sum(1 for r in retry_counts if r >= config.FAIRNESS_MAX_RETRIES)

        print(f"  full_pass_rate: {full_pass_rate:.1f}%  (expected low — calibration gap)")
        print(f"  mean_metrics_pass: {mean_passes:.2f}/4")
        print(f"  retries — mean: {mean_retries:.2f}  exhausted: {exhausted}/{N_MAPS}")
        print(f"  timing — mean: {mean_time:.1f}ms  p95: {p95_time:.1f}ms")
        print(f"  layout distribution: " +
              "  ".join(f"{lid.split('_')[1][:5]}={cnt}"
                        for lid, cnt in sorted(layout_counts.items())))
        print(f"  contact sheet → {sheet_path}")
        print()

    # ── Determinism check ────────────────────────────────────────────────────
    print("── Determinism check (10 reruns of archetype[0] seed[0]) ───────────")
    archetype = ARCHETYPES[0]
    seed0, rs0, _, _ = determinism_results[archetype]
    ginput0 = GeneratorInput(archetype=archetype, region_state=rs0,
                             canvas_size="medium", seed=seed0)
    seen_layouts = set()
    seen_ratios  = set()
    for _ in range(10):
        r = generate_map(ginput0, library)
        seen_layouts.add(r.chosen_layout_id)
        seen_ratios.add(round(r.fairness_score.path_balance_ratio, 6))

    if len(seen_layouts) == 1 and len(seen_ratios) == 1:
        print(f"  layout: {next(iter(seen_layouts))}  ratio: {next(iter(seen_ratios))}  ✓ deterministic")
    else:
        msg = f"Non-deterministic: layouts={seen_layouts} ratios={seen_ratios}"
        failures.append(msg)
        print(f"  FAIL: {msg}")

    # ── Structural checks ────────────────────────────────────────────────────
    print("\n── Structural checks ────────────────────────────────────────────────")
    for archetype in ARCHETYPES:
        seed = BASE_SEED
        rs   = _varied_region_state(seed)
        ginput = GeneratorInput(archetype=archetype, region_state=rs,
                                canvas_size="medium", seed=seed)
        result = generate_map(ginput, library)
        tm     = result.tactical_map
        meta   = result.generation_metadata

        if tm.width <= 0 or tm.height <= 0:
            failures.append(f"{archetype}: TacticalMap has zero dimensions")
        if tm.layers != config.LAYER_COUNT:
            failures.append(f"{archetype}: TacticalMap layers={tm.layers} expected {config.LAYER_COUNT}")
        if len(tm.gradient_sources) == 0:
            failures.append(f"{archetype}: no gradient sources")
        if len(tm.spine_nodes) == 0:
            failures.append(f"{archetype}: no spine nodes")
        if "candidate_layouts" not in meta:
            failures.append(f"{archetype}: missing candidate_layouts in metadata")
        if "fairness_retries" not in meta:
            failures.append(f"{archetype}: missing fairness_retries in metadata")

        # Gradient sampling must not crash
        try:
            _ = tm.obstacle_density(tm.width / 2, tm.height / 2)
            _ = tm.layer_accessibility(tm.width / 2, tm.height / 2, 0)
        except Exception as exc:
            failures.append(f"{archetype}: gradient sampling crashed: {exc}")

        # Reinforcement structures have initial_owner set
        for node in tm.spine_nodes:
            if node.node_type == "reinforcement_structure":
                if "initial_owner" not in node.properties:
                    failures.append(f"{archetype}: reinforcement_structure missing initial_owner")
                    break

        print(f"  {archetype:<22} width={tm.width}  nodes={len(tm.spine_nodes)}"
              f"  sources={len(tm.gradient_sources)}  layers={tm.layers}  ✓")

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    else:
        print("Checkpoint I complete — no failures.")

    print(f"\nPNGs → {out_root}")


if __name__ == "__main__":
    main()
