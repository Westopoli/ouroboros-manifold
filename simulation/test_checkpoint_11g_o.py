#!/usr/bin/env python3
"""Stage 11g Checkpoint O — chronicle mentions transport.

scroll_entries_to_messages serializes per-entry mention spans onto the
keyframe message stream so Godot can wrap them in BBCode urls. With the
flag on and entry.mentions populated (Checkpoint N), no caller-side
mentions_by_entry dict is required.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config
from chronicle_assembler import ScrollEntry
from world_view.keyframe_message import scroll_entries_to_messages
from world_view.keyframe_selector import _entry_id


def _entry(idx, base, expanded, mentions, expanded_mentions):
    return ScrollEntry(
        base_text=base,
        expanded_text=expanded,
        cluster_type="regional",
        category="regional_growth",
        region_id="r_alpha",
        tick_range=(0, 5),
        mentions=mentions,
        expanded_mentions=expanded_mentions,
    )


def _keyframes(entry_indices):
    return [{"chronicle_entry_id": _entry_id(i)} for i in entry_indices]


def test_flag_off_no_mentions_key():
    config.ENABLE_CHRONICLE_MENTIONS = False
    e = _entry(0, "Alpha endured.", "Alpha endured. Phoenix watched.",
               [{"kind": "region", "id": "r_alpha", "start": 0, "end": 5}],
               [{"kind": "region", "id": "r_alpha", "start": 0, "end": 5},
                {"kind": "faction", "id": "f_phoenix", "start": 15, "end": 22}])
    msgs = scroll_entries_to_messages([e], _keyframes([0]), "tj_test")
    assert len(msgs) == 1
    m = msgs[0]
    assert "mentions" not in m, "flag off: mentions key must be absent"
    assert "expanded_mentions" not in m, "flag off: expanded_mentions key must be absent"
    print("ok flag_off_no_mentions_key")


def test_flag_on_reads_from_entry_fields():
    """With N landed, scroll_entries_to_messages picks up entry.mentions /
    entry.expanded_mentions without needing mentions_by_entry parameter."""
    config.ENABLE_CHRONICLE_MENTIONS = True
    base_mentions = [{"kind": "region", "id": "r_alpha", "start": 0, "end": 5}]
    exp_mentions = [
        {"kind": "region", "id": "r_alpha", "start": 0, "end": 5},
        {"kind": "faction", "id": "f_phoenix", "start": 15, "end": 22},
    ]
    e = _entry(0, "Alpha endured.", "Alpha endured. Phoenix watched.",
               base_mentions, exp_mentions)
    msgs = scroll_entries_to_messages([e], _keyframes([0]), "tj_test")
    assert len(msgs) == 1
    m = msgs[0]
    assert m.get("mentions") == base_mentions
    assert m.get("expanded_mentions") == exp_mentions
    print("ok flag_on_reads_from_entry_fields")


def test_explicit_mentions_by_entry_overrides_entry_fields():
    """Backwards compat: if caller passes mentions_by_entry, that wins over
    the entry-side fields."""
    config.ENABLE_CHRONICLE_MENTIONS = True
    entry_side = [{"kind": "region", "id": "r_entry", "start": 0, "end": 5}]
    explicit = [{"kind": "region", "id": "r_override", "start": 0, "end": 8}]
    e = _entry(0, "Alpha endured.", "Alpha endured.",
               entry_side, entry_side)
    eid = _entry_id(0)
    msgs = scroll_entries_to_messages(
        [e], _keyframes([0]), "tj_test",
        mentions_by_entry={eid: explicit},
    )
    assert len(msgs) == 1
    m = msgs[0]
    assert m["mentions"] == explicit, f"override expected, got {m['mentions']}"
    print("ok explicit_mentions_by_entry_overrides_entry_fields")


def test_empty_mentions_omits_keys():
    """If flag on but entry has empty mention lists, the keys should be omitted
    (keeps the wire small and lets Godot skip the wrap path entirely)."""
    config.ENABLE_CHRONICLE_MENTIONS = True
    e = _entry(0, "Alpha endured.", "Alpha endured.", [], [])
    msgs = scroll_entries_to_messages([e], _keyframes([0]), "tj_test")
    assert len(msgs) == 1
    m = msgs[0]
    assert "mentions" not in m, "empty mentions: key must be omitted"
    assert "expanded_mentions" not in m, "empty expanded_mentions: key must be omitted"
    print("ok empty_mentions_omits_keys")


if __name__ == "__main__":
    try:
        test_flag_off_no_mentions_key()
        test_flag_on_reads_from_entry_fields()
        test_explicit_mentions_by_entry_overrides_entry_fields()
        test_empty_mentions_omits_keys()
        print("all 4 pass")
    finally:
        config.ENABLE_CHRONICLE_MENTIONS = False
