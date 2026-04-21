from world_view.keyframe_selector import select_keyframes
from world_view.keyframe_message import (
    keyframes_to_messages,
    scroll_entries_to_messages,
    time_jump_lifecycle_messages,
)


def build_time_jump_messages(time_jump_result: dict, time_jump_id: str) -> list[dict]:
    scroll_entries = time_jump_result.get("scroll_entries", [])
    keyframes = select_keyframes(time_jump_result)

    kf_messages = keyframes_to_messages(keyframes, time_jump_id)
    ce_messages = scroll_entries_to_messages(scroll_entries, keyframes, time_jump_id)

    ticks_run = time_jump_result.get("ticks_run", 0)
    span_years = max(1, ticks_run // 10)

    start_msg, end_msg = time_jump_lifecycle_messages(
        time_jump_id, span_years, len(keyframes), len(ce_messages))

    ce_by_id = {m["entry_id"]: m for m in ce_messages}

    ordered = [start_msg]
    for kf_msg in kf_messages:
        paired_id = kf_msg.get("chronicle_entry_id")
        if paired_id and paired_id in ce_by_id:
            ordered.append(ce_by_id[paired_id])
        ordered.append(kf_msg)
    ordered.append(end_msg)

    return ordered
