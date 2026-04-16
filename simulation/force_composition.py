"""
Per-force composition templates for behavior script force groups.

COMPOSITION_TEMPLATES maps template_name → {unit_type: power_ratio}.
instantiate_force converts a template + power budget into a slot list
(unit_type, count, power_each, power_total) matching the ratios within ±5%.

# See also: scripts/*.json — force definitions reference template names here.
# See also: force_allocator.py — allocates full archetype force by ASSET_PROFILES;
#   force_composition handles the per-force-group split within a script.
"""
import config


COMPOSITION_TEMPLATES: dict[str, dict[str, float]] = {
    # Defensive Stand — main thrust (heavy assault mix, DQ-A)
    "defensive_stand_attacker": {
        "Vanguard": 0.35, "Raider": 0.20, "Bombard": 0.20,
        "Interceptor": 0.15, "Warden": 0.10,
    },
    # Defensive Stand — flanker (fast light mix)
    "defensive_stand_attacker_light": {
        "Raider": 0.45, "Interceptor": 0.35, "Vanguard": 0.20,
    },
    # Assault — garrison (defensive heavy line, DQ-B)
    "assault_defender": {
        "Warden": 0.30, "Bastion": 0.20, "Interceptor": 0.20,
        "Bombard": 0.15, "Vanguard": 0.10, "Raider": 0.05,
    },
    # Assault — reserve commitment force (aggressive fast mix)
    "assault_reserve": {
        "Vanguard": 0.40, "Raider": 0.30, "Interceptor": 0.20, "Warden": 0.10,
    },
    # Multi-Front Defense — primary front (vanguard-biased)
    "multi_front_attacker": {
        "Vanguard": 0.40, "Bombard": 0.20, "Raider": 0.20, "Interceptor": 0.20,
    },
    # Multi-Front Defense — secondary fronts (lighter, raider-biased)
    "multi_front_attacker_light": {
        "Raider": 0.50, "Interceptor": 0.30, "Vanguard": 0.20,
    },
    # Counterinsurgency — insurgent cell (raider-dominant, DQ-D)
    "insurgent_cell": {
        "Raider": 0.55, "Interceptor": 0.25, "Vanguard": 0.15, "Warden": 0.05,
    },
}


# Force instantiation from these templates is handled by force_allocator._fill_force().
# Pass the desired template dict as the asset_profile argument.
