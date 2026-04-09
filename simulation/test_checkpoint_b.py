#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from mission_generator import TRIGGER_FUNCTIONS


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


def run_triggers(label, region, world, registry, player_fid,
                 event_log, action_log, conquest_log, tick, expected):
    print(f"\n  {'─'*60}")
    print(f"  TEST: {label}")
    print(f"  Region: {region.id} (faction={region.faction_id}, "
          f"mil={region.fields['military']}, eco={region.fields['economy']}, "
          f"stab={region.composites.get('stability', '?')})")
    print(f"  {'─'*60}")

    all_ok = True
    for archetype, fn in TRIGGER_FUNCTIONS.items():
        fired, ctx = fn(region, world, registry, player_fid,
                        event_log, action_log, conquest_log, tick)
        exp = expected.get(archetype, False)
        match = fired == exp
        icon = "+" if match else "X"
        status = "FIRE" if fired else "    "
        exp_str = "FIRE" if exp else "    "
        ctx_str = f"  ctx: {ctx}" if fired else ""
        line = f"    {icon} {archetype:<24} {status}  (expected: {exp_str})"
        if not match:
            line += "  MISMATCH"
        line += ctx_str
        print(line)
        if not match:
            all_ok = False

    return all_ok


def main():
    print(f"\n{'═'*70}")
    print(f"  Stage 5.5 Checkpoint B — Trigger Conditions")
    print(f"{'═'*70}")

    player_fid = "player_civ"

    r_home = MockRegion("home", player_fid,
                        fields={"military": 35, "economy": 30, "tension": 55, "population": 50},
                        composites={"stability": 30, "capacity": 40})
    r_enemy_a = MockRegion("enemy_a", "iron_dominion",
                           fields={"military": 70, "economy": 60, "tension": 20, "population": 70},
                           composites={"stability": 65, "capacity": 60})
    r_enemy_b = MockRegion("enemy_b", "warlord_clan",
                           fields={"military": 65, "economy": 45, "tension": 30, "population": 55},
                           composites={"stability": 50, "capacity": 45})
    r_breakaway = MockRegion("breakaway_zone", "breakaway_revolt",
                             fields={"military": 30, "economy": 25, "tension": 60, "population": 35},
                             composites={"stability": 20, "capacity": 25},
                             held_since_tick=400)
    r_stable = MockRegion("stable_core", player_fid,
                          fields={"military": 75, "economy": 80, "tension": 15, "population": 85},
                          composites={"stability": 75, "capacity": 80})
    r_desperate = MockRegion("desperate", player_fid,
                             fields={"military": 10, "economy": 12, "tension": 80, "population": 30},
                             composites={"stability": 10, "capacity": 15},
                             held_since_tick=0)
    r_conquered = MockRegion("conquered", "iron_dominion",
                             fields={"military": 40, "economy": 35, "tension": 50, "population": 40},
                             composites={"stability": 35, "capacity": 35})
    r_siege = MockRegion("sieged", player_fid,
                         fields={"military": 25, "economy": 20, "tension": 65, "population": 40},
                         composites={"stability": 22, "capacity": 30},
                         held_since_tick=200)
    r_far_enemy = MockRegion("far_enemy", "distant_horde",
                             fields={"military": 80, "economy": 50, "tension": 20, "population": 60},
                             composites={"stability": 60, "capacity": 50})
    r_expanding = MockRegion("expanding_zone", "iron_dominion",
                             fields={"military": 60, "economy": 55, "tension": 25, "population": 60},
                             composites={"stability": 55, "capacity": 50})

    all_regions = [r_home, r_enemy_a, r_enemy_b, r_breakaway, r_stable,
                   r_desperate, r_conquered, r_siege, r_far_enemy, r_expanding]

    adjacency = {
        "home":            ["enemy_a", "enemy_b", "stable_core", "breakaway_zone", "sieged", "expanding_zone"],
        "enemy_a":         ["home", "conquered", "expanding_zone", "desperate"],
        "enemy_b":         ["home", "sieged"],
        "breakaway_zone":  ["home", "stable_core"],
        "stable_core":     ["home", "breakaway_zone"],
        "desperate":       ["enemy_a", "sieged"],
        "conquered":       ["enemy_a", "expanding_zone"],
        "sieged":          ["home", "enemy_b", "desperate"],
        "far_enemy":       [],
        "expanding_zone":  ["enemy_a", "conquered", "home"],
    }

    world = MockWorld(all_regions, adjacency)

    registry = {
        player_fid: MockFaction(player_fid, "player_civilization",
                                {"iron_dominion": "hostile", "warlord_clan": "hostile",
                                 "breakaway_revolt": "hostile", "distant_horde": "hostile"}),
        "iron_dominion": MockFaction("iron_dominion", "conqueror",
                                     {player_fid: "hostile"}),
        "warlord_clan": MockFaction("warlord_clan", "warlord",
                                     {player_fid: "hostile"}),
        "breakaway_revolt": MockFaction("breakaway_revolt", "breakaway",
                                         {player_fid: "hostile"}),
        "distant_horde": MockFaction("distant_horde", "conqueror",
                                      {player_fid: "hostile"}),
    }

    results = []
    tick = 600

    # ── Test 1: Region under active attack → Defensive Stand
    # Also triggers siege_breaking (held 600 ticks, low fields, hostile neighbors)
    # and multi_front_defense (2 hostile neighbors with mil>50)
    results.append(run_triggers(
        "Player region under attack",
        r_home, world, registry, player_fid,
        event_log=[], action_log=[
            {"faction_id": "iron_dominion", "action": "attack", "target_region": "home",
             "budget_committed": 340, "tick": 598},
        ], conquest_log=[], tick=tick,
        expected={"defensive_stand": True, "siege_breaking": True, "multi_front_defense": True},
    ))

    # ── Test 2: Sustained border friction → Siege Breaking
    results.append(run_triggers(
        "Region under sustained border friction (held 400 ticks, low mil/eco, hostile neighbor mil>50)",
        r_siege, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[], tick=tick,
        expected={"siege_breaking": True},
    ))

    # ── Test 3: Recently conquered region → Reconquest
    results.append(run_triggers(
        "Recently conquered player region",
        r_conquered, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[
            {"region_id": "conquered", "old_faction_id": player_fid,
             "new_faction_id": "iron_dominion", "tick": 580},
        ], tick=tick,
        expected={"reconquest": True},
    ))

    # ── Test 4: Revolt events → Counterinsurgency
    # Also triggers siege_breaking and multi_front_defense (same home region conditions)
    results.append(run_triggers(
        "Player region with active revolt chains",
        r_home, world, registry, player_fid,
        event_log=[
            {"template_id": "evt_regional_revolt", "region_id": "home", "tick": 595},
            {"template_id": "evt_resistance_movement", "region_id": "home", "tick": 597},
        ], action_log=[], conquest_log=[], tick=tick,
        expected={"counterinsurgency": True, "siege_breaking": True, "multi_front_defense": True},
    ))

    # ── Test 5: Critically failing region → Evacuation
    # Also triggers siege_breaking (held 600 ticks, mil<40, eco<40, hostile neighbor)
    results.append(run_triggers(
        "Critically failing region (mil=10, eco=12, stab=10, hostile neighbor)",
        r_desperate, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[], tick=tick,
        expected={"evacuation": True, "siege_breaking": True},
    ))

    # ── Test 6: Young breakaway adjacent → Suppression
    # Also triggers assault (enemy, weak, adjacent to player, hostile)
    results.append(run_triggers(
        "Young breakaway faction adjacent to player",
        r_breakaway, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[], tick=tick,
        expected={"suppression": True, "assault": True},
    ))

    # ── Test 7: Multi-front attack → Multi-Front Defense
    # Also triggers siege_breaking (same home region conditions)
    results.append(run_triggers(
        "Two factions attacking same player region",
        r_home, world, registry, player_fid,
        event_log=[], action_log=[
            {"faction_id": "iron_dominion", "action": "attack", "target_region": "home",
             "budget_committed": 200, "tick": 598},
            {"faction_id": "warlord_clan", "action": "attack", "target_region": "home",
             "budget_committed": 180, "tick": 599},
        ], conquest_log=[], tick=tick,
        expected={"defensive_stand": True, "multi_front_defense": True, "siege_breaking": True},
    ))

    # ── Test 8: Non-adjacent attacker → Interception
    # Also triggers siege_breaking and multi_front_defense (same home region conditions)
    results.append(run_triggers(
        "Non-adjacent faction attacking (interception opportunity)",
        r_home, world, registry, player_fid,
        event_log=[], action_log=[
            {"faction_id": "distant_horde", "action": "attack", "target_region": "home",
             "budget_committed": 500, "tick": 597},
        ], conquest_log=[], tick=tick,
        expected={"defensive_stand": True, "interception": True,
                  "siege_breaking": True, "multi_front_defense": True},
    ))

    # ── Test 9: Weak enemy region adjacent → Assault
    r_weak_enemy = MockRegion("weak_target", "iron_dominion",
                              fields={"military": 30, "economy": 35, "tension": 50, "population": 40},
                              composites={"stability": 30, "capacity": 35})
    world.regions["weak_target"] = r_weak_enemy
    adjacency["weak_target"] = ["home"]
    adjacency["home"].append("weak_target")
    results.append(run_triggers(
        "Weak enemy region adjacent to player",
        r_weak_enemy, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[], tick=tick,
        expected={"assault": True},
    ))
    adjacency["home"].remove("weak_target")

    # ── Test 10: Rapidly expanding faction → Containment
    # Also triggers assault (enemy, adjacent, mil=60 not >60 so passes threshold)
    results.append(run_triggers(
        "Iron Dominion gained 2+ regions, adjacent to player",
        r_expanding, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[
            {"region_id": "conquered", "old_faction_id": player_fid,
             "new_faction_id": "iron_dominion", "tick": 580},
            {"region_id": "expanding_zone", "old_faction_id": "warlord_clan",
             "new_faction_id": "iron_dominion", "tick": 585},
        ], tick=tick,
        expected={"containment": True, "assault": True},
    ))

    # ── Test 11: Stable region, no pressure → NOTHING
    results.append(run_triggers(
        "Stable player region, no external pressure (should fire NOTHING)",
        r_stable, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[], tick=tick,
        expected={},
    ))

    # ── Test 12: Far enemy, not adjacent → NOTHING
    results.append(run_triggers(
        "Far enemy region, not adjacent to player (should fire NOTHING)",
        r_far_enemy, world, registry, player_fid,
        event_log=[], action_log=[], conquest_log=[], tick=tick,
        expected={},
    ))

    # ── Summary ──
    total = len(results)
    passed = sum(results)
    print(f"\n{'═'*70}")
    print(f"  SUMMARY: {passed}/{total} test cases passed")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
