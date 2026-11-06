import json
import random
import sys
import os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from map_gen_contracts import GeneratorInput, MapGenerationResult
from layout_instantiator import instantiate_layout
from gradient_placer import place_gradients, place_cover_polygons
from layer_masks import place_layer_masks
from sim_flavoring import compute_flavoring, apply_flavoring
from fairness_evaluator import evaluate_fairness
from archetype_filters import matching_layouts, get_baseline_ownership
from tactical_map import TacticalMap


# See also: docs/legacy/stage_specs/stage_11e_fairness_reconciliation_spec.md — interim simple picker;
# bible's two-layer fairness architecture deferred to stage_11f.
def generate_map(generator_input: GeneratorInput, layout_library: dict) -> MapGenerationResult:
    compatible = matching_layouts(generator_input.archetype, layout_library)
    if not compatible:
        raise ValueError(f"No layouts compatible with archetype {generator_input.archetype!r}")

    seed = generator_input.seed
    rng  = random.Random(seed)

    layout = rng.choice(compatible)
    inst   = instantiate_layout(layout, generator_input.canvas_size, seed)

    _assign_reinforcement_ownership(
        inst, generator_input.region_state, random.Random(seed ^ 0xABCD),
        generator_input.archetype,
    )

    base_sources     = place_gradients(inst)
    deltas           = compute_flavoring(generator_input.region_state)
    flavored_sources = apply_flavoring(base_sources, deltas)
    mask_sources     = place_layer_masks(inst)
    all_sources      = flavored_sources + mask_sources

    score = evaluate_fairness(inst, generator_input.archetype)
    _log_fairness(generator_input, layout, score)

    return _build_result(inst, layout, all_sources, score, 0, compatible)


# ── Internals ─────────────────────────────────────────────────────────────────

_FAIRNESS_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "tuning_output", "fairness_log")


def _log_fairness(generator_input, layout, score):
    try:
        os.makedirs(_FAIRNESS_LOG_DIR, exist_ok=True)
        log_path = os.path.join(_FAIRNESS_LOG_DIR, f"{date.today().isoformat()}.jsonl")
        entry = {
            "archetype": generator_input.archetype,
            "layout_id": layout.layout_id,
            "seed": generator_input.seed,
            "fairness_score": {
                "path_balance_ratio": score.path_balance_ratio,
                "path_balance_pass": score.path_balance_pass,
                "path_balance_skipped": score.path_balance_skipped,
                "travel_time_ratio": score.travel_time_ratio,
                "travel_time_pass": score.travel_time_pass,
                "travel_time_skipped": score.travel_time_skipped,
                "vantage_ratio": score.vantage_ratio,
                "vantage_pass": score.vantage_pass,
                "vantage_skipped": score.vantage_skipped,
                "hazard_ratio": score.hazard_ratio,
                "hazard_pass": score.hazard_pass,
                "hazard_skipped": score.hazard_skipped,
                "all_metrics_pass": score.all_metrics_pass,
            },
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _assign_reinforcement_ownership(inst, region_state, rng, archetype):
    rs = region_state
    base_p, base_n, base_e = get_baseline_ownership(archetype)
    player_shift  = config.OWNERSHIP_MILITARY_COEFF * (rs.military - 50) / 50
    neutral_shift = config.OWNERSHIP_TENSION_COEFF  * (rs.tension  - 50) / 50

    p = base_p + player_shift - neutral_shift / 2
    e = base_e - player_shift - neutral_shift / 2
    n = base_n + neutral_shift

    p = max(0.0, min(1.0, p))
    e = max(0.0, min(1.0, e))
    n = max(0.0, min(1.0, n))
    total = p + e + n
    if total > 0:
        p, e, n = p / total, e / total, n / total
    else:
        p, e, n = 0.33, 0.34, 0.33

    # thresholds: roll < p → player, < p+n → neutral, else → enemy
    p_thresh = p
    n_thresh = p + n

    for node in inst.spine_nodes:
        if node.node_type == "reinforcement_structure":
            roll = rng.random()
            if roll < p_thresh:
                node.properties["initial_owner"] = "player"
            elif roll < n_thresh:
                node.properties["initial_owner"] = "neutral"
            else:
                node.properties["initial_owner"] = "enemy"


def _build_result(inst, layout, all_sources, score, attempt, compatible):
    resolved_edges = []
    for edge in inst.edges:
        na = inst.node_id_map.get(edge.from_zone)
        nb = inst.node_id_map.get(edge.to_zone)
        if na and nb:
            resolved_edges.append((na, nb, edge.edge_type))

    cover_polys = place_cover_polygons(inst)
    tm = TacticalMap(
        width            = inst.canvas_w,
        height           = inst.canvas_h,
        gradient_sources = all_sources,
        spine_nodes      = inst.spine_nodes,
        layers           = config.LAYER_COUNT,
        edges            = resolved_edges,
        cover_polygons   = cover_polys,
    )

    owner_counts = {"player": 0, "neutral": 0, "enemy": 0}
    reinf_count  = 0
    for node in inst.spine_nodes:
        if node.node_type == "reinforcement_structure":
            reinf_count += 1
            owner = node.properties.get("initial_owner", "neutral")
            owner_counts[owner] = owner_counts.get(owner, 0) + 1

    return MapGenerationResult(
        tactical_map      = tm,
        chosen_layout_id  = layout.layout_id,
        fairness_score    = score,
        generation_metadata = {
            "candidate_layouts":            [l.layout_id for l in compatible],
            "fairness_retries":             attempt,
            "gradient_source_count":        len(all_sources),
            "reinforcement_structure_count": reinf_count,
            "reinforcement_ownership":      owner_counts,
        },
    )
