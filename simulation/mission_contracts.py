from dataclasses import dataclass, field


@dataclass
class ForceUnit:
    unit_type: str
    category: str
    stats: dict
    power_rating: float
    faction_id: str
    name: str


@dataclass
class ForceComposition:
    units: list[ForceUnit]
    total_power: float
    faction_id: str


@dataclass
class ObjectiveSpec:
    id: str
    type: str
    weight: float
    params: dict
    is_primary: bool


@dataclass
class ReinforcementSpec:
    structure_count: int
    player_structures: int
    enemy_structures: int
    neutral_structures: int
    production_rate: float
    enemy_target_ratio: dict


@dataclass
class MissionSetup:
    mission_id: str
    archetype: str
    region_id: str
    map_params: dict
    player_force: ForceComposition
    enemy_forces: list[ForceComposition]
    objectives: list[ObjectiveSpec]
    reinforcements: ReinforcementSpec
    time_limit_ticks: int
    behavior_script_id: str
    briefing: dict
    difficulty: str
    metadata: dict


@dataclass
class MissionResult:
    mission_id: str
    outcome_band: str
    objective_score: float
    force_retention: float
    per_objective: list[dict]
    commander_survived: bool
    ticks_elapsed: int
