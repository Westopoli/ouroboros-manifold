# Input:  tier string ("home", "frontier", "empty"), field values (0-100 floats)
# Output: Region object with .fields dict, .composites dict, .recompute_composites()

import config


class Region:
    def __init__(self, region_id: str, name: str, tier: str,
                 fields: dict | None = None,
                 faction_id: str | None = None) -> None:
        self.id = region_id
        self.name = name
        self.tier = tier  # "home", "frontier", "empty"
        self.faction_id = faction_id  # None = unclaimed/neutral

        if tier == "empty" or fields is None:
            self.fields = {"military": 0.0, "economy": 0.0, "tension": 0.0, "population": 0.0}
        else:
            self.fields = {
                "military":   float(fields.get("military",   0.0)),
                "economy":    float(fields.get("economy",    0.0)),
                "tension":    float(fields.get("tension",    0.0)),
                "population": float(fields.get("population", 0.0)),
            }

        self.econ_phase_offset = 0.0
        self.tension_phase_offset = 0.0
        self.held_since_tick = None

        self.composites = {"stability": 0.0, "capacity": 0.0}
        if tier != "empty":
            self.recompute_composites()

    def recompute_composites(self) -> None:
        m = self.fields["military"]
        e = self.fields["economy"]
        t = self.fields["tension"]
        p = self.fields["population"]

        stability = (
            m * config.W_STAB_MILITARY
            + (100.0 - t) * config.W_STAB_TENSION
            + p * config.W_STAB_POPULATION
        )
        if m < config.STAB_MILITARY_THRESHOLD:
            stability *= config.STAB_MILITARY_PENALTY
        if p < config.STAB_POPULATION_THRESHOLD:
            stability *= config.STAB_POPULATION_PENALTY

        capacity = (
            e * config.W_CAP_ECONOMY
            + p * config.W_CAP_POPULATION
            + m * config.W_CAP_MILITARY
        )
        if e < config.CAP_ECONOMY_THRESHOLD:
            capacity *= config.CAP_ECONOMY_PENALTY
        if p < config.CAP_POPULATION_THRESHOLD:
            capacity *= config.CAP_POPULATION_PENALTY

        self.composites["stability"] = round(stability, 2)
        self.composites["capacity"]  = round(capacity, 2)

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "tier":       self.tier,
            "faction_id": self.faction_id,
            "fields":     {k: round(v, 2) for k, v in self.fields.items()},
            "composites": dict(self.composites),
        }
