def keyframes_to_messages(keyframes: list[dict], time_jump_id: str) -> list[dict]:
    messages = []
    for i, kf in enumerate(keyframes):
        msg = {"type": "keyframe", "time_jump_id": time_jump_id, "keyframe_index": i}
        msg.update(kf)
        messages.append(msg)
    return messages


def scroll_entries_to_messages(scroll_entries, keyframes: list[dict], time_jump_id: str) -> list[dict]:
    entry_id_set = {kf["chronicle_entry_id"] for kf in keyframes if kf["chronicle_entry_id"] is not None}
    messages = []
    for i, entry in enumerate(scroll_entries):
        from world_view.keyframe_selector import _entry_id
        eid = _entry_id(i)
        if eid not in entry_id_set:
            continue
        messages.append({
            "type": "chronicle_entry",
            "time_jump_id": time_jump_id,
            "entry_id": eid,
            "tick_range_start": entry.tick_range[0],
            "tick_range_end": entry.tick_range[1],
            "base_form": entry.base_text,
            "expanded_form": entry.expanded_text,
        })
    return messages


def time_jump_lifecycle_messages(time_jump_id: str, span_years: int,
                                  total_keyframes: int, total_entries: int,
                                  faction_names: dict | None = None,
                                  ownership_timeline: list | None = None) -> tuple[dict, dict]:
    start_msg = {
        "type": "time_jump_start",
        "time_jump_id": time_jump_id,
        "span_years": span_years,
        "total_keyframes": total_keyframes,
        "total_entries": total_entries,
        "faction_names": faction_names or {},
        "ownership_timeline": ownership_timeline or [],
    }
    end_msg = {
        "type": "time_jump_end",
        "time_jump_id": time_jump_id,
    }
    return start_msg, end_msg
