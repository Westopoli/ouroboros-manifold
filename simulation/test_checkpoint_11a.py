import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


def run():
    failures = []

    scroll_entries = [
        make_entry("Entry A base", "Entry A expanded", 10, 20, "r_01"),
        make_entry("Entry B base", "Entry B expanded", 30, 50, "r_02"),
        make_entry("Entry C base", "Entry C expanded", 60, 80, "r_03"),
    ]

    territory_changes = [
        {"region_id": "r_04", "old_faction": "f_alpha", "new_faction": "f_beta"},
        {"region_id": "r_05", "old_faction": "f_beta", "new_faction": "f_gamma"},
        {"region_id": "r_02", "old_faction": "f_delta", "new_faction": "f_alpha"},
    ]

    conquests = [
        {"attacker": "f_beta", "defender": "f_alpha", "region_id": "r_04", "tick": 15},
        {"attacker": "f_gamma", "defender": "f_beta", "region_id": "r_05", "tick": 90},
        {"attacker": "f_alpha", "defender": "f_delta", "region_id": "r_02", "tick": 40},
    ]

    time_jump_result = {
        "scroll_entries": scroll_entries,
        "territory_changes": territory_changes,
        "conquests": conquests,
        "ticks_run": 80,
        "start_tick": 0,
        "end_tick": 80,
    }

    keyframes = select_keyframes(time_jump_result)

    # 1. Every scroll entry produced a keyframe with matching tick_range
    chronicle_kfs = [kf for kf in keyframes if kf["chronicle_entry_id"] is not None]
    if len(chronicle_kfs) != len(scroll_entries):
        failures.append(f"Expected {len(scroll_entries)} chronicle keyframes, got {len(chronicle_kfs)}")

    for kf in chronicle_kfs:
        matched = False
        for entry in scroll_entries:
            if kf["tick_range_start"] == entry.tick_range[0] and kf["tick_range_end"] == entry.tick_range[1]:
                matched = True
                break
        if not matched:
            failures.append(f"Keyframe {kf['entry_id']} tick_range ({kf['tick_range_start']},{kf['tick_range_end']}) not matched to any scroll entry")

    # 2. r_04 conquest tick=15 falls in entry A range (10-20) → absorbed
    entry_a_kf = next((kf for kf in keyframes if kf["tick_range_start"] == 10 and kf["tick_range_end"] == 20), None)
    if entry_a_kf is None:
        failures.append("Entry A keyframe (10-20) not found")
    else:
        r04_changes = [oc for oc in entry_a_kf["ownership_changes"] if oc["region_id"] == "r_04"]
        if not r04_changes:
            failures.append("r_04 ownership change not absorbed into entry A keyframe (10-20)")

    # 3. r_02 conquest tick=40 falls in entry B range (30-50) → absorbed
    entry_b_kf = next((kf for kf in keyframes if kf["tick_range_start"] == 30 and kf["tick_range_end"] == 50), None)
    if entry_b_kf is None:
        failures.append("Entry B keyframe (30-50) not found")
    else:
        r02_changes = [oc for oc in entry_b_kf["ownership_changes"] if oc["region_id"] == "r_02"]
        if not r02_changes:
            failures.append("r_02 ownership change not absorbed into entry B keyframe (30-50)")

    # 4. r_05 conquest tick=90 outside all scroll entry ranges → standalone keyframe
    standalone_kfs = [kf for kf in keyframes if kf["chronicle_entry_id"] is None]
    r05_standalone = [kf for kf in standalone_kfs
                      if any(oc["region_id"] == "r_05" for oc in kf["ownership_changes"])]
    if not r05_standalone:
        failures.append("r_05 standalone ownership keyframe not created (conquest tick=90 outside all ranges)")

    # 5. All keyframes ordered by tick ascending
    ticks = [kf["tick"] for kf in keyframes]
    if ticks != sorted(ticks):
        failures.append(f"Keyframes not sorted by tick: {ticks}")

    # 6. JSON round-trip via keyframe_message
    TIME_JUMP_ID = "tj_test_001"
    messages = keyframes_to_messages(keyframes, TIME_JUMP_ID)
    for msg in messages:
        try:
            roundtrip = json.loads(json.dumps(msg))
            assert roundtrip == msg
        except Exception as e:
            failures.append(f"JSON round-trip failed for keyframe: {e}")
            break

    scroll_msgs = scroll_entries_to_messages(scroll_entries, keyframes, TIME_JUMP_ID)
    for msg in scroll_msgs:
        try:
            json.loads(json.dumps(msg))
        except Exception as e:
            failures.append(f"JSON round-trip failed for scroll entry message: {e}")
            break

    start_msg, end_msg = time_jump_lifecycle_messages(TIME_JUMP_ID, 25, len(keyframes), len(scroll_entries))
    assert start_msg["type"] == "time_jump_start"
    assert end_msg["type"] == "time_jump_end"

    # Print table
    print(f"\n{'tick':>6} | {'entry_id':<10} | {'chronicle_id':<14} | {'own_changes':>11} | {'mil_events':>10}")
    print("-" * 65)
    for kf in keyframes:
        cid = kf["chronicle_entry_id"] if kf["chronicle_entry_id"] else "---"
        print(f"{kf['tick']:>6} | {kf['entry_id']:<10} | {cid:<14} | {len(kf['ownership_changes']):>11} | {len(kf['military_events']):>10}")

    print(f"\nTotal keyframes: {len(keyframes)}")
    print(f"Chronicle keyframes: {len(chronicle_kfs)}")
    print(f"Standalone keyframes: {len(standalone_kfs)}")
    print(f"Transport messages: {len(messages)} keyframe, {len(scroll_msgs)} chronicle_entry")

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print(f"  FAIL: {f}")
        sys.exit(1)
    else:
        print("\nAll checks passed.")


if __name__ == "__main__":
    run()
