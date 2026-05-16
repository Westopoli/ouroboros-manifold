def keyframes_to_messages(keyframes: list[dict], time_jump_id: str) -> list[dict]:
    messages = []
    for i, kf in enumerate(keyframes):
        msg = {"type": "keyframe", "time_jump_id": time_jump_id, "keyframe_index": i}
        msg.update(kf)
        messages.append(msg)
    return messages


def scroll_entries_to_messages(scroll_entries, keyframes: list[dict], time_jump_id: str,
                               mentions_by_entry: dict | None = None) -> list[dict]:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    import config as _config

    entry_id_set = {kf["chronicle_entry_id"] for kf in keyframes if kf["chronicle_entry_id"] is not None}
    messages = []
    for i, entry in enumerate(scroll_entries):
        from world_view.keyframe_selector import _entry_id
        eid = _entry_id(i)
        if eid not in entry_id_set:
            continue
        msg = {
            "type": "chronicle_entry",
            "time_jump_id": time_jump_id,
            "entry_id": eid,
            "tick_range_start": entry.tick_range[0],
            "tick_range_end": entry.tick_range[1],
            "base_form": entry.base_text,
            "expanded_form": entry.expanded_text,
        }
        # Stage 11g — additive, gated. Flag off → key absent (bit-identical).
        if getattr(_config, "ENABLE_CHRONICLE_MENTIONS", False):
            base_m = None
            exp_m = None
            if mentions_by_entry and eid in mentions_by_entry:
                base_m = mentions_by_entry.get(eid)
            else:
                base_m = getattr(entry, "mentions", None) or None
                exp_m = getattr(entry, "expanded_mentions", None) or None
            if base_m:
                msg["mentions"] = base_m
            if exp_m:
                msg["expanded_mentions"] = exp_m
        messages.append(msg)
    return messages


def time_jump_lifecycle_messages(time_jump_id: str, span_years: int,
                                  total_keyframes: int, total_entries: int,
                                  faction_names: dict | None = None,
                                  ownership_timeline: list | None = None,
                                  ownership_history: dict | None = None) -> tuple[dict, dict]:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    import config as _config

    start_msg = {
        "type": "time_jump_start",
        "time_jump_id": time_jump_id,
        "span_years": span_years,
        "total_keyframes": total_keyframes,
        "total_entries": total_entries,
        "faction_names": faction_names or {},
        "ownership_timeline": ownership_timeline or [],
    }
    # Stage 11g — additive, gated. Flag off → key absent (bit-identical).
    if getattr(_config, "ENABLE_OWNERSHIP_HISTORY", False) and ownership_history is not None:
        start_msg["ownership_history"] = ownership_history
    end_msg = {
        "type": "time_jump_end",
        "time_jump_id": time_jump_id,
    }
    return start_msg, end_msg
