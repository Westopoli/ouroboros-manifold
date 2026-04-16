"""
Archetype compatibility filter language for map layout selection.

Each archetype has:
  - a filter spec (tree of primitives + operators)
  - a FairnessTargetProfile (per-metric target ratio + tolerance)

evaluate_filter(filter_spec, layout_spec) -> bool
matching_layouts(archetype, layout_library)  -> list[LayoutSpec]
"""
from dataclasses import dataclass
import config
from map_gen_contracts import LayoutSpec


# ── Fairness target profiles ──────────────────────────────────────────────────

@dataclass(frozen=True)
class FairnessTargetProfile:
    # Each field: (target_ratio, tolerance)
    # ratio = player_value / enemy_value; passes iff abs(measured - target) <= tolerance
    path_balance:         tuple[float, float]
    travel_time_balance:  tuple[float, float]
    vantage_balance:      tuple[float, float]
    hazard_balance:       tuple[float, float]
    archetype:            str

_SYMMETRIC_DEFAULT = lambda name: FairnessTargetProfile(
    path_balance        = (1.0, 0.15),
    travel_time_balance = (1.0, 0.15),
    vantage_balance     = (1.0, 0.15),
    hazard_balance      = (1.0, 0.15),
    archetype           = name,
)

FAIRNESS_PROFILES: dict[str, FairnessTargetProfile] = {
    "defensive_stand": FairnessTargetProfile(
        path_balance        = (0.60, 0.15),   # fewer enemy ingress routes
        travel_time_balance = (1.00, 0.15),
        vantage_balance     = (1.15, 0.15),   # defender slight vantage edge
        hazard_balance      = (0.75, 0.15),   # hazards along enemy approach
        archetype           = "defensive_stand",
    ),
    "assault": FairnessTargetProfile(
        path_balance        = (1.70, 0.20),   # inverse: attacker paths matter
        travel_time_balance = (1.00, 0.15),
        vantage_balance     = (0.85, 0.15),
        hazard_balance      = (1.30, 0.20),   # hazards in defender zone
        archetype           = "assault",
    ),
    "multi_front_defense": FairnessTargetProfile(
        path_balance        = (1.00, 0.15),
        travel_time_balance = (1.00, 0.15),
        vantage_balance     = (1.00, 0.15),
        hazard_balance      = (1.00, 0.15),
        archetype           = "multi_front_defense",
    ),
    "counterinsurgency": FairnessTargetProfile(
        path_balance        = (1.00, 0.25),   # wide tolerance — dispersed enemy
        travel_time_balance = (1.00, 0.20),
        vantage_balance     = (1.20, 0.20),   # player has sensor/vantage edge
        hazard_balance      = (0.60, 0.20),   # interference clusters near enemy
        archetype           = "counterinsurgency",
    ),
    # Non-prototype archetypes: symmetric default until Stage 7.5 scripts land
    "siege_breaking":   _SYMMETRIC_DEFAULT("siege_breaking"),
    "reconquest":       _SYMMETRIC_DEFAULT("reconquest"),
    "suppression":      _SYMMETRIC_DEFAULT("suppression"),
    "evacuation":       _SYMMETRIC_DEFAULT("evacuation"),
    "raid":             _SYMMETRIC_DEFAULT("raid"),
    "rear_guard":       _SYMMETRIC_DEFAULT("rear_guard"),
}


# ── Reinforcement ownership baselines (Stage 7.5) ────────────────────────────
# Each entry: (player_share, neutral_share, enemy_share) at region state 50/50.
# The S7-5 delta math in map_generator._assign_reinforcement_ownership applies
# OWNERSHIP_MILITARY_COEFF and OWNERSHIP_TENSION_COEFF on top of these baselines.
# Non-prototype archetypes use config.SCRIPT_FALLBACK_OWNERSHIP.

BASELINE_OWNERSHIP: dict[str, tuple[float, float, float]] = {
    # Player holds more territory; enemy has a foothold — attacker scenario.
    "defensive_stand":   (0.50, 0.20, 0.30),
    # Enemy holds most territory; player attacking in — assault scenario.
    "assault":           (0.30, 0.20, 0.50),
    # Player holds majority; multi-vector enemy pressure — defense scenario.
    "multi_front_defense": (0.50, 0.20, 0.30),
    # Player's own territory; neutral infrastructure dominant — insurgency.
    "counterinsurgency": (0.30, 0.50, 0.20),
}

def get_baseline_ownership(archetype: str) -> tuple[float, float, float]:
    """Return (player, neutral, enemy) baseline for the given archetype.
    Falls back to config.SCRIPT_FALLBACK_OWNERSHIP for non-prototype archetypes.
    """
    return BASELINE_OWNERSHIP.get(archetype, config.SCRIPT_FALLBACK_OWNERSHIP)


# ── Filter primitives ─────────────────────────────────────────────────────────

def _count_zone_type(layout: LayoutSpec, node_type: str) -> int:
    return sum(1 for z in layout.zones if z.node_type == node_type)


def _count_edge_type(layout: LayoutSpec, edge_type: str) -> int:
    return sum(1 for e in layout.edges if e.edge_type == edge_type)


def _has_zone_with_property(layout: LayoutSpec, key: str, value=None) -> bool:
    for z in layout.zones:
        if key in z.properties:
            if value is None or z.properties[key] == value:
                return True
    return False


def _layer_accessibility_variety(layout: LayoutSpec) -> int:
    """Count distinct layer restriction sets across all zones (proxy for variety)."""
    seen = set()
    for z in layout.zones:
        layers = z.properties.get("layer_restrictions", None)
        seen.add(str(layers))
    return len(seen)


# ── Evaluator ────────────────────────────────────────────────────────────────

def evaluate_filter(f: dict, layout: LayoutSpec) -> bool:
    t = f["type"]

    if t == "count_zone_type":
        count = _count_zone_type(layout, f["node_type"])
        return _compare(count, f["op"], f["n"])

    if t == "count_edge_type":
        count = _count_edge_type(layout, f["edge_type"])
        return _compare(count, f["op"], f["n"])

    if t == "has_zone_with_property":
        return _has_zone_with_property(layout, f["key"], f.get("value"))

    if t == "layer_accessibility_variety":
        variety = _layer_accessibility_variety(layout)
        return _compare(variety, f["op"], f["n"])

    if t == "all_of":
        return all(evaluate_filter(sub, layout) for sub in f["filters"])

    if t == "any_of":
        return any(evaluate_filter(sub, layout) for sub in f["filters"])

    if t == "not":
        return not evaluate_filter(f["filter"], layout)

    raise ValueError(f"Unknown filter type: {t!r}")


def _compare(value, op: str, n) -> bool:
    if op == ">=": return value >= n
    if op == "<=": return value <= n
    if op == "==": return value == n
    if op == ">":  return value > n
    if op == "<":  return value < n
    raise ValueError(f"Unknown op: {op!r}")


# ── Filter helpers ────────────────────────────────────────────────────────────

def _zone_gte(node_type, n):
    return {"type": "count_zone_type", "node_type": node_type, "op": ">=", "n": n}

def _edge_gte(edge_type, n):
    return {"type": "count_edge_type", "edge_type": edge_type, "op": ">=", "n": n}

def _all(*filters):
    return {"type": "all_of", "filters": list(filters)}

def _any(*filters):
    return {"type": "any_of", "filters": list(filters)}

def _not(f):
    return {"type": "not", "filter": f}

def _has_prop(key, value=None):
    d = {"type": "has_zone_with_property", "key": key}
    if value is not None:
        d["value"] = value
    return d


# ── Archetype filter definitions ──────────────────────────────────────────────

# Reading discipline: filter rules translate the map character prose directly.
# See bible_missions.md per-archetype "Map character" sections.

ARCHETYPE_FILTERS: dict[str, dict] = {

    # --- Prototype archetypes (full filters) ---

    # Defensible terrain. Chokepoints between enemy approach vectors and objective.
    # Multiple approach routes. Player starts in position; enemy approaches.
    # Bible rule: "at least one flank route per chokepoint to prevent pure-grind maps."
    "defensive_stand": _all(
        _zone_gte("staging", 1),
        _zone_gte("chokepoint", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
        _edge_gte("path", 3),          # multiple approach routes
        _zone_gte("flank_route", 1),   # bible: generation rules require at least one flank route
    ),

    # Enemy territory. Fortified chokepoints. Multiple approach vectors with
    # different risk/reward — frontal + flanking route + exposed Raider path.
    "assault": _all(
        _zone_gte("staging", 1),
        _zone_gte("chokepoint", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
        _zone_gte("flank_route", 1),   # multiple approach vectors, one must be a flank route node
    ),

    # Multiple enemy approach vectors from different directions. Player central.
    # Chokepoints on each front. Interior lines. Wide front.
    "multi_front_defense": _all(
        _zone_gte("staging", 1),
        _zone_gte("chokepoint", 3),    # one per front — need at least 3 fronts
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
        _edge_gte("path", 5),          # multiple corridors
    ),

    # Insurgents hidden in sensor interference zones. Player must locate and
    # engage. Scattered positions. Multiple hazard anchors (sensor interference).
    "counterinsurgency": _all(
        _zone_gte("staging", 1),
        _zone_gte("hazard_zone_anchor", 2),   # scattered interference zones
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),

    # --- Non-prototype archetypes (stubs — refined in Stage 7.5) ---
    # Minimum structural requirements only: must have staging, spawn, objective.

    "siege_breaking": _all(
        _zone_gte("staging", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),

    "reconquest": _all(
        _zone_gte("staging", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),

    "suppression": _all(
        _zone_gte("staging", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),

    "evacuation": _all(
        _zone_gte("staging", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),

    "raid": _all(
        _zone_gte("staging", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),

    "rear_guard": _all(
        _zone_gte("staging", 1),
        _zone_gte("spawn_point", 1),
        _zone_gte("objective", 1),
    ),
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_filter(archetype: str) -> dict:
    if archetype not in ARCHETYPE_FILTERS:
        raise KeyError(f"No filter defined for archetype: {archetype!r}")
    return ARCHETYPE_FILTERS[archetype]


def get_fairness_profile(archetype: str) -> FairnessTargetProfile:
    if archetype not in FAIRNESS_PROFILES:
        raise KeyError(f"No fairness profile for archetype: {archetype!r}")
    return FAIRNESS_PROFILES[archetype]


def matching_layouts(archetype: str, layout_library: dict) -> list:
    f = get_filter(archetype)
    return [layout for layout in layout_library.values() if evaluate_filter(f, layout)]
