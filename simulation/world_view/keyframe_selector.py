import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _entry_id(index):
    return f"ce_{index:04d}"


def _tick_in_range(tick, tick_range_start, tick_range_end):
    return tick_range_start <= tick <= tick_range_end


def _conquest_tick_for_region(region_id, conquests):
    for c in conquests:
        if c["region_id"] == region_id:
            return c["tick"]
    return None


def select_keyframes(time_jump_result: dict) -> list[dict]:
    scroll_entries = time_jump_result.get("scroll_entries", [])
    territory_changes = time_jump_result.get("territory_changes", [])
    conquests = time_jump_result.get("conquests", [])

    keyframes = []
    for i, entry in enumerate(scroll_entries):
        keyframes.append({
            "entry_id": _entry_id(i),
            "tick": entry.tick_range[1],
            "tick_range_start": entry.tick_range[0],
            "tick_range_end": entry.tick_range[1],
            "chronicle_entry_id": _entry_id(i),
            "ownership_changes": [],
            "military_events": [],
        })

    for tc in territory_changes:
        conquest_tick = _conquest_tick_for_region(tc["region_id"], conquests)

        absorbed = False
        if conquest_tick is not None:
            for kf in keyframes:
                if _tick_in_range(conquest_tick, kf["tick_range_start"], kf["tick_range_end"]):
                    kf["ownership_changes"].append({
                        "region_id": tc["region_id"],
                        "old_faction_id": tc["old_faction"],
                        "new_faction_id": tc["new_faction"],
                    })
                    absorbed = True
                    break

        if not absorbed:
            tick = conquest_tick if conquest_tick is not None else time_jump_result.get("end_tick", 0)
            keyframes.append({
                "entry_id": "",
                "tick": tick,
                "tick_range_start": tick,
                "tick_range_end": tick,
                "chronicle_entry_id": None,
                "ownership_changes": [{
                    "region_id": tc["region_id"],
                    "old_faction_id": tc["old_faction"],
                    "new_faction_id": tc["new_faction"],
                }],
                "military_events": [],
            })

    for conquest in conquests:
        ctick = conquest["tick"]
        target = None
        target_dist = None
        for kf in keyframes:
            if _tick_in_range(ctick, kf["tick_range_start"], kf["tick_range_end"]):
                target = kf
                break
        if target is None:
            for kf in keyframes:
                dist = abs(kf["tick"] - ctick)
                if target_dist is None or dist < target_dist:
                    target = kf
                    target_dist = dist
        if target is not None:
            target["military_events"].append({
                "kind": "conquest",
                "attacker_region_id": conquest["attacker"],
                "defender_region_id": conquest["region_id"],
            })

    keyframes.sort(key=lambda kf: kf["tick"])

    if len(keyframes) > config.KEYFRAME_MAX_PER_TIME_JUMP:
        # Keep highest-significance: prefer keyframes with chronicle entries, then by event count
        def significance(kf):
            has_chronicle = 0 if kf["chronicle_entry_id"] is None else 1
            events = len(kf["ownership_changes"]) + len(kf["military_events"])
            return (has_chronicle, events)
        keyframes.sort(key=significance, reverse=True)
        keyframes = keyframes[:config.KEYFRAME_MAX_PER_TIME_JUMP]
        keyframes.sort(key=lambda kf: kf["tick"])

    for i, kf in enumerate(keyframes):
        old_id = kf["entry_id"]
        new_id = _entry_id(i)
        if kf["chronicle_entry_id"] == old_id:
            kf["chronicle_entry_id"] = new_id
        kf["entry_id"] = new_id

    return keyframes
