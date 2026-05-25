"""
Per-node-type gradient source placement for the 4 continuous properties:
  obstacle_density, cover_density, elevation, sensor_interference

Rules per node type:
  chokepoint          → obstacle_density   (funnels forces, dense obstruction)
                        + cover_density    (defenders dig in along corridor)
  staging             → cover_density      (defensible entry area)
  vantage             → elevation          (high ground advantage)
  hazard_zone_anchor  → sensor_interference (environmental hazard / obscuring field)
                        + cover_density    (mild — rebels/units hide behind cover
                                            within interference zones per bible)
  objective           → cover_density      (focal point with prepared positions)
  flank_route         → obstacle_density (mild) + cover_density (mild)
                        (hazardous-but-traversable character per bible)
  spawn_point         → (no gradient — pure placement marker per spec)
  reinforcement_structure/transit → (no sources; terrain character comes
                                     from surrounding gradients)

A3 Option B (2026-05-20): chokepoint/objective/hazard_zone_anchor cover
emissions added per bible_world.md:188 — "cover density gradients are placed
in defensible positions and approach corridors."
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
import random

import config
from layout_instantiator import InstantiatedLayout
from tactical_map import GradientSource, Asteroid, AsteroidField


# Cover-emitting node types — matches the set that previously produced cover
# polygons (A3 Option B). Hardcoded here; same set referenced in place_gradients below.
# See leaf-03.ASSUMPTIONS.md for rationale.
_COVER_EMITTING_TYPES = {"chokepoint", "staging", "objective", "hazard_zone_anchor", "flank_route"}

# Map each cover-emitting type to its config radius constant name.
# staging reuses GRADIENT_STAGING_RADIUS (no separate staging cover radius constant).
_COVER_RADIUS_ATTR_BY_TYPE = {
    "chokepoint":         "GRADIENT_CHOKEPOINT_COVER_RADIUS",
    "staging":            "GRADIENT_STAGING_RADIUS",
    "hazard_zone_anchor": "GRADIENT_HAZARD_COVER_RADIUS",
    "objective":          "GRADIENT_OBJECTIVE_COVER_RADIUS",
    "flank_route":        "GRADIENT_FLANK_COVER_RADIUS",
}

_FALLBACK_CLUSTER_RADIUS = 50.0  # used if a config radius constant is absent


def place_asteroid_fields(inst) -> AsteroidField:
    """Generate one asteroid cluster per cover-emitting spine node. Deterministic."""
    all_asteroids: list[Asteroid] = []
    asteroid_id = 0

    for cluster_id, node in enumerate(inst.spine_nodes):
        if node.node_type not in _COVER_EMITTING_TYPES:
            continue

        radius_attr = _COVER_RADIUS_ATTR_BY_TYPE[node.node_type]
        radius = getattr(config, radius_attr, None)
        if radius is None:
            radius = _FALLBACK_CLUSTER_RADIUS

        cx, cy = node.position
        count = int(math.pi * radius ** 2 * config.ASTEROID_BASE_DENSITY)
        rng = random.Random(cluster_id * 1009 + getattr(inst, "map_seed", 0))

        scale_classes = list(config.ASTEROID_SCALE_DISTRIBUTION.keys())
        scale_weights = [config.ASTEROID_SCALE_DISTRIBUTION[k] for k in scale_classes]

        placed = 0
        max_attempts = count * 20
        attempts = 0
        while placed < count and attempts < max_attempts:
            attempts += 1
            scale_class = rng.choices(scale_classes, weights=scale_weights, k=1)[0]
            lo, hi = config.ASTEROID_SCALE_RANGES[scale_class]
            radius_xy = rng.uniform(lo, hi)
            height = radius_xy * rng.uniform(*config.ASTEROID_HEIGHT_RATIO_RANGE)

            # Rejection sample: uniform in disk of cluster radius around node center
            r = radius * math.sqrt(rng.random())
            theta = rng.uniform(0.0, 2.0 * math.pi)
            ax = cx + r * math.cos(theta)
            ay = cy + r * math.sin(theta)

            all_asteroids.append(Asteroid(
                asteroid_id=asteroid_id,
                cluster_id=cluster_id,
                x=ax,
                y=ay,
                radius_xy=radius_xy,
                height=height,
                scale_class=scale_class,
            ))
            asteroid_id += 1
            placed += 1

    return AsteroidField(all_asteroids)


def place_gradients(inst: InstantiatedLayout) -> list[GradientSource]:
    sources: list[GradientSource] = []

    for node in inst.spine_nodes:
        pos = node.position
        nt  = node.node_type

        if nt == "chokepoint":
            sources.append(GradientSource(
                position=pos,
                property_type="obstacle_density",
                radius=config.GRADIENT_CHOKEPOINT_RADIUS,
                intensity=config.GRADIENT_CHOKEPOINT_INTENSITY,
            ))
            # A3 Option B: defenders dig in at chokepoints — prepared cover.
            sources.append(GradientSource(
                position=pos,
                property_type="cover_density",
                radius=config.GRADIENT_CHOKEPOINT_COVER_RADIUS,
                intensity=config.GRADIENT_CHOKEPOINT_COVER_INTENSITY,
            ))

        elif nt == "staging":
            sources.append(GradientSource(
                position=pos,
                property_type="cover_density",
                radius=config.GRADIENT_STAGING_RADIUS,
                intensity=config.GRADIENT_STAGING_INTENSITY,
            ))

        elif nt == "vantage":
            sources.append(GradientSource(
                position=pos,
                property_type="elevation",
                radius=config.GRADIENT_VANTAGE_RADIUS,
                intensity=config.GRADIENT_VANTAGE_INTENSITY,
            ))

        elif nt == "hazard_zone_anchor":
            sources.append(GradientSource(
                position=pos,
                property_type="sensor_interference",
                radius=config.GRADIENT_HAZARD_RADIUS,
                intensity=config.GRADIENT_HAZARD_INTENSITY,
            ))
            # A3 Option B: bible_missions.md counterinsurgency — "hidden in sensor
            # interference zones, behind cover, in defensible pockets." Mild cover
            # overlay within interference zones.
            sources.append(GradientSource(
                position=pos,
                property_type="cover_density",
                radius=config.GRADIENT_HAZARD_COVER_RADIUS,
                intensity=config.GRADIENT_HAZARD_COVER_INTENSITY,
            ))

        elif nt == "objective":
            # A3 Option B: objective is the focal defensible position — prepared
            # cover (defensive_stand "prepared positions", assault "fortified
            # chokepoints, established infrastructure").
            sources.append(GradientSource(
                position=pos,
                property_type="cover_density",
                radius=config.GRADIENT_OBJECTIVE_COVER_RADIUS,
                intensity=config.GRADIENT_OBJECTIVE_COVER_INTENSITY,
            ))

        elif nt == "flank_route":
            # Mild obstacle_density (rough terrain) + mild cover_density
            # (concealment) — makes flanks feel hazardous but passable.
            sources.append(GradientSource(
                position=pos,
                property_type="obstacle_density",
                radius=config.GRADIENT_FLANK_OBSTACLE_RADIUS,
                intensity=config.GRADIENT_FLANK_OBSTACLE_INTENSITY,
            ))
            sources.append(GradientSource(
                position=pos,
                property_type="cover_density",
                radius=config.GRADIENT_FLANK_COVER_RADIUS,
                intensity=config.GRADIENT_FLANK_COVER_INTENSITY,
            ))

        # spawn_point, reinforcement_structure, transit — no sources

    return sources
