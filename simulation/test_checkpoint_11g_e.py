import sys
import os
import json
import copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from chronicle_assembler import ScrollEntry
from world_view.keyframe_selector import select_keyframes
from world_view.keyframe_message import (
    keyframes_to_messages,
    scroll_entries_to_messages,
    time_jump_lifecycle_messages,
)


def make_entry(base, expanded, tick_start, tick_end, region_id="r_01"):
    return ScrollEntry(
        base_text=base,
        expanded_text=expanded,
        cluster_type="conflict",
        category="conflict",
        region_id=region_id,
        tick_range=(tick_start, tick_end),
    )


def build_fixture():
    scroll_entries = [
        make_entry("Entry A base", "Entry A expanded", 10, 20, "r_01"),
        make_entry("Entry B base", "Entry B expanded", 30, 50, "r_02"),
        make_entry("Entry C base", "Entry C expanded", 60, 80, "r_03"),
    ]
    territory_changes = [
        {"region_id": "r_04", "old_faction": "f_alpha", "new_faction": "f_beta"},
        {"region_id": "r_05", "old_faction": "f_beta",  "new_faction": "f_gamma"},
        {"region_id": "r_02", "old_faction": "f_delta", "new_faction": "f_alpha"},
    ]
    conquests = [
        {"attacker": "f_beta",  "defender": "f_alpha", "region_id": "r_04", "tick": 15},
        {"attacker": "f_gamma", "defender": "f_beta",  "region_id": "r_05", "tick": 90},
        {"attacker": "f_alpha", "defender": "f_delta", "region_id": "r_02", "tick": 40},
    ]
    start_ownership = {
        "r_01": "f_alpha", "r_02": "f_delta", "r_03": "f_alpha",
        "r_04": "f_alpha", "r_05": "f_beta",
    }
    return {
        "scroll_entries": scroll_entries,
        "territory_changes": territory_changes,
        "conquests": conquests,
        "ticks_run": 80,
        "start_tick": 0,
        "end_tick": 80,
        "region_populations": {"r_01": 100.0, "r_02": 60.0, "r_03": 30.0, "r_04": 80.0, "r_05": 50.0},
        "adjacency": {"r_01": ["r_02"], "r_02": ["r_01", "r_03"], "r_03": ["r_02"]},
        "edge_types": {("r_01", "r_02"): "both", ("r_02", "r_03"): "both"},
    }, start_ownership


def stage_11g_metadata():
    region_metadata = {
        "r_01": {"name": "Veraxis Reach", "tier": "home",     "military": 72, "economy": 55, "tension": 30, "population": 100},
        "r_02": {"name": "Tepan-Dazur",   "tier": "frontier", "military": 40, "economy": 38, "tension": 65, "population": 60},
        "r_03": {"name": "Hollow Span",   "tier": "frontier", "military": 25, "economy": 20, "tension": 50, "population": 30},
        "r_04": {"name": "Skarath Umal",  "tier": "frontier", "military": 60, "economy": 45, "tension": 70, "population": 80},
        "r_05": {"name": "Pellis Veil",   "tier": "empty",    "military": 18, "economy": 12, "tension": 35, "population": 50},
    }
    faction_metadata = {
        "f_alpha": {"name": "Dominion of Vaer", "archetype": "expansionist", "tech_tier": 3},
        "f_beta":  {"name": "Kestrel Compact",  "archetype": "balanced",     "tech_tier": 2},
        "f_gamma": {"name": "Pellian Order",    "archetype": "isolationist", "tech_tier": 2},
        "f_delta": {"name": "Outer Spiral",     "archetype": "raider",       "tech_tier": 1},
    }
    mentions_by_entry = {
        "ce_0000": [{"kind": "region", "id": "r_01", "span_start": 0, "span_end": 11}],
        "ce_0001": [{"kind": "faction", "id": "f_alpha", "span_start": 5, "span_end": 19}],
        "ce_0002": [{"kind": "region", "id": "r_03", "span_start": 0, "span_end": 11}],
    }
    ownership_history = {
        "factions": {
            "f_alpha": {"region_count_history": [3, 4, 3], "delta": -1, "status": "Waning"},
            "f_beta":  {"region_count_history": [2, 1, 1], "delta":  0, "status": "Stable"},
            "f_gamma": {"region_count_history": [0, 0, 1], "delta": +1, "status": "Rising"},
            "f_delta": {"region_count_history": [1, 0, 0], "delta":  0, "status": "Defeated"},
        },
        "regions": {
            "r_02": {"previous_owners": ["f_delta"]},
            "r_04": {"previous_owners": ["f_alpha"]},
            "r_05": {"previous_owners": ["f_beta"]},
        },
    }
    return region_metadata, faction_metadata, mentions_by_entry, ownership_history


def run_pipeline(time_jump_result, start_ownership, scroll_entries,
                 mentions_by_entry=None, ownership_history=None):
    keyframes = select_keyframes(time_jump_result, start_ownership=start_ownership)
    kf_msgs = keyframes_to_messages(keyframes, "tj_test")
    ce_msgs = scroll_entries_to_messages(scroll_entries, keyframes, "tj_test",
                                         mentions_by_entry=mentions_by_entry)
    start_msg, end_msg = time_jump_lifecycle_messages(
        "tj_test", 25, len(keyframes), len(scroll_entries),
        ownership_history=ownership_history,
    )
    return {
        "keyframes": keyframes,
        "kf_msgs": kf_msgs,
        "ce_msgs": ce_msgs,
        "start_msg": start_msg,
        "end_msg": end_msg,
    }


def force_flags(faction_palette, inspection_panels, chronicle_mentions, ownership_history):
    config.ENABLE_FACTION_PALETTE    = faction_palette
    config.ENABLE_INSPECTION_PANELS  = inspection_panels
    config.ENABLE_CHRONICLE_MENTIONS = chronicle_mentions
    config.ENABLE_OWNERSHIP_HISTORY  = ownership_history


def main():
    fixture, start_ownership = build_fixture()
    scroll_entries = fixture["scroll_entries"]
    region_metadata, faction_metadata, mentions_by_entry, oh_payload = stage_11g_metadata()

    # ── Pass 1: ALL FLAGS OFF, no extra metadata supplied ────────────────
    force_flags(False, False, False, False)
    off = run_pipeline(
        copy.deepcopy(fixture), start_ownership, scroll_entries,
        mentions_by_entry=None, ownership_history=None,
    )

    # ── Pass 2: ALL FLAGS OFF, but caller did pass metadata.
    # Must still be bit-identical (gating, not opportunistic merging). ────
    fixture_with_meta = copy.deepcopy(fixture)
    fixture_with_meta["region_metadata"] = region_metadata
    fixture_with_meta["faction_metadata"] = faction_metadata
    off_meta_present = run_pipeline(
        fixture_with_meta, start_ownership, scroll_entries,
        mentions_by_entry=mentions_by_entry, ownership_history=oh_payload,
    )

    # ── Pass 3: ALL FLAGS ON, metadata supplied ─────────────────────────
    force_flags(True, True, True, True)
    fixture_on = copy.deepcopy(fixture)
    fixture_on["region_metadata"] = region_metadata
    fixture_on["faction_metadata"] = faction_metadata
    on = run_pipeline(
        fixture_on, start_ownership, scroll_entries,
        mentions_by_entry=mentions_by_entry, ownership_history=oh_payload,
    )

    # Reset flags to default so we don't leak state.
    force_flags(False, False, False, False)

    # ── Verifications ────────────────────────────────────────────────────
    failures = []

    def assert_eq(label, a, b):
        if a != b:
            failures.append(f"{label}: NOT EQUAL")

    # 1. Flags off + no metadata == flags off + metadata supplied (proves gating)
    assert_eq("flags-off bit-identical regardless of caller-supplied metadata",
              json.dumps(off, default=str, sort_keys=True),
              json.dumps(off_meta_present, default=str, sort_keys=True))

    # 2. With flags off, no new keys appear
    for kf in off["keyframes"]:
        if "factions" in kf:
            failures.append("flags-off keyframe contains 'factions' key — leak")
        for snap in kf.get("regions_snapshot", []):
            for k in ("name", "tier", "military", "economy", "tension", "population"):
                if k in snap:
                    failures.append(f"flags-off region_snapshot leaked key '{k}'")
    for ce in off["ce_msgs"]:
        if "mentions" in ce:
            failures.append("flags-off chronicle msg leaked 'mentions'")
    if "ownership_history" in off["start_msg"]:
        failures.append("flags-off start_msg leaked 'ownership_history'")

    # 3. With flags on, new keys ARE present
    on_kf = on["keyframes"][0]
    if "factions" not in on_kf:
        failures.append("flags-on missing 'factions' on keyframe")
    elif len(on_kf["factions"]) != 4:
        failures.append(f"flags-on factions count wrong: {len(on_kf['factions'])}")

    on_snap0 = on["keyframes"][0].get("regions_snapshot", [{}])[0]
    for k in ("name", "tier", "military", "economy", "tension", "population"):
        if k not in on_snap0:
            failures.append(f"flags-on region snapshot missing '{k}'")

    on_ce0 = on["ce_msgs"][0]
    if "mentions" not in on_ce0:
        failures.append("flags-on chronicle msg missing 'mentions'")

    if "ownership_history" not in on["start_msg"]:
        failures.append("flags-on start_msg missing 'ownership_history'")

    # 4. Existing original keys still present and unchanged when flags on
    base_keys = {"region_id", "owner_faction_id", "significance", "x", "y", "z"}
    for k in base_keys:
        if k not in on_snap0:
            failures.append(f"flags-on region snapshot lost original key '{k}'")
        if off["keyframes"][0]["regions_snapshot"][0].get(k) != on_snap0.get(k):
            failures.append(f"flags-on changed value of original key '{k}'")

    # ── Print samples ────────────────────────────────────────────────────
    print("=== Checkpoint E — keyframe payload extension prove-it ===\n")

    print("--- FLAGS OFF: regions_snapshot[0] of keyframe[0] ---")
    print(json.dumps(off["keyframes"][0]["regions_snapshot"][0], indent=2, sort_keys=True))
    print("")
    print("--- FLAGS OFF: keys present on keyframe[0] ---")
    print(sorted(off["keyframes"][0].keys()))
    print("")
    print("--- FLAGS OFF: chronicle msg[0] keys ---")
    print(sorted(off["ce_msgs"][0].keys()))
    print("")
    print("--- FLAGS OFF: start_msg keys ---")
    print(sorted(off["start_msg"].keys()))
    print("")

    print("--- FLAGS ON: regions_snapshot[0] of keyframe[0] ---")
    print(json.dumps(on["keyframes"][0]["regions_snapshot"][0], indent=2, sort_keys=True))
    print("")
    print("--- FLAGS ON: factions[] on keyframe[0] ---")
    print(json.dumps(on["keyframes"][0]["factions"], indent=2, sort_keys=True))
    print("")
    print("--- FLAGS ON: chronicle msg[0] (with mentions) ---")
    print(json.dumps(on["ce_msgs"][0], indent=2, sort_keys=True))
    print("")
    print("--- FLAGS ON: start_msg.ownership_history ---")
    print(json.dumps(on["start_msg"]["ownership_history"], indent=2, sort_keys=True))
    print("")

    print("=== diff summary ===")
    off_keys = set(off["keyframes"][0]["regions_snapshot"][0].keys())
    on_keys  = set(on["keyframes"][0]["regions_snapshot"][0].keys())
    print(f"region_snapshot new keys when flags on: {sorted(on_keys - off_keys)}")
    on_kf_top = set(on["keyframes"][0].keys())
    off_kf_top = set(off["keyframes"][0].keys())
    print(f"keyframe top-level new keys when flags on: {sorted(on_kf_top - off_kf_top)}")
    on_ce_keys = set(on["ce_msgs"][0].keys())
    off_ce_keys = set(off["ce_msgs"][0].keys())
    print(f"chronicle msg new keys when flags on: {sorted(on_ce_keys - off_ce_keys)}")
    on_start_keys = set(on["start_msg"].keys())
    off_start_keys = set(off["start_msg"].keys())
    print(f"start_msg new keys when flags on: {sorted(on_start_keys - off_start_keys)}")
    print("")

    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  FAIL: {f}")
        sys.exit(1)
    else:
        print("ALL PASSED")


if __name__ == "__main__":
    main()
