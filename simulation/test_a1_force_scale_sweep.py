"""
test_a1_force_scale_sweep.py — Track A / A1 measurement harness.

Sweeps BUDGET_TO_POWER_SCALE and MILITARY_TO_POWER_SCALE multipliers across
representative archetypes / region states / capacities, calls allocate_forces,
records resulting enemy & player unit counts. Pure diagnostic — does not
mutate config persistently (snapshots and restores) and does not assert.

Run: python3 simulation/test_a1_force_scale_sweep.py
"""
import os
import random
import sys
from collections import Counter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")

import config
from force_allocator import allocate_forces


BASE_BUDGET_SCALE   = 150.0
BASE_MILITARY_SCALE = 1000.0

SCALE_MULTIPLIERS = [1.0, 1.5, 2.0, 3.0, 4.0]

ARCHETYPES_BY_PATH = {
    "BUDGET":    ["defensive_stand"],
    "DEFAULT":   ["assault", "reconquest", "siege_breaking"],
    "INSURGENT": ["counterinsurgency"],
}

# Representative region states
REGION_STATES = [
    {"military": 30, "population": 40, "label": "weak"},
    {"military": 50, "population": 50, "label": "mid"},
    {"military": 80, "population": 70, "label": "strong"},
]

# Representative trigger contexts (only used for BUDGET / INSURGENT paths)
BUDGET_VALUES         = [100, 300, 500]
CAPACITY_VALUES       = [0.3, 0.5, 0.8]
DIFFICULTY            = "medium"
SEED                  = 1


class MockRegion:
    def __init__(self, military, population):
        self.fields = {"military": float(military), "population": float(population)}
        self.composites = {"capacity": 0.5}


def _summarize_units(force):
    counts = Counter(u.unit_type for u in force.units)
    cat_counts = Counter(u.category for u in force.units)
    return len(force.units), counts, cat_counts


def _format_counts(counts: Counter) -> str:
    order = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]
    return " ".join(f"{ut[:3]}={counts.get(ut, 0)}" for ut in order)


def _run_one(archetype, region_state, capacity, scale_mult, budget_committed=None):
    config.BUDGET_TO_POWER_SCALE   = BASE_BUDGET_SCALE * scale_mult
    config.MILITARY_TO_POWER_SCALE = BASE_MILITARY_SCALE * scale_mult

    region = MockRegion(region_state["military"], region_state["population"])
    rng = random.Random(SEED)
    trigger_ctx = {}
    if budget_committed is not None:
        trigger_ctx["budget_committed"] = budget_committed

    alloc = allocate_forces(
        archetype=archetype,
        trigger_context=trigger_ctx,
        region=region,
        capacity=capacity,
        difficulty=DIFFICULTY,
        player_faction_id="player",
        enemy_faction_id="enemy",
        rng=rng,
    )

    e_n, e_counts, e_cats = _summarize_units(alloc["enemy_force"])
    p_n, p_counts, p_cats = _summarize_units(alloc["player_force"])
    return {
        "enemy_power":  alloc["enemy_power_total"],
        "parity":       alloc["parity_ratio"],
        "enemy_total":  e_n,
        "player_total": p_n,
        "enemy_counts": e_counts,
        "player_counts": p_counts,
        "enemy_cats":   e_cats,
        "player_cats":  p_cats,
    }


def _scenario_grid(path_name, archetype):
    print()
    print("=" * 100)
    print(f"  PATH={path_name}  archetype={archetype}")
    print("=" * 100)

    if path_name == "BUDGET":
        # Budget archetype: enemy_power = budget × BUDGET_TO_POWER_SCALE
        for budget in BUDGET_VALUES:
            print(f"\n  budget_committed={budget}, capacity=0.5, mil=50")
            print(f"  {'mult':>5} {'e_pow':>10} {'e_n':>4} {'p_n':>4} {'parity':>7}  enemy_breakdown")
            print(f"  {'-'*5} {'-'*10} {'-'*4} {'-'*4} {'-'*7}  {'-'*40}")
            for m in SCALE_MULTIPLIERS:
                r = _run_one(archetype, REGION_STATES[1], 0.5, m, budget_committed=budget)
                print(f"  {m:>5.2f} {r['enemy_power']:>10.0f} "
                      f"{r['enemy_total']:>4} {r['player_total']:>4} "
                      f"{r['parity']:>7.2f}  {_format_counts(r['enemy_counts'])}")
    elif path_name == "INSURGENT":
        # Insurgent: pop-driven; sweep region.population implicitly via REGION_STATES
        for rs in REGION_STATES:
            print(f"\n  region={rs['label']} (mil={rs['military']}, pop={rs['population']}), capacity=0.5")
            print(f"  {'mult':>5} {'e_pow':>10} {'e_n':>4} {'p_n':>4} {'parity':>7}  enemy_breakdown")
            print(f"  {'-'*5} {'-'*10} {'-'*4} {'-'*4} {'-'*7}  {'-'*40}")
            for m in SCALE_MULTIPLIERS:
                r = _run_one(archetype, rs, 0.5, m)
                print(f"  {m:>5.2f} {r['enemy_power']:>10.0f} "
                      f"{r['enemy_total']:>4} {r['player_total']:>4} "
                      f"{r['parity']:>7.2f}  {_format_counts(r['enemy_counts'])}")
    else:
        # DEFAULT: enemy_power = region.military × MILITARY_TO_POWER_SCALE
        for rs in REGION_STATES:
            for cap in CAPACITY_VALUES:
                print(f"\n  region={rs['label']} (mil={rs['military']}), capacity={cap}")
                print(f"  {'mult':>5} {'e_pow':>10} {'e_n':>4} {'p_n':>4} {'parity':>7}  enemy_breakdown")
                print(f"  {'-'*5} {'-'*10} {'-'*4} {'-'*4} {'-'*7}  {'-'*40}")
                for m in SCALE_MULTIPLIERS:
                    r = _run_one(archetype, rs, cap, m)
                    print(f"  {m:>5.2f} {r['enemy_power']:>10.0f} "
                          f"{r['enemy_total']:>4} {r['player_total']:>4} "
                          f"{r['parity']:>7.2f}  {_format_counts(r['enemy_counts'])}")


def main():
    base_budget   = config.BUDGET_TO_POWER_SCALE
    base_military = config.MILITARY_TO_POWER_SCALE
    try:
        print("\n" + "#" * 100)
        print(f"  A1 force-scale sweep")
        print(f"  Baseline: BUDGET_TO_POWER_SCALE={base_budget}  MILITARY_TO_POWER_SCALE={base_military}")
        print(f"  Multipliers: {SCALE_MULTIPLIERS}")
        print(f"  Difficulty: {DIFFICULTY}  seed: {SEED}")
        print("#" * 100)
        for path_name, archs in ARCHETYPES_BY_PATH.items():
            for a in archs:
                _scenario_grid(path_name, a)
    finally:
        config.BUDGET_TO_POWER_SCALE   = base_budget
        config.MILITARY_TO_POWER_SCALE = base_military
        print("\n  (config restored)")


if __name__ == "__main__":
    main()
