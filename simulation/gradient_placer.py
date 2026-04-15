"""
Per-node-type gradient source placement for the 4 continuous properties:
  obstacle_density, cover_density, elevation, sensor_interference

Rules per node type:
  chokepoint          → obstacle_density   (funnels forces, dense obstruction)
  staging             → cover_density      (defensible entry area)
  vantage             → elevation          (high ground advantage)
  hazard_zone_anchor  → sensor_interference (environmental hazard / obscuring field)
  flank_route         → obstacle_density (mild) + cover_density (mild)
                        (hazardous-but-traversable character per bible)
  spawn_point         → (no gradient — pure placement marker per spec)
  objective/reinforcement_structure/transit → (no sources; terrain character comes
                                               from surrounding gradients)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from layout_instantiator import InstantiatedLayout
from tactical_map import GradientSource


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

        # spawn_point, objective, reinforcement_structure, transit — no sources

    return sources
