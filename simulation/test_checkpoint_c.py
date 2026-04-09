#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from mission_generator import build_candidate_pool, score_candidates
import config


class MockRegion:
    def __init__(self, id, faction_id, fields=None, composites=None, held_since_tick=0):
        self.id = id
        self.faction_id = faction_id
        self.fields = fields or {"military": 50, "economy": 50, "tension": 30, "population": 60}
        self.composites = composites or {"stability": 50, "capacity": 50}
        self.held_since_tick = held_since_tick


class MockFaction:
    def __init__(self, id, archetype="conqueror", diplomatic_stance=None):
        self.id = id
        self.archetype = archetype
        self.diplomatic_stance = diplomatic_stance or {}


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


def main():
    print(f"\n{'═'*70}")
    print(f"  Stage 5.5 Checkpoint C — Candidate Scoring")
    print(f"{'═'*70}")

    player_fid = "player_civ"
    tick = 600

    # ── World: 8 regions at varying pressure levels ──
    r_crisis = MockRegion("crisis_zone", player_fid,
                          fields={"military": 15, "economy": 18, "tension": 75, "population": 30},
                          composites={"stability": 12, "capacity": 18},
                          held_since_tick=0)
    r_pressured = MockRegion("pressured", player_fid,
                             fields={"military": 30, "economy": 35, "tension": 50, "population": 45},
                             composites={"stability": 30, "capacity": 35},
                             held_since_tick=100)
    r_stable = MockRegion("stable_core", player_fid,
                          fields={"military": 70, "economy": 75, "tension": 20, "population": 80},
                          composites={"stability": 70, "capacity": 75})
    r_quiet = MockRegion("quiet_border", player_fid,
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

    world = MockWorld(regions, adjacency)

    registry = {
        player_fid: MockFaction(player_fid, "player_civilization",
                                {"iron_dominion": "hostile", "breakaway_revolt": "hostile"}),
        "iron_dominion": MockFaction("iron_dominion", "conqueror",
                                     {player_fid: "hostile"}),
        "breakaway_revolt": MockFaction("breakaway_revolt", "breakaway",
                                         {player_fid: "hostile"}),
    }

    # Active events: attack on crisis zone + revolt on pressured
    action_log = [
        {"faction_id": "iron_dominion", "action": "attack", "target_region": "crisis_zone",
         "budget_committed": 400, "tick": 598},
    ]
    event_log = [
        {"template_id": "evt_regional_revolt", "region_id": "pressured", "tick": 595},
    ]
    conquest_log = [
        {"region_id": "lost_territory", "old_faction_id": player_fid,
         "new_faction_id": "iron_dominion", "tick": 570},
    ]

    # Lineage: operated in crisis_zone and pressured, currently in crisis_zone
    # Expert at defensive_stand (3 past missions), some siege_breaking experience
    ledger = MockLedger(
        lineage_regions=["crisis_zone", "pressured"],
        active_regions={"crisis_zone"},
        archetype_history={"defensive_stand": 3, "siege_breaking": 1},
    )
    current_lineage_id = "lineage_001"

    # Preferences: likes defensive_stand and assault, rare = evacuation and multi_front
    player_preferences = {
        "defensive_stand": 0.9,
        "assault": 0.8,
        "evacuation": "rare",
        "multi_front_defense": "rare",
    }

    # ── Step 1: Build candidate pool ──
    candidates = build_candidate_pool(
        world, registry, player_fid, event_log, action_log,
        conquest_log, tick)

    print(f"\n{'─'*70}")
    print(f"  Step 1 — Candidate Pool ({len(candidates)} candidates)")
    print(f"{'─'*70}")
    for c in candidates:
        print(f"    ({c['region_id']}, {c['archetype']})")

    # ── Step 2: Score candidates ──
    scored = score_candidates(
        candidates, world, registry, player_fid,
        event_log, action_log, conquest_log, tick,
        ledger=ledger, current_lineage_id=current_lineage_id,
        player_preferences=player_preferences)

    print(f"\n{'─'*70}")
    print(f"  Step 2 — Scored Candidates (sorted by final score)")
    print(f"{'─'*70}")
    print(f"  {'#':<4} {'Region':<18} {'Archetype':<22} {'Urgency':>7} {'Relev':>7} {'Pref':>7} {'Score':>7}")
    print(f"  {'─'*4} {'─'*18} {'─'*22} {'─'*7} {'─'*7} {'─'*7} {'─'*7}")

    top_n = config.GENERATOR_TOP_N_CANDIDATES
    for i, s in enumerate(scored):
        marker = " [TOP]" if i < top_n else ""
        print(f"  {i+1:<4} {s['region_id']:<18} {s['archetype']:<22} "
              f"{s['urgency']:>7.3f} {s['relevance']:>7.3f} {s['preference']:>7.3f} "
              f"{s['score']:>7.3f}{marker}")

    # ── Analysis ──
    print(f"\n{'─'*70}")
    print(f"  Analysis")
    print(f"{'─'*70}")

    if scored:
        top = scored[0]
        print(f"\n  Top candidate: ({top['region_id']}, {top['archetype']}) score={top['score']:.3f}")
        print(f"    Urgency={top['urgency']:.3f}  Relevance={top['relevance']:.3f}  Preference={top['preference']:.3f}")

    top_5_regions = set(s["region_id"] for s in scored[:top_n])
    print(f"\n  Crisis zone in top {top_n}: {'crisis_zone' in top_5_regions}")
    print(f"  Pressured in top {top_n}: {'pressured' in top_5_regions}")

    rare_candidates = [s for s in scored if s["archetype"] in ("evacuation", "multi_front_defense")]
    if rare_candidates:
        print(f"\n  Rare archetype candidates ({len(rare_candidates)}):")
        for r in rare_candidates:
            rank = scored.index(r) + 1
            print(f"    #{rank} ({r['region_id']}, {r['archetype']}) score={r['score']:.3f} pref={r['preference']:.3f}")

    has_connection = [s for s in scored if s["relevance"] > 0.0]
    no_connection = [s for s in scored if s["relevance"] == 0.0]
    print(f"\n  With lineage connection: {len(has_connection)}")
    print(f"  Without lineage connection: {len(no_connection)}")

    preferred = [s for s in scored if s["preference"] >= 0.8]
    default = [s for s in scored if s["preference"] == config.GENERATOR_DEFAULT_PREFERENCE]
    rare = [s for s in scored if s["preference"] == config.GENERATOR_RARE_PREFERENCE]
    print(f"  Preferred (>=0.8): {len(preferred)}, Default (0.5): {len(default)}, Rare (0.1): {len(rare)}")

    print(f"\n{'═'*70}")
    print(f"  Checkpoint C — Complete")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
