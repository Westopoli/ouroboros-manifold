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
class CommanderSelection:
    character_id: str
    character_name: str
    lineage_id: str | None
    faction_id: str
    region_id: str
    chapter_number: int
    pool_used: str | None        # "previous_descendant"|"nemesis_descendant"|"unrelated"; None on STAY or bloodline succession
    pool_rolled: str | None      # which pool was rolled before fallthrough; None when no roll occurred
    rotation_reason: str | None  # None=stayed, "hard_cap"|"normal"|"commander_death"|"forced"
    rotation_mechanism: str | None  # "pool_roll"|"bloodline_succession"; None on STAY


@dataclass
class MissionResult:
    mission_id: str
    outcome_band: str
    objective_score: float
    force_retention: float
    per_objective: list[dict]
    commander_survived: bool
    ticks_elapsed: int
