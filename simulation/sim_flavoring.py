"""
Region state → per-property gradient intensity deltas.

compute_flavoring(region_state) returns a FlavoringDeltas with a signed additive
delta for each of the 4 continuous gradient properties.  The map generator adds
these deltas to the base intensities from gradient_placer.py, then clamps to [0,1].

Field mapping:
  stability (0-1):  instability = 1 - stability
                    → +sensor_interference (degraded environment)
                    → +cover_density (improvised fortification)
  capacity  (0-1):  → -obstacle_density (open, developed terrain)
  economy   (0-100): high → -obstacle_density (cleared infrastructure)
  tension   (0-100): high → +cover_density (entrenched positions)
  military  (0-100): high → +obstacle_density (defensive emplacements)
  population(0-100): above/below midpoint scales all density up/down
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataclasses import dataclass
import config
from map_gen_contracts import RegionState


@dataclass
class FlavoringDeltas:
    obstacle_density:    float
    cover_density:       float
    elevation:           float
    sensor_interference: float


def compute_flavoring(rs: RegionState) -> FlavoringDeltas:
    instability = 1.0 - rs.stability
    eco  = rs.economy    / 100.0
    ten  = rs.tension    / 100.0
    mil  = rs.military   / 100.0
    pop  = rs.population / 100.0
    cap  = rs.capacity

    obs = (
        - cap  * config.FLAVOR_CAPACITY_OBS_COEFF
        - eco  * config.FLAVOR_ECONOMY_OBS_COEFF
        + mil  * config.FLAVOR_MILITARY_OBS_COEFF
        + (pop - 0.5) * config.FLAVOR_POPULATION_SCALE_COEFF
    )
    cov = (
          instability * config.FLAVOR_STABILITY_COV_COEFF
        + ten         * config.FLAVOR_TENSION_COV_COEFF
        + (pop - 0.5) * config.FLAVOR_POPULATION_SCALE_COEFF
    )
    elev = 0.0
    si = instability * config.FLAVOR_STABILITY_SI_COEFF

    cap_val = config.FLAVOR_MAX_DELTA
    def clamp(v):
        return max(-cap_val, min(cap_val, v))

    return FlavoringDeltas(
        obstacle_density    = clamp(obs),
        cover_density       = clamp(cov),
        elevation           = clamp(elev),
        sensor_interference = clamp(si),
    )


def apply_flavoring(sources, deltas: FlavoringDeltas):
    """Return a new list of GradientSources with intensities shifted by deltas.

    Intensities are clamped to [0, 1] after adjustment.
    Sources are not mutated — new GradientSource objects are returned.
    """
    from tactical_map import GradientSource

    delta_map = {
        "obstacle_density":    deltas.obstacle_density,
        "cover_density":       deltas.cover_density,
        "elevation":           deltas.elevation,
        "sensor_interference": deltas.sensor_interference,
    }
    result = []
    for src in sources:
        d = delta_map.get(src.property_type, 0.0)
        new_intensity = max(0.0, min(1.0, src.intensity + d))
        result.append(GradientSource(
            position      = src.position,
            property_type = src.property_type,
            radius        = src.radius,
            intensity     = new_intensity,
            falloff       = src.falloff,
        ))
    return result
