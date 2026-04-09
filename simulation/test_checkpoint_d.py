#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import random
from collections import Counter
import config
from force_allocator import allocate_forces, compute_reinforcement_spec


class MockRegion:
    def __init__(self, fields=None):
        self.fields = fields or {"military": 50, "economy": 50, "tension": 30, "population": 60}


def print_force(label, force):
    tc = Counter(u.unit_type for u in force.units)
    parts = [f"{cnt} {ut}" for ut, cnt in sorted(tc.items(), key=lambda x: -x[1])]
    print(f"    {label}: {', '.join(parts)} | Total power: {force.total_power:.0f} ({len(force.units)} units)")


def main():
    print(f"\n{'═'*70}")
    print(f"  Stage 5.5 Checkpoint D — Force Allocation")
    print(f"{'═'*70}")

    rng = random.Random(42)

    archetypes = [
        ("defensive_stand", "Budget-driven defensive",
         {"budget_committed": 400}, MockRegion({"military": 25, "economy": 30, "tension": 60, "population": 40})),
        ("assault", "Budget-driven offensive",
         {"budget_committed": 350}, MockRegion({"military": 35, "economy": 40, "tension": 40, "population": 50})),
        ("counterinsurgency", "Military-driven asymmetric",
         {}, MockRegion({"military": 30, "economy": 25, "tension": 70, "population": 35})),
    ]
    capacities = [("thriving", 0.9), ("stable", 0.6), ("declining", 0.3)]
    difficulties = ["easy", "medium", "hard"]

    for arch_key, arch_label, trigger_ctx, region in archetypes:
        print(f"\n{'─'*70}")
        print(f"  ARCHETYPE: {arch_key} ({arch_label})")
        print(f"  Trigger context: {trigger_ctx}")
        print(f"  Region military: {region.fields['military']}")
        target_profile = config.ASSET_PROFILES[arch_key]
        top_types = sorted(target_profile.items(), key=lambda x: -x[1])[:3]
        print(f"  Target profile (top 3): {', '.join(f'{t}={r:.0%}' for t, r in top_types)}")
        print(f"{'─'*70}")

        enemy_forces_by_difficulty = {}

        for cap_label, cap_value in capacities:
            print(f"\n  Capacity: {cap_label} ({cap_value})")
            for diff in difficulties:
                result = allocate_forces(
                    arch_key, trigger_ctx, region, cap_value, diff,
                    "player_civ", "iron_dominion", rng)

                ef = result["enemy_force"]
                pf = result["player_force"]
                parity = result["parity_ratio"]
                actual_parity = pf.total_power / ef.total_power if ef.total_power > 0 else 0

                print(f"\n    [{diff.upper():>6}] Parity: {parity:.3f} (actual: {actual_parity:.3f})")
                print_force("Enemy ", ef)
                print_force("Player", pf)

                if pf.total_power > 0:
                    tc = Counter(u.unit_type for u in pf.units)
                    total_units = len(pf.units)
                    max_dev = 0
                    for ut, target_ratio in target_profile.items():
                        actual_ratio = tc.get(ut, 0) / total_units if total_units > 0 else 0
                        dev = abs(actual_ratio - target_ratio)
                        max_dev = max(max_dev, dev)
                    print(f"    Asset deviation: max {max_dev:.2f} {'(OK)' if max_dev < 0.15 else '(HIGH)'}")

                if result["shortfall_types"]:
                    sc = Counter(result["shortfall_types"])
                    parts = [f"{cnt} {ut}" for ut, cnt in sc.items()]
                    print(f"    Shortfall: {', '.join(parts)} removed")

                enemy_forces_by_difficulty[(cap_label, diff)] = ef.total_power

        print(f"\n  ── Enemy Force Invariance Check ──")
        for cap_label, _ in capacities:
            powers = [enemy_forces_by_difficulty[(cap_label, d)] for d in difficulties]
            all_same = all(abs(p - powers[0]) < 0.01 for p in powers)
            print(f"    {cap_label}: easy={powers[0]:.0f}, medium={powers[1]:.0f}, hard={powers[2]:.0f} "
                  f"{'(identical)' if all_same else '(DIFFERS — BUG)'}")

    # ── Reinforcement specs ──
    print(f"\n{'─'*70}")
    print(f"  Reinforcement Specs")
    print(f"{'─'*70}")
    for arch_key in ["defensive_stand", "assault", "counterinsurgency"]:
        for mil in [25, 50, 75]:
            r = compute_reinforcement_spec(arch_key, mil)
            print(f"  {arch_key:<22} mil={mil:>2} → {r.structure_count} structures "
                  f"(P:{r.player_structures} E:{r.enemy_structures} N:{r.neutral_structures})")

    print(f"\n{'═'*70}")
    print(f"  Checkpoint D — Complete")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
