import config
from mission_contracts import (
    ForceUnit, ForceComposition, ObjectiveSpec,
    ReinforcementSpec, MissionSetup, MissionResult,
)
from power_rating import compute_power_rating
from test_maps import open_field


def test_contracts():
    print("=" * 60)
    print("CONTRACT DATACLASS INSTANTIATION")
    print("=" * 60)

    unit = ForceUnit(
        unit_type="Raider", category="Strike",
        stats=config.UNIT_STATS["Raider"], power_rating=0.0,
        faction_id="player", name="Alpha Squad",
    )
    print(f"  ForceUnit:          OK  ({unit.unit_type}, {unit.category})")

    comp = ForceComposition(units=[unit], total_power=100.0, faction_id="player")
    print(f"  ForceComposition:   OK  ({len(comp.units)} unit, power={comp.total_power})")

    obj = ObjectiveSpec(
        id="obj_1", type="hold_zone", weight=1.0,
        params={"center": (2000, 2000), "radius": 500, "hold_ticks": 600},
        is_primary=True,
    )
    print(f"  ObjectiveSpec:      OK  ({obj.type}, primary={obj.is_primary})")

    reinf = ReinforcementSpec(
        structure_count=4, player_structures=2,
        enemy_structures=1, neutral_structures=1,
        production_rate=0.1, enemy_target_ratio={"Vanguard": 0.5, "Raider": 0.5},
    )
    print(f"  ReinforcementSpec:  OK  ({reinf.structure_count} structures)")

    setup = MissionSetup(
        mission_id="mission_001", archetype="defensive_stand",
        region_id="region_alpha", map_params={"canvas": "small"},
        player_force=comp, enemy_forces=[comp],
        objectives=[obj], reinforcements=reinf,
        time_limit_ticks=6000, behavior_script_id="script_default",
        briefing={"situation": "Under attack", "objective": "Hold the line"},
        difficulty="medium", metadata={"seed": 42},
    )
    print(f"  MissionSetup:       OK  (archetype={setup.archetype}, region={setup.region_id})")

    result = MissionResult(
        mission_id="mission_001", outcome_band="strong_success",
        objective_score=0.85, force_retention=0.72,
        per_objective=[{"id": "obj_1", "completion": 1.0}],
        commander_survived=True, ticks_elapsed=4200,
    )
    print(f"  MissionResult:      OK  (band={result.outcome_band}, score={result.objective_score})")
    print()


def test_power_ratings():
    print("=" * 60)
    print("POWER RATING TABLE — Tier 2 Baselines")
    print("=" * 60)
    print(f"  {'Unit':<14} {'HP':>6} {'DPS':>7} {'Range':>6} {'Speed':>6} {'Power':>10}")
    print(f"  {'-'*14} {'-'*6} {'-'*7} {'-'*6} {'-'*6} {'-'*10}")

    ratings = {}
    for unit_type, stats in config.UNIT_STATS.items():
        s = dict(stats)
        s["unit_type"] = unit_type
        dps = s["base_damage"] / s["attack_interval"]
        pr = compute_power_rating(s)
        ratings[unit_type] = pr
        print(f"  {unit_type:<14} {s['hp']:>6} {dps:>7.1f} {s['attack_range']:>6} {s['speed']:>6} {pr:>10.1f}")

    print()
    ranked = sorted(ratings.items(), key=lambda x: -x[1])
    print("  Ranking (highest to lowest):")
    for i, (name, pr) in enumerate(ranked, 1):
        print(f"    {i}. {name:<14} {pr:.1f}")
    print()


def test_map():
    print("=" * 60)
    print("OPEN FIELD MAP — Gradient Queries")
    print("=" * 60)

    tmap = open_field()
    print(f"  Canvas: {tmap.width} x {tmap.height}")
    print(f"  Layers: {tmap.layers}")
    print(f"  Gradient sources: {len(tmap.gradient_sources)}")
    print(f"  Spine nodes: {len(tmap.spine_nodes)}")
    print()

    positions = [
        (0, 0),
        (2000, 2000),
        (3999, 3999),
    ]
    print(f"  {'Position':<18} {'sensor_int':>10} {'elevation':>10} {'obstacle':>10} {'cover':>10}")
    print(f"  {'-'*18} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for pos in positions:
        si = tmap.sensor_interference(*pos)
        el = tmap.elevation(*pos)
        ob = tmap.obstacle_density(*pos)
        co = tmap.cover_density(*pos)
        print(f"  ({pos[0]:>5}, {pos[1]:>5})   {si:>10.2f} {el:>10.2f} {ob:>10.2f} {co:>10.2f}")
    print()


def test_spatial_hash():
    print("=" * 60)
    print("SPATIAL HASH — Query Test")
    print("=" * 60)

    tmap = open_field()

    result_empty = tmap.spatial_hash.query(2000, 2000, 500)
    print(f"  Query (2000, 2000) r=500, no units: {len(result_empty)} results (expected 0)")

    tmap.spatial_hash.insert(0, 2000, 2000)
    tmap.spatial_hash.insert(1, 2100, 2100)
    tmap.spatial_hash.insert(2, 3500, 3500)

    result_near = tmap.spatial_hash.query(2000, 2000, 500)
    print(f"  Query (2000, 2000) r=500, 3 units placed: {len(result_near)} results (expected 2)")
    print(f"    Found unit IDs: {sorted(result_near)}")

    result_far = tmap.spatial_hash.query(3500, 3500, 200)
    print(f"  Query (3500, 3500) r=200, 3 units placed: {len(result_far)} results (expected 1)")
    print(f"    Found unit IDs: {sorted(result_far)}")
    print()


if __name__ == "__main__":
    test_contracts()
    test_power_ratings()
    test_map()
    test_spatial_hash()
    print("Checkpoint A complete.")
