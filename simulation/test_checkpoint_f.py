#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import random
from collections import Counter
import config
from mission_generator import generate_mission, build_candidate_pool, compute_urgency


class MockRegion:
    def __init__(self, id, faction_id, fields=None, composites=None, held_since_tick=0):
        self.id = id
        self.faction_id = faction_id
        self.fields = fields or {"military": 50, "economy": 50, "tension": 30, "population": 60}
        self.composites = composites or {"stability": 50, "capacity": 50}
        self.held_since_tick = held_since_tick
        self.display_name = id.replace("_", " ").title()


class MockFaction:
    def __init__(self, id, archetype="conqueror", diplomatic_stance=None):
        self.id = id
        self.archetype = archetype
        self.diplomatic_stance = diplomatic_stance or {}
        self.display_name = id.replace("_", " ").title()


class MockWorld:
    def __init__(self, regions, adjacency):
        self.regions = {r.id: r for r in regions}
        self._adjacency = adjacency

    def get_neighbors(self, region_id, edge_type=None):
        return self._adjacency.get(region_id, [])


class MockLedger:
    def __init__(self, lineage_regions=None, active_regions=None, archetype_history=None):
        self._lineage_regions = lineage_regions or []
        self._active_regions = active_regions or set()
        self._archetype_history = archetype_history or {}

    def get_lineage_history(self, lineage_id):
        return self._lineage_regions

    def lineage_in_region(self, lineage_id, region_id):
        return region_id in self._active_regions

    def get_lineage_archetype_history(self, lineage_id):
        return self._archetype_history


def build_normal_world():
    r_crisis = MockRegion("crisis_zone", "player_civ",
                          fields={"military": 15, "economy": 18, "tension": 75, "population": 30},
                          composites={"stability": 12, "capacity": 18},
                          held_since_tick=0)
    r_pressured = MockRegion("pressured", "player_civ",
                             fields={"military": 30, "economy": 35, "tension": 50, "population": 45},
                             composites={"stability": 30, "capacity": 35},
                             held_since_tick=100)
    r_stable = MockRegion("stable_core", "player_civ",
                          fields={"military": 70, "economy": 75, "tension": 20, "population": 80},
                          composites={"stability": 70, "capacity": 75})
    r_quiet = MockRegion("quiet_border", "player_civ",
                         fields={"military": 55, "economy": 60, "tension": 25, "population": 65},
                         composites={"stability": 55, "capacity": 60})
    r_enemy_strong = MockRegion("enemy_fortress", "iron_dominion",
                                fields={"military": 85, "economy": 70, "tension": 15, "population": 75},
                                composites={"stability": 75, "capacity": 70})
    r_enemy_weak = MockRegion("enemy_outpost", "iron_dominion",
                              fields={"military": 25, "economy": 30, "tension": 55, "population": 35},
                              composites={"stability": 25, "capacity": 30})
    r_breakaway = MockRegion("rebel_zone", "breakaway_revolt",
                             fields={"military": 20, "economy": 22, "tension": 65, "population": 30},
                             composites={"stability": 15, "capacity": 20},
                             held_since_tick=450)
    r_conquered = MockRegion("lost_territory", "iron_dominion",
                             fields={"military": 35, "economy": 30, "tension": 60, "population": 35},
                             composites={"stability": 28, "capacity": 30})

    regions = [r_crisis, r_pressured, r_stable, r_quiet,
               r_enemy_strong, r_enemy_weak, r_breakaway, r_conquered]

    adjacency = {
        "crisis_zone":     ["enemy_fortress", "pressured", "rebel_zone"],
        "pressured":       ["crisis_zone", "stable_core", "enemy_outpost"],
        "stable_core":     ["pressured", "quiet_border", "rebel_zone"],
        "quiet_border":    ["stable_core", "lost_territory"],
        "enemy_fortress":  ["crisis_zone", "enemy_outpost", "lost_territory"],
        "enemy_outpost":   ["enemy_fortress", "pressured"],
        "rebel_zone":      ["crisis_zone", "stable_core"],
        "lost_territory":  ["quiet_border", "enemy_fortress"],
    }

    registry = {
        "player_civ": MockFaction("player_civ", "player_civilization",
                                  {"iron_dominion": "hostile", "breakaway_revolt": "hostile"}),
        "iron_dominion": MockFaction("iron_dominion", "conqueror",
                                     {"player_civ": "hostile"}),
        "breakaway_revolt": MockFaction("breakaway_revolt", "breakaway",
                                         {"player_civ": "hostile"}),
    }

    action_log = [
        {"faction_id": "iron_dominion", "action": "attack", "target_region": "crisis_zone",
         "budget_committed": 400, "tick": 598},
    ]
    event_log = [
        {"template_id": "evt_regional_revolt", "region_id": "pressured", "tick": 595},
    ]
    conquest_log = [
        {"region_id": "lost_territory", "old_faction_id": "player_civ",
         "new_faction_id": "iron_dominion", "tick": 570},
    ]

    return MockWorld(regions, adjacency), registry, action_log, event_log, conquest_log


def print_mission_summary(result, index=None):
    setup = result["setup"]
    sel = result["selected"]
    prefix = f"  Run {index}" if index is not None else "  "
    print(f"{prefix}: ({setup.region_id}, {setup.archetype}) "
          f"score={sel['score']:.3f} urg={sel['urgency']:.3f} "
          f"rel={sel['relevance']:.3f} pref={sel['preference']:.3f}")
    pf = setup.player_force
    ef = setup.enemy_forces[0]
    tc_p = Counter(u.unit_type for u in pf.units)
    tc_e = Counter(u.unit_type for u in ef.units)
    p_parts = ", ".join(f"{n} {t}" for t, n in sorted(tc_p.items(), key=lambda x: -x[1]))
    e_parts = ", ".join(f"{n} {t}" for t, n in sorted(tc_e.items(), key=lambda x: -x[1]))
    print(f"       Player: {p_parts} ({pf.total_power:.0f} power, {len(pf.units)} units)")
    print(f"       Enemy:  {e_parts} ({ef.total_power:.0f} power, {len(ef.units)} units)")
    print(f"       Objectives: {', '.join(o.type for o in setup.objectives)}")
    r = setup.reinforcements
    print(f"       Reinforcements: {r.structure_count} structures "
          f"(P:{r.player_structures} E:{r.enemy_structures} N:{r.neutral_structures})")


def main():
    print(f"\n{'═'*70}")
    print(f"  Stage 5.5 Checkpoint F — Mission Generator End-to-End")
    print(f"{'═'*70}")

    player_fid = "player_civ"
    tick = 600
    difficulty = "medium"

    ledger = MockLedger(
        lineage_regions=["crisis_zone", "pressured"],
        active_regions={"crisis_zone"},
        archetype_history={"defensive_stand": 3, "siege_breaking": 1},
    )
    lineage_id = "lineage_001"
    prefs = {
        "defensive_stand": 0.9,
        "assault": 0.8,
        "evacuation": "rare",
        "multi_front_defense": "rare",
    }

    # ── 10 runs with different seeds from same state ──
    print(f"\n{'─'*70}")
    print(f"  10 Runs — Same State, Different Seeds")
    print(f"{'─'*70}")

    world, registry, action_log, event_log, conquest_log = build_normal_world()
    selections = []

    for i in range(10):
        w, reg, al, el, cl = build_normal_world()
        rng = random.Random(1000 + i)
        result = generate_mission(
            w, reg, player_fid, el, al, cl, tick, difficulty, rng,
            ledger=ledger, current_lineage_id=lineage_id,
            player_preferences=prefs)
        if result:
            print_mission_summary(result, i + 1)
            selections.append((result["setup"].region_id, result["setup"].archetype))
        else:
            print(f"  Run {i+1}: No mission generated")

    unique = len(set(selections))
    print(f"\n  Unique selections: {unique}/10 "
          f"{'(variety OK)' if unique > 1 else '(NO VARIETY — check weighting)'}")
    selection_counts = Counter(selections)
    print(f"  Distribution:")
    for (rid, arch), cnt in selection_counts.most_common():
        print(f"    ({rid}, {arch}): {cnt}/10")

    # ── Crisis state — M2: selected region in top 3 by urgency >80% of time ──
    print(f"\n{'─'*70}")
    print(f"  M2 — Urgency Dominates in Crisis (top 3 by urgency >80%)")
    print(f"{'─'*70}")

    # Pre-flight: verify crisis_zone urgency > 0.8 before loop
    w_check, reg_check, al_check, el_check, cl_check = build_normal_world()
    w_check.regions["crisis_zone"].fields = {
        "military": 5, "economy": 7, "tension": 95, "population": 12}
    w_check.regions["crisis_zone"].composites = {"stability": 3, "capacity": 8}
    al_check.extend([
        {"faction_id": "iron_dominion", "action": "attack",
         "target_region": "crisis_zone", "budget_committed": 600, "tick": 599},
        {"faction_id": "iron_dominion", "action": "attack",
         "target_region": "crisis_zone", "budget_committed": 450, "tick": 597},
    ])
    el_check.extend([
        {"template_id": "evt_regional_revolt", "region_id": "crisis_zone", "tick": 596},
        {"template_id": "evt_revolt_entrenched", "region_id": "crisis_zone", "tick": 598},
        {"template_id": "evt_resistance_movement", "region_id": "crisis_zone", "tick": 599},
    ])
    cl_check.extend([
        {"region_id": "pressured", "old_faction_id": "player_civ",
         "new_faction_id": "iron_dominion", "tick": 590},
        {"region_id": "rebel_zone", "old_faction_id": "player_civ",
         "new_faction_id": "breakaway_revolt", "tick": 585},
    ])
    preflight_urg = compute_urgency(
        w_check.regions["crisis_zone"], w_check, reg_check,
        el_check, al_check, cl_check, tick)
    print(f"\n  Pre-flight crisis_zone urgency: {preflight_urg:.3f} "
          f"{'(>0.8 OK)' if preflight_urg > 0.8 else '(FAILED — not >0.8)'}")
    assert preflight_urg > 0.8, f"crisis_zone urgency {preflight_urg:.3f} must be >0.8"

    m2_hits = 0
    m2_total = 0
    for i in range(20):
        w, reg, al, el, cl = build_normal_world()
        w.regions["crisis_zone"].fields = {
            "military": 5, "economy": 7, "tension": 95, "population": 12}
        w.regions["crisis_zone"].composites = {"stability": 3, "capacity": 8}
        al.extend([
            {"faction_id": "iron_dominion", "action": "attack",
             "target_region": "crisis_zone", "budget_committed": 600, "tick": 599},
            {"faction_id": "iron_dominion", "action": "attack",
             "target_region": "crisis_zone", "budget_committed": 450, "tick": 597},
        ])
        el.extend([
            {"template_id": "evt_regional_revolt", "region_id": "crisis_zone", "tick": 596},
            {"template_id": "evt_revolt_entrenched", "region_id": "crisis_zone", "tick": 598},
            {"template_id": "evt_resistance_movement", "region_id": "crisis_zone", "tick": 599},
        ])
        cl.extend([
            {"region_id": "pressured", "old_faction_id": "player_civ",
             "new_faction_id": "iron_dominion", "tick": 590},
            {"region_id": "rebel_zone", "old_faction_id": "player_civ",
             "new_faction_id": "breakaway_revolt", "tick": 585},
        ])

        # Compute per-region urgency to find top 3
        region_urgencies = {}
        for rid, region in w.regions.items():
            urg = compute_urgency(region, w, reg, el, al, cl, tick)
            region_urgencies[rid] = urg
        sorted_by_urgency = sorted(region_urgencies.items(), key=lambda x: -x[1])
        top_3_regions = {rid for rid, _ in sorted_by_urgency[:3]}
        worst_urgency = sorted_by_urgency[0][1]

        rng = random.Random(2000 + i)
        result = generate_mission(
            w, reg, player_fid, el, al, cl, tick, difficulty, rng,
            ledger=ledger, current_lineage_id=lineage_id,
            player_preferences=prefs)
        if result and worst_urgency > 0.8:
            m2_total += 1
            selected_rid = result["setup"].region_id
            in_top3 = selected_rid in top_3_regions
            if in_top3:
                m2_hits += 1
            if i < 3:
                print(f"  Run {i+1}: selected={selected_rid}, "
                      f"top3={sorted_by_urgency[:3]}, in_top3={in_top3}")

    pct = m2_hits / m2_total * 100 if m2_total else 0
    print(f"\n  Selected in top 3 by urgency: {m2_hits}/{m2_total} ({pct:.0f}%)")
    print(f"  M2 target: >80% — {'PASS' if pct > 80 else 'BELOW TARGET'}")

    # ── Calm state — M3 + M4 ──
    print(f"\n{'─'*70}")
    print(f"  M3 — Preference Influence + M4 — Rare Archetypes (<10%)")
    print(f"{'─'*70}")

    calm_selections = []
    for i in range(50):
        calm_regions = [
            MockRegion("sector_alpha", "player_civ",
                       fields={"military": 60, "economy": 65, "tension": 20, "population": 70},
                       composites={"stability": 65, "capacity": 60},
                       held_since_tick=0),
            MockRegion("sector_beta", "player_civ",
                       fields={"military": 55, "economy": 60, "tension": 25, "population": 65},
                       composites={"stability": 55, "capacity": 55},
                       held_since_tick=0),
            MockRegion("enemy_border", "iron_dominion",
                       fields={"military": 30, "economy": 35, "tension": 45, "population": 40},
                       composites={"stability": 30, "capacity": 35}),
            MockRegion("breakaway_near", "breakaway_revolt",
                       fields={"military": 20, "economy": 25, "tension": 50, "population": 30},
                       composites={"stability": 20, "capacity": 25},
                       held_since_tick=500),
        ]
        calm_adj = {
            "sector_alpha": ["sector_beta", "enemy_border"],
            "sector_beta": ["sector_alpha", "breakaway_near"],
            "enemy_border": ["sector_alpha"],
            "breakaway_near": ["sector_beta"],
        }
        calm_world = MockWorld(calm_regions, calm_adj)
        calm_reg = {
            "player_civ": MockFaction("player_civ", "player_civilization",
                                      {"iron_dominion": "hostile", "breakaway_revolt": "hostile"}),
            "iron_dominion": MockFaction("iron_dominion", "conqueror",
                                         {"player_civ": "hostile"}),
            "breakaway_revolt": MockFaction("breakaway_revolt", "breakaway",
                                             {"player_civ": "hostile"}),
        }

        rng = random.Random(3000 + i)
        result = generate_mission(
            calm_world, calm_reg, player_fid, [], [], [], tick, difficulty, rng,
            ledger=ledger, current_lineage_id=lineage_id,
            player_preferences=prefs)
        if result:
            calm_selections.append(result["setup"].archetype)
            if i < 3:
                print_mission_summary(result, i + 1)

    arch_counts = Counter(calm_selections)
    preferred = sum(arch_counts.get(a, 0) for a in ["defensive_stand", "assault"])
    non_preferred = len(calm_selections) - preferred
    print(f"\n  Archetype distribution ({len(calm_selections)} missions):")
    for arch, cnt in arch_counts.most_common():
        pref_val = prefs.get(arch, 0.5)
        print(f"    {arch:<22} {cnt:>3} ({pref_val})")
    print(f"  Preferred (defensive_stand + assault): {preferred}")
    print(f"  Non-preferred: {non_preferred}")
    if preferred > 0 and non_preferred > 0:
        ratio = preferred / non_preferred
        print(f"  Ratio preferred/non-preferred: {ratio:.1f}x "
              f"{'(>2× target PASS)' if ratio > 2 else '(below 2× target)'}")

    rare_archetypes = {a for a, v in prefs.items() if v == "rare"}
    rare_count = sum(arch_counts.get(a, 0) for a in rare_archetypes)
    rare_pct = rare_count / len(calm_selections) * 100 if calm_selections else 0
    print(f"\n  M4 — Rare archetypes ({', '.join(rare_archetypes)}):")
    print(f"  Rare selected: {rare_count}/{len(calm_selections)} ({rare_pct:.1f}%)")
    print(f"  M4 target: <10% — {'PASS' if rare_pct < 10 else 'ABOVE TARGET'}")

    # ── Full briefing preview ──
    print(f"\n{'─'*70}")
    print(f"  Full Briefing Preview")
    print(f"{'─'*70}")

    w, reg, al, el, cl = build_normal_world()
    rng = random.Random(42)
    result = generate_mission(
        w, reg, player_fid, el, al, cl, tick, difficulty, rng,
        ledger=ledger, current_lineage_id=lineage_id,
        player_preferences=prefs)

    if result:
        briefing = result["setup"].briefing
        print(f"\n  Mission: ({result['setup'].region_id}, {result['setup'].archetype})")
        print(f"\n  ── SITUATION ──")
        print(f"  {briefing['situation']}")
        print(f"\n  ── OBJECTIVE ──")
        print(f"  {briefing['objective']}")
        print(f"\n  ── ASSETS ──")
        print(f"  {briefing['assets']}")

    print(f"\n{'═'*70}")
    print(f"  Checkpoint F — Complete")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
