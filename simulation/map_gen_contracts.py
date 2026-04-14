from dataclasses import dataclass, field


@dataclass(frozen=True)
class ZoneSpec:
    zone_id: str
    position_ratio: tuple[float, float]  # (x, y) in [0.0, 1.0]
    node_type: str
    properties: dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.zone_id)

    def __eq__(self, other):
        return isinstance(other, ZoneSpec) and self.zone_id == other.zone_id


@dataclass(frozen=True)
class EdgeSpec:
    from_zone: str
    to_zone: str
    edge_type: str  # "path" | "restricted" | "flank"


@dataclass(frozen=True)
class DriftPathSpec:
    zone_id: str
    waypoints: tuple  # tuple of (x, y) position_ratio pairs
    period_ticks: int
    mode: str  # "ping_pong" | "loop"


@dataclass(frozen=True)
class LayoutSpec:
    layout_id: str
    name: str
    canvas_class: str  # "small" | "medium" | "large"
    zones: tuple[ZoneSpec, ...]
    edges: tuple[EdgeSpec, ...]
    tags: tuple[str, ...]
    drift_paths: tuple[DriftPathSpec, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RegionState:
    # Six numeric driver fields — read by generation logic
    stability: float
    capacity: float
    economy: float
    tension: float
    military: float
    population: float
    # Two debug/label fields — carried for filenames, metadata, log lines only
    region_id: str = ""
    tier: int = 0


@dataclass(frozen=True)
class GeneratorInput:
    archetype: str
    region_state: RegionState
    canvas_size: str  # "small" | "medium" | "large"
    seed: int


@dataclass
class MapGenerationResult:
    tactical_map: object  # TacticalMap — avoid circular import
    chosen_layout_id: str
    fairness_score: object  # FairnessScore
    generation_metadata: dict
