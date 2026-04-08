#!/usr/bin/env python3
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from chronicle_distiller import distill, score_event
from chronicle_assembler import assemble_scroll, ScrollEntry


class MockRegion:
    def __init__(self, rid, faction_id, tier="frontier"):
        self.id = rid
        self.display_name = rid
        self.faction_id = faction_id
        self.tier = tier
        self.fields = {"economy": 50, "military": 40, "tension": 25, "population": 60}
        self.composites = {"stability": 55, "capacity": 50}


class MockWorld:
    def __init__(self):
        self.regions = {
            "alpha": MockRegion("alpha", "player_civilization"),
            "beta": MockRegion("beta", "player_civilization"),
            "gamma": MockRegion("gamma", "conqueror"),
            "delta": MockRegion("delta", "fortifier"),
            "epsilon": MockRegion("epsilon", "opportunist"),
        }
        self._neighbors = {
            "alpha": ["beta", "gamma"],
            "beta": ["alpha", "delta"],
            "gamma": ["alpha", "epsilon"],
            "delta": ["beta", "epsilon"],
            "epsilon": ["gamma", "delta"],
        }

    def get_neighbors(self, rid):
        return self._neighbors.get(rid, [])


class MockCharacter:
    def __init__(self, char_id, name, faction_id, region_id, rank, lineage_id=None):
        self.id = char_id
        self.name = name
        self.faction_id = faction_id
        self.region_id = region_id
        self.rank = rank
        self.lineage_id = lineage_id
        self.event_history = []


class MockLedger:
    def __init__(self):
        self._characters = {
            "char_1": MockCharacter("char_1", "Kael Ashford", "player_civilization", "alpha", "supreme_commander", "lineage_1"),
            "char_2": MockCharacter("char_2", "Maren Ashford", "player_civilization", "alpha", "lineage_member", "lineage_1"),
            "char_3": MockCharacter("char_3", "Dorin Vex", "conqueror", "gamma", "supreme_commander"),
            "char_4": MockCharacter("char_4", "Suranna Thal", "player_civilization", "beta", "regional_commander", "lineage_1"),
        }
        self._lineages = {
            "lineage_1": {"root_id": "char_1", "member_ids": ["char_1", "char_2", "char_4"]},
        }

    def lineage_in_region(self, lineage_id, region_id):
        lin = self._lineages.get(lineage_id)
        if not lin:
            return False
        return any(self._characters[cid].region_id == region_id
                   for cid in lin["member_ids"]
                   if cid in self._characters)

    def get_character_by_id(self, char_id):
        return self._characters.get(char_id)

    def get_lineage_members(self, lineage_id):
        lin = self._lineages.get(lineage_id)
        if not lin:
            return []
        return [self._characters[cid] for cid in lin["member_ids"]
                if cid in self._characters]

    def get_lineage_history(self, lineage_id):
        members = self.get_lineage_members(lineage_id)
        regions = []
        seen = set()
        for m in members:
            if m.region_id not in seen:
                regions.append(m.region_id)
                seen.add(m.region_id)
        return regions


def build_mock_event_log():
    events = [
        # Consequence events (mission aftermath in alpha)
        {"template_id": "evt_garrison_collapse", "name": "Garrison Collapse", "region_id": "alpha", "tick": 5,
         "field_deltas": {"military": -3, "tension": 4}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": True, "character_id": "char_1"},
        {"template_id": "evt_emergency_levy", "name": "Emergency Levy", "region_id": "alpha", "tick": 8,
         "field_deltas": {"military": 3, "economy": -2, "tension": 2}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": True, "character_id": None},

        # Lineage events in alpha (player lineage home)
        {"template_id": "evt_trade_boom", "name": "Trade Boom", "region_id": "alpha", "tick": 12,
         "field_deltas": {"economy": 4, "population": 1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": "char_2"},
        {"template_id": "evt_cultural_festival", "name": "Cultural Festival", "region_id": "alpha", "tick": 18,
         "field_deltas": {"tension": -2, "economy": 1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},

        # Lineage events in beta (lineage member there)
        {"template_id": "evt_border_incursion", "name": "Border Incursion", "region_id": "beta", "tick": 10,
         "field_deltas": {"military": -2, "economy": -2, "tension": 3}, "chain_tag": "chain_0001", "chain_length": 2,
         "mission_consequence": False, "character_id": "char_4"},
        {"template_id": "evt_emergency_levy", "name": "Emergency Levy", "region_id": "beta", "tick": 14,
         "field_deltas": {"military": 3, "economy": -2, "tension": 2}, "chain_tag": "chain_0001", "chain_length": 2,
         "mission_consequence": False, "character_id": None},

        # Chain events in gamma (conqueror territory, military crisis)
        {"template_id": "evt_garrison_collapse", "name": "Garrison Collapse", "region_id": "gamma", "tick": 3,
         "field_deltas": {"military": -5, "tension": 6}, "chain_tag": "chain_0002", "chain_length": 3,
         "mission_consequence": False, "character_id": "char_3"},
        {"template_id": "evt_border_incursion", "name": "Border Incursion", "region_id": "gamma", "tick": 7,
         "field_deltas": {"military": -3, "economy": -2, "tension": 4}, "chain_tag": "chain_0002", "chain_length": 3,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_regional_revolt", "name": "Regional Revolt", "region_id": "gamma", "tick": 13,
         "field_deltas": {"military": -2, "economy": -2, "tension": 5}, "chain_tag": "chain_0002", "chain_length": 3,
         "mission_consequence": False, "character_id": None},

        # Chain events in delta (fortifier territory, economic)
        {"template_id": "evt_trade_boom", "name": "Trade Boom", "region_id": "delta", "tick": 6,
         "field_deltas": {"economy": 5, "population": 2}, "chain_tag": "chain_0003", "chain_length": 2,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_prosperity_unrest", "name": "Prosperity Unrest", "region_id": "delta", "tick": 15,
         "field_deltas": {"tension": 3, "economy": -1}, "chain_tag": "chain_0003", "chain_length": 2,
         "mission_consequence": False, "character_id": None},

        # Standalone events in epsilon
        {"template_id": "evt_trade_boom", "name": "Trade Boom", "region_id": "epsilon", "tick": 4,
         "field_deltas": {"economy": 3, "population": 1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_famine", "name": "Famine", "region_id": "epsilon", "tick": 11,
         "field_deltas": {"population": -4, "economy": -2, "tension": 3}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_emergency_levy", "name": "Emergency Levy", "region_id": "epsilon", "tick": 16,
         "field_deltas": {"military": 2, "economy": -1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},

        # More standalone events across regions for volume
        {"template_id": "evt_cultural_festival", "name": "Cultural Festival", "region_id": "delta", "tick": 20,
         "field_deltas": {"tension": -1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_garrison_collapse", "name": "Garrison Collapse", "region_id": "epsilon", "tick": 22,
         "field_deltas": {"military": -3, "tension": 3}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},

        # Additional events to reach ~30
        {"template_id": "evt_trade_boom", "name": "Trade Boom", "region_id": "alpha", "tick": 25,
         "field_deltas": {"economy": 3}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_border_incursion", "name": "Border Incursion", "region_id": "gamma", "tick": 19,
         "field_deltas": {"military": -2, "tension": 2}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_emergency_levy", "name": "Emergency Levy", "region_id": "gamma", "tick": 23,
         "field_deltas": {"military": 3, "economy": -1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_famine", "name": "Famine", "region_id": "beta", "tick": 21,
         "field_deltas": {"population": -3, "economy": -1, "tension": 2}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_trade_boom", "name": "Trade Boom", "region_id": "delta", "tick": 24,
         "field_deltas": {"economy": 2, "population": 1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},

        # A few more for density
        {"template_id": "evt_cultural_festival", "name": "Cultural Festival", "region_id": "alpha", "tick": 28,
         "field_deltas": {"tension": -2}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_garrison_collapse", "name": "Garrison Collapse", "region_id": "delta", "tick": 26,
         "field_deltas": {"military": -2, "tension": 3}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_border_incursion", "name": "Border Incursion", "region_id": "epsilon", "tick": 27,
         "field_deltas": {"military": -1, "economy": -1, "tension": 2}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_trade_boom", "name": "Trade Boom", "region_id": "beta", "tick": 29,
         "field_deltas": {"economy": 2}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_emergency_levy", "name": "Emergency Levy", "region_id": "alpha", "tick": 30,
         "field_deltas": {"military": 2, "economy": -1, "tension": 1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},

        # Chain in epsilon
        {"template_id": "evt_regional_revolt", "name": "Regional Revolt", "region_id": "epsilon", "tick": 17,
         "field_deltas": {"military": -2, "tension": 5}, "chain_tag": "chain_0004", "chain_length": 2,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_revolt_crushed", "name": "Revolt Crushed", "region_id": "epsilon", "tick": 20,
         "field_deltas": {"military": -1, "tension": -3}, "chain_tag": "chain_0004", "chain_length": 2,
         "mission_consequence": False, "character_id": None},

        # Two more standalones
        {"template_id": "evt_famine", "name": "Famine", "region_id": "gamma", "tick": 28,
         "field_deltas": {"population": -2, "economy": -1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
        {"template_id": "evt_cultural_festival", "name": "Cultural Festival", "region_id": "beta", "tick": 30,
         "field_deltas": {"tension": -1}, "chain_tag": "", "chain_length": 0,
         "mission_consequence": False, "character_id": None},
    ]
    return events


def main():
    print("=" * 60)
    print("CHECKPOINT H: Chronicle Distiller + Assembler")
    print("=" * 60)

    event_log = build_mock_event_log()
    ledger = MockLedger()
    world = MockWorld()
    player_lineage_id = "lineage_1"
    last_mission_region = "alpha"
    last_mission_outcome = "mixed"
    mission_info = {
        "outcome": "a pyrrhic defense that held the line but left the garrison shattered",
        "archetype": "defensive_stand",
        "region": "alpha",
    }

    print(f"\nInput: {len(event_log)} events across {len(set(e['region_id'] for e in event_log))} regions")
    print(f"Player lineage: {player_lineage_id} (members in alpha, beta)")
    print(f"Last mission: {last_mission_outcome} in {last_mission_region}")

    # Pass 1: score all events
    print("\n--- Pass 1: Significance Scoring ---\n")
    scores = []
    for evt in event_log:
        s = score_event(evt, ledger, player_lineage_id, last_mission_region)
        scores.append((evt, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    print(f"  Score range: {scores[-1][1]:.2f} – {scores[0][1]:.2f}")
    print(f"  Top 5 events:")
    for evt, s in scores[:5]:
        print(f"    {s:5.2f}  {evt['name']:25s} in {evt['region_id']:8s} tick={evt['tick']}")

    # Pass 2+3: distill and assemble
    print("\n--- Pass 2: Clustering ---\n")
    clusters = distill(event_log, ledger, player_lineage_id, last_mission_region,
                       last_mission_outcome, world)

    print(f"  Selected {len(clusters)} clusters:")
    for i, c in enumerate(clusters):
        print(f"    [{i+1}] {c.cluster_type:12s} | {c.category:30s} | "
              f"region={c.region_id:8s} | events={len(c.events)} | "
              f"peak={c.peak_score:.2f} | ticks={c.tick_range}")

    # Verify structural claims
    print("\n--- Structural Checks ---\n")
    n = len(clusters)
    k1 = 5 <= n <= 10
    print(f"  K1 (5-10 entries): {n} — {'PASS' if k1 else 'FAIL'}")

    has_lineage = any(c.cluster_type == "lineage" for c in clusters)
    print(f"  K2 (lineage present): {'PASS' if has_lineage else 'FAIL'}")

    k3 = True
    if clusters and clusters[0].cluster_type == "consequence":
        print(f"  K3 (consequence first): PASS")
    elif any(c.cluster_type == "consequence" for c in clusters):
        print(f"  K3 (consequence first): FAIL — consequence exists but not first")
        k3 = False
    else:
        print(f"  K3 (consequence first): N/A — no consequence cluster")

    # Pass 3: assemble
    print("\n--- Pass 3: Assembly ---\n")
    entries, warnings = assemble_scroll(clusters, ledger, player_lineage_id, world,
                                        mission_info, seed=42)

    print(f"  Assembled {len(entries)} scroll entries")
    if warnings:
        print(f"  Warnings: {len(warnings)}")
        for w in warnings:
            print(f"    {w}")

    # K4: word counts
    print("\n--- K4: Word Count Check ---\n")
    k4_pass = True
    for entry in entries:
        base_wc = len(entry.base_text.split())
        exp_wc = len(entry.expanded_text.split())
        status = "OK"
        if base_wc >= 90 or exp_wc >= 140:
            status = "OVER"
            k4_pass = False
        print(f"  {entry.category:30s} base={base_wc:3d} expanded={exp_wc:3d} {status}")
    print(f"\n  K4 (word limits): {'PASS' if k4_pass else 'WARNING — some entries over limit'}")

    # K5: unresolved slots
    print("\n--- K5: Slot Resolution Check ---\n")
    import re
    k5_pass = True
    for entry in entries:
        unresolved = re.findall(r"\{[a-z_]+\}", entry.expanded_text)
        if unresolved:
            print(f"  {entry.category}: UNRESOLVED: {unresolved}")
            k5_pass = False
    print(f"  K5 (all slots resolved): {'PASS' if k5_pass else 'FAIL'}")

    # Print assembled scroll
    print("\n--- Assembled Scroll ---\n")
    for i, entry in enumerate(entries):
        print(f"  [{i+1}] {entry.cluster_type} / {entry.category}")
        print(f"      Region: {entry.region_id} | Ticks: {entry.tick_range}")
        print(f"      Fragments: {entry.fragment_ids}")
        print(f"      Base ({len(entry.base_text.split())}w):")
        print(f"        \"{entry.base_text}\"")
        print(f"      Expanded ({len(entry.expanded_text.split())}w):")
        print(f"        \"{entry.expanded_text}\"")
        print()

    print("=" * 60)
    all_pass = k1 and has_lineage and k3 and k5_pass
    print(f"CHECKPOINT H: {'PASS' if all_pass else 'ISSUES FOUND'}")
    if not k4_pass:
        print("  (K4 word limit warnings are non-blocking per spec)")
    print("=" * 60)


if __name__ == "__main__":
    main()
