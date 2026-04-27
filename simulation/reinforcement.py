from dataclasses import dataclass, field
import math
import random
import config
from unit import FIELD_X, FIELD_Y


@dataclass
class ReinforcementStructure:
    structure_uid: int
    position: tuple
    layer: int
    hp: float
    max_hp: float
    owner_faction: int          # -1 = neutral
    capture_progress: float     # 0.0–1.0; resets to 0.0 on ownership flip
    production_timer_sec: float
    production_target_unit_type: str
    capture_radius: float
    _capturing_faction: int = field(default=-1, repr=False)


def step_reinforcement(engine, dt):
    to_remove = []

    for structure in engine.reinforcement_structures:
        if structure.hp <= 0:
            to_remove.append(structure)
            continue

        sx, sy = structure.position
        nearby = engine.map.spatial_hash.query(sx, sy, structure.capture_radius)

        faction_present = set()
        for uid in nearby:
            if not engine.store.alive[uid]:
                continue
            ux = engine.store.data[uid, FIELD_X]
            uy = engine.store.data[uid, FIELD_Y]
            if (ux - sx) ** 2 + (uy - sy) ** 2 <= structure.capture_radius ** 2:
                faction_present.add(int(engine.store.faction[uid]))

        non_owner = faction_present - {structure.owner_faction}

        if not non_owner:
            # abandoned: no capturing-eligible units present
            structure.capture_progress = 0.0
            structure._capturing_faction = -1
        elif len(non_owner) == 1 and structure.owner_faction not in faction_present:
            # uncontested: exactly one non-owner faction, owner absent
            capturing = next(iter(non_owner))
            structure._capturing_faction = capturing
            structure.capture_progress += dt / config.REINFORCEMENT_CAPTURE_DURATION_SEC
            if structure.capture_progress >= 1.0:
                structure.capture_progress = 0.0
                structure.owner_faction = capturing
                structure._capturing_faction = -1
        # else: contested (owner + non-owner, or 2+ non-owner factions) — stall

        if structure.owner_faction != -1:
            structure.production_timer_sec += dt
            power = config.UNIT_POWER_RATINGS.get(
                structure.production_target_unit_type, config.POWER_NORMALIZATION
            )
            prod_time = config.BASE_PRODUCTION_TIME_SEC * (power / config.POWER_NORMALIZATION)
            if structure.production_timer_sec >= prod_time:
                structure.production_timer_sec -= prod_time
                sx, sy = structure.position
                angle = random.random() * math.tau
                dist = random.random() * structure.capture_radius * 0.5
                spawn_x = sx + math.cos(angle) * dist
                spawn_y = sy + math.sin(angle) * dist
                engine.store.spawn(
                    structure.production_target_unit_type,
                    structure.owner_faction,
                    spawn_x, spawn_y,
                    structure.layer,
                )

    for s in to_remove:
        engine.reinforcement_structures.remove(s)


# Counter category for composition reactivity (Strike→Line→Siege→Strike)
_COUNTER = {"Strike": "Line", "Line": "Siege", "Siege": "Strike"}


def select_enemy_unit_type(target_ratio, current_composition, player_composition):
    """
    Adjust enemy production target based on player unit composition (70/15 skew rule).

    target_ratio: dict {category: float} — enemy's intended production share
    current_composition: dict {category: float} — current enemy unit distribution
    player_composition: dict {category: float} — current player unit distribution

    Returns a new target_ratio dict with the skew applied and renormalized.
    Triggers when any player category exceeds COMPOSITION_SKEW_THRESHOLD (0.70).
    Shifts COMPOSITION_SHIFT_MAGNITUDE (0.15) of the total target budget toward
    the counter category, taken proportionally from all non-counter categories.
    """
    result = dict(target_ratio)

    for player_cat, player_frac in player_composition.items():
        if player_frac >= config.COMPOSITION_SKEW_THRESHOLD:
            counter_cat = _COUNTER.get(player_cat)
            if counter_cat is None:
                continue
            shift = config.COMPOSITION_SHIFT_MAGNITUDE
            others_total = sum(v for k, v in result.items() if k != counter_cat)
            if others_total <= 0:
                continue
            scale = (others_total - shift) / others_total
            for cat in list(result):
                if cat != counter_cat:
                    result[cat] = result[cat] * scale
            result[counter_cat] = result.get(counter_cat, 0.0) + shift

    total = sum(result.values())
    if total > 0:
        result = {k: v / total for k, v in result.items()}

    return result
