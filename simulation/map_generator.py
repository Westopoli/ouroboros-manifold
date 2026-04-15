import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from map_gen_contracts import GeneratorInput, MapGenerationResult
from layout_instantiator import instantiate_layout
from gradient_placer import place_gradients
from layer_masks import place_layer_masks
from sim_flavoring import compute_flavoring, apply_flavoring
from fairness_evaluator import evaluate_fairness, is_acceptable
from archetype_filters import matching_layouts
from tactical_map import TacticalMap


def generate_map(generator_input: GeneratorInput, layout_library: dict) -> MapGenerationResult:
    compatible = matching_layouts(generator_input.archetype, layout_library)
    if not compatible:
        raise ValueError(f"No layouts compatible with archetype {generator_input.archetype!r}")

    best_score  = None
    best_result = None

    for attempt in range(config.FAIRNESS_MAX_RETRIES + 1):
        seed = generator_input.seed + attempt
        rng  = random.Random(seed)

        layout = rng.choice(compatible)
        inst   = instantiate_layout(layout, generator_input.canvas_size, seed)

        _assign_reinforcement_ownership(
            inst, generator_input.region_state, random.Random(seed ^ 0xABCD)
        )

        base_sources     = place_gradients(inst)
        deltas           = compute_flavoring(generator_input.region_state)
        flavored_sources = apply_flavoring(base_sources, deltas)
        mask_sources     = place_layer_masks(inst)
        all_sources      = flavored_sources + mask_sources

        score = evaluate_fairness(inst, generator_input.archetype)

        if best_score is None or _pass_count(score) > _pass_count(best_score):
            best_score = score
            best_result = _build_result(inst, layout, all_sources, score, attempt, compatible)

        if is_acceptable(score):
            break

    return best_result


# ── Internals ─────────────────────────────────────────────────────────────────

def _pass_count(score):
    return sum([score.path_balance_pass, score.travel_time_pass,
                score.vantage_pass, score.hazard_pass])


def _assign_reinforcement_ownership(inst, region_state, rng):
    rs = region_state
    player_shift  = config.OWNERSHIP_MILITARY_COEFF * (rs.military - 50) / 50
    neutral_shift = config.OWNERSHIP_TENSION_COEFF  * (rs.tension  - 50) / 50

    p = 0.33 + player_shift - neutral_shift / 2
    e = 0.33 - player_shift - neutral_shift / 2
    n = 0.34 + neutral_shift

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
    tm = TacticalMap(
        width            = inst.canvas_w,
        height           = inst.canvas_h,
        gradient_sources = all_sources,
        spine_nodes      = inst.spine_nodes,
        layers           = config.LAYER_COUNT,
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
