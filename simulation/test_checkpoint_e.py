#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
from mission_contracts import MissionResult
from outcome_resolver import resolve_outcome, compute_delta


class MockRegion:
    def __init__(self, id, faction_id, fields=None):
        self.id = id
        self.faction_id = faction_id
        self.fields = dict(fields) if fields else {}


class MockWorld:
    def __init__(self, regions, adjacency=None):
        self.regions = {r.id: r for r in regions}
        self._adjacency = adjacency or {}

    def get_neighbors(self, region_id, edge_type=None):
        return self._adjacency.get(region_id, [])


class MockLedger:
    def __init__(self):
        self.deaths = []

    def record_commander_death(self, commander_id, region_id, outcome_band):
        self.deaths.append({
            "commander_id": commander_id,
            "region_id": region_id,
            "outcome_band": outcome_band,
        })


def make_result(outcome_band, commander_survived=True):
    return MissionResult(
        mission_id="test_mission",
        outcome_band=outcome_band,
        objective_score=0.5,
        force_retention=0.5,
        per_objective=[],
        commander_survived=commander_survived,
        ticks_elapsed=100,
    )


def fresh_region(id, faction_id, fields):
    return MockRegion(id, faction_id, fields)


BANDS = ["total_success", "strong_success", "partial_success", "partial_failure", "total_failure"]


def main():
    print(f"\n{'═'*70}")
    print(f"  Stage 5.5 Checkpoint E — Outcome Resolver")
    print(f"{'═'*70}")

    region_a_base = {"military": 23, "economy": 41, "tension": 72, "stability": 18, "population": 50}
    region_b_base = {"military": 75, "economy": 82, "tension": 25, "stability": 71, "population": 80}

    # ── Delta computation verification ──
    print(f"\n{'─'*70}")
    print(f"  Delta Computation Verification")
    print(f"{'─'*70}")
    print(f"  {'Form':<18} {'Field':<10} {'Current':>8} {'Pct':>6} {'Delta':>8} {'New':>8}")
    print(f"  {'─'*18} {'─'*10} {'─'*8} {'─'*6} {'─'*8} {'─'*8}")
    for current, label in [(23, "mil@23"), (75, "mil@75")]:
        for form, pct in [("deficit", 15), ("current", -10), ("deficit", 5), ("current", -30)]:
            delta = compute_delta(current, form, pct)
            new = max(0, min(100, current + delta))
            print(f"  {form:<18} {label:<10} {current:>8} {pct:>+6} {delta:>+8.2f} {new:>8.2f}")

    # ── Defensive Stand: all 5 bands × 2 regions ──
    print(f"\n{'─'*70}")
    print(f"  Defensive Stand — All 5 Outcome Bands")
    print(f"{'─'*70}")

    for band in BANDS:
        print(f"\n  ── {band.upper().replace('_', ' ')} ──")
        print(f"  {'Region':<12} {'Field':<12} {'Old':>8} {'Delta':>8} {'New':>8} {'Form':<10} {'Pct':>5}")
        print(f"  {'─'*12} {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*5}")

        for region_label, base_fields in [("Region A", region_a_base), ("Region B", region_b_base)]:
            r = fresh_region("test_region", "player_civ", base_fields)
            world = MockWorld([r])
            result = make_result(band)
            outcome = resolve_outcome(result, "defensive_stand", "test_region",
                                      world, "player_civ")
            for d in outcome["applied_deltas"]:
                print(f"  {region_label:<12} {d['field']:<12} {d['old_value']:>8.1f} "
                      f"{d['delta']:>+8.2f} {d['new_value']:>8.2f} {d['form']:<10} {d['pct']:>+5}")

    # ── Side-by-side comparison ──
    print(f"\n{'─'*70}")
    print(f"  Side-by-Side: Region A (desperate) vs Region B (thriving)")
    print(f"{'─'*70}")
    print(f"  Region A: mil={region_a_base['military']}, eco={region_a_base['economy']}, "
          f"ten={region_a_base['tension']}, pop={region_a_base['population']}")
    print(f"  Region B: mil={region_b_base['military']}, eco={region_b_base['economy']}, "
          f"ten={region_b_base['tension']}, pop={region_b_base['population']}")

    print(f"\n  {'Band':<20} {'Field':<10} {'A delta':>8} {'B delta':>8} {'A bigger?':<12}")
    print(f"  {'─'*20} {'─'*10} {'─'*8} {'─'*8} {'─'*12}")

    for band in BANDS:
        for region_label, base_fields in [("A", region_a_base), ("B", region_b_base)]:
            r = fresh_region("test_region", "player_civ", base_fields)
            world = MockWorld([r])
            result = make_result(band)
            outcome = resolve_outcome(result, "defensive_stand", "test_region",
                                      world, "player_civ")
            if region_label == "A":
                a_deltas = {d["field"]: d["delta"] for d in outcome["applied_deltas"]}
            else:
                b_deltas = {d["field"]: d["delta"] for d in outcome["applied_deltas"]}

        for field in sorted(set(list(a_deltas.keys()) + list(b_deltas.keys()))):
            ad = a_deltas.get(field, 0)
            bd = b_deltas.get(field, 0)
            if ad == 0 and bd == 0:
                continue
            a_bigger = abs(ad) > abs(bd)
            note = ""
            if field == "military" and band in ("total_success", "strong_success"):
                note = "(deficit → desperate gains more)" if a_bigger else "(unexpected)"
            elif field == "military" and band in ("total_failure", "partial_failure"):
                note = "(current → thriving loses more)" if not a_bigger else "(unexpected)"
            print(f"  {band:<20} {field:<10} {ad:>+8.2f} {bd:>+8.2f} {'YES' if a_bigger else 'no':<12} {note}")

    # ── Commander death ──
    print(f"\n{'─'*70}")
    print(f"  Commander Death Handling")
    print(f"{'─'*70}")

    r = fresh_region("crisis_zone", "player_civ", dict(region_a_base))
    world = MockWorld([r])
    ledger = MockLedger()
    result = make_result("partial_failure", commander_survived=False)
    outcome = resolve_outcome(result, "defensive_stand", "crisis_zone",
                              world, "player_civ",
                              ledger=ledger, commander_id="cmd_voss_003")

    print(f"\n  Commander survived: {result.commander_survived}")
    print(f"  Events generated: {len(outcome['events'])}")
    for evt in outcome["events"]:
        print(f"    event_id: {evt['event_id']}")
        print(f"    commander_id: {evt['commander_id']}")
        print(f"    region_id: {evt['region_id']}")
        print(f"    outcome_band: {evt['outcome_band']}")
    print(f"  Ledger deaths recorded: {len(ledger.deaths)}")
    for d in ledger.deaths:
        print(f"    {d}")

    # ── Region transfer (Reconquest) ──
    print(f"\n{'─'*70}")
    print(f"  Region Transfer — Reconquest")
    print(f"{'─'*70}")

    for band in BANDS:
        r = fresh_region("lost_territory", "iron_dominion",
                         {"military": 40, "economy": 35, "tension": 55, "stability": 30, "population": 45})
        world = MockWorld([r])
        result = make_result(band)
        outcome = resolve_outcome(result, "reconquest", "lost_territory",
                                  world, "player_civ")
        transfer = outcome["region_transfer"]
        owner_after = world.regions["lost_territory"].faction_id
        print(f"  {band:<20} → transfer: {'YES' if transfer else 'no':<5} "
              f"owner: {owner_after}")

    # ── Adjacent player target (Evacuation) ──
    print(f"\n{'─'*70}")
    print(f"  Adjacent Player Targets — Evacuation Total Success")
    print(f"{'─'*70}")

    r_doomed = fresh_region("doomed", "player_civ",
                            {"military": 10, "economy": 15, "tension": 80, "population": 20})
    r_adj1 = fresh_region("safe_harbor", "player_civ",
                          {"military": 60, "economy": 55, "tension": 30, "population": 65})
    r_adj2 = fresh_region("refugee_camp", "player_civ",
                          {"military": 45, "economy": 40, "tension": 35, "population": 50})
    r_enemy = fresh_region("enemy_land", "iron_dominion",
                           {"military": 80, "economy": 70, "tension": 20, "population": 75})
    adjacency = {
        "doomed": ["safe_harbor", "refugee_camp", "enemy_land"],
    }
    world = MockWorld([r_doomed, r_adj1, r_adj2, r_enemy], adjacency)
    result = make_result("total_success")
    outcome = resolve_outcome(result, "evacuation", "doomed", world, "player_civ")

    print(f"\n  Mission region: doomed (player)")
    print(f"  Adjacent: safe_harbor (player), refugee_camp (player), enemy_land (enemy)")
    print(f"  Deltas applied to adjacent player regions only:")
    for d in outcome["applied_deltas"]:
        print(f"    {d['region_id']:<16} {d['field']:<12} {d['old_value']:>6.1f} → {d['new_value']:>6.2f} "
              f"(delta {d['delta']:>+6.2f})")
    enemy_touched = any(d["region_id"] == "enemy_land" for d in outcome["applied_deltas"])
    print(f"  Enemy region touched: {enemy_touched} (should be False)")

    print(f"\n{'═'*70}")
    print(f"  Checkpoint E — Complete")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
