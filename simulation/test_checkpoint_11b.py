import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chronicle_assembler import ScrollEntry
from world_view.time_jump_emitter import build_time_jump_messages


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

    TIME_JUMP_ID = "tj_test_11b"

    time_jump_result = {
        "scroll_entries": scroll_entries,
        "territory_changes": territory_changes,
        "conquests": conquests,
        "ticks_run": 80,
        "start_tick": 0,
        "end_tick": 80,
    }

    messages = build_time_jump_messages(time_jump_result, TIME_JUMP_ID)

    # 1. First message is time_jump_start
    if not messages or messages[0]["type"] != "time_jump_start":
        failures.append(f"First message is not time_jump_start: {messages[0] if messages else 'empty'}")

    # 2. Last message is time_jump_end
    if not messages or messages[-1]["type"] != "time_jump_end":
        failures.append(f"Last message is not time_jump_end: {messages[-1] if messages else 'empty'}")

    # 3. All messages have time_jump_id
    for i, msg in enumerate(messages):
        if msg.get("time_jump_id") != TIME_JUMP_ID:
            failures.append(f"Message {i} ({msg.get('type')}) missing or wrong time_jump_id")

    # 4. Chronicle entries appear before their paired keyframes
    last_seen_entry_id = {}  # entry_id -> index in messages
    for i, msg in enumerate(messages):
        if msg["type"] == "chronicle_entry":
            last_seen_entry_id[msg["entry_id"]] = i
        elif msg["type"] == "keyframe":
            paired_id = msg.get("chronicle_entry_id")
            if paired_id:
                ce_index = last_seen_entry_id.get(paired_id)
                if ce_index is None:
                    failures.append(f"Keyframe at index {i} has chronicle_entry_id={paired_id} but no preceding chronicle_entry found")
                elif ce_index >= i:
                    failures.append(f"chronicle_entry {paired_id} (index {ce_index}) does not precede its keyframe (index {i})")

    # 5. Total message count: 1 start + N keyframes + M chronicle entries + 1 end
    inner = messages[1:-1]
    kf_msgs = [m for m in inner if m["type"] == "keyframe"]
    ce_msgs = [m for m in inner if m["type"] == "chronicle_entry"]
    expected_total = 1 + len(kf_msgs) + len(ce_msgs) + 1
    if len(messages) != expected_total:
        failures.append(f"Total message count {len(messages)} != expected {expected_total}")

    # Print ordered message stream
    print(f"\n{'idx':>4} | {'type':<20} | {'id/index':<20} | {'tick':>6}")
    print("-" * 60)
    for i, msg in enumerate(messages):
        t = msg["type"]
        if t == "time_jump_start":
            label = f"span_years={msg.get('span_years')} kf={msg.get('total_keyframes')} ce={msg.get('total_entries')}"
            tick_str = "—"
        elif t == "time_jump_end":
            label = TIME_JUMP_ID
            tick_str = "—"
        elif t == "chronicle_entry":
            label = msg.get("entry_id", "?")
            tick_str = str(msg.get("tick_range_end", "?"))
        elif t == "keyframe":
            label = f"kf_idx={msg.get('keyframe_index')} ce={msg.get('chronicle_entry_id') or '---'}"
            tick_str = str(msg.get("tick", "?"))
        else:
            label = str(msg)
            tick_str = "?"
        print(f"{i:>4} | {t:<20} | {label:<20} | {tick_str:>6}")

    print(f"\nTotal messages: {len(messages)}  (1 start + {len(kf_msgs)} keyframes + {len(ce_msgs)} chronicle_entries + 1 end)")

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print(f"  FAIL: {f}")
        sys.exit(1)
    else:
        print("\nAll checks passed.")


if __name__ == "__main__":
    run()
