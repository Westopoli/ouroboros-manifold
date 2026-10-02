"""GC2 / A53 (R-069-07): the chronicle frame carries each entry's text and the
sim's mentions.

Every entry has `text` and `expanded_text` (the finished prose) and `mentions`
and `expanded_mentions`: lists of {"start","len","kind","id"} with code point
offsets into that string as sent, kind "faction" or "region". The pipe copies
the sim's spans; it finds nothing by matching text. Region names do not cross
the pipe, so these checks use what the frame itself says: spans in bounds, in
order, non-overlapping, one reading per (kind, id), spans that begin and end on word edges, faction ids valid, and the
", held by" faction equal to the entry's own faction ref.

Positive controls: the checker rejects a planted off-by-one span and a stale
span after the text was rewritten (test_control_*).
Ids: R-069-07, S-069, docs/architecture.md "chronicle frame".
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
KINDS = ("faction", "region")

needs_pipe = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n].decode("utf-8")))
        i += 4 + n
    return out[1:]


def _jump(seed):
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": 80, "features": FEATURES},
        {"type": "cmd", "name": "jump", "ticks": 50},
    ])
    chron = next((f for f in frames if f.get("type") == "chronicle"), None)
    assert chron is not None, f"no chronicle frame; types={[f.get('type') for f in frames]}"
    snap = [f for f in frames if f.get("type") == "snapshot"][-1]
    return chron, snap


def check_form(text, mentions, n_regions, n_factions, readings):
    """Raise AssertionError unless `mentions` is a well-formed span list for `text`.
    `readings` maps (kind, id) to the first slice seen; the same thing must read the same."""
    assert isinstance(text, str) and isinstance(mentions, list), f"text/mentions wrong type: {type(text)}, {type(mentions)}"
    prev_end = 0
    for m in mentions:
        assert sorted(m) == ["id", "kind", "len", "start"], f"mention keys: {sorted(m)}"
        assert m["kind"] in KINDS, f"kind {m['kind']!r}"
        assert all(isinstance(m[k], int) for k in ("start", "len", "id")), f"non-integer field in {m}"
        s, n = m["start"], m["len"]
        assert n > 0 and s >= prev_end, f"{m} out of order or overlapping (previous ended at {prev_end})"
        assert s + n <= len(text), f"{m} runs past the text ({len(text)} characters)"
        limit = n_regions if m["kind"] == "region" else n_factions
        assert 0 <= m["id"] < limit, f"{m['kind']} id {m['id']} outside 0..{limit - 1}"
        read = text[s:s + n]
        assert read[:1].isalpha() and read[-1:].isalpha(), f"{m} reads {read!r}: not a name"
        assert not text[s - 1:s].isalpha() if s else True, f"{m} starts inside a word in {text!r}"
        assert not text[s + n:s + n + 1].isalpha(), f"{m} ends inside a word in {text!r}"
        key = (m["kind"], m["id"])
        first = readings.setdefault(key, read)
        assert first[1:] == read[1:], f"{key} reads {first!r} and {read!r}"
        prev_end = s + n


def _check_entry(ent, n_regions, n_factions, readings):
    for text_key, men_key in (("text", "mentions"), ("expanded_text", "expanded_mentions")):
        assert text_key in ent and men_key in ent, f"entry {ent.get('id')}: missing {text_key}/{men_key}"
        check_form(ent[text_key], ent[men_key], n_regions, n_factions, readings)


@needs_pipe
def test_r069_07_every_entry_carries_text_and_wellformed_mentions():
    """After a 50-tick jump every entry has text, expanded_text and both mention lists, spans in bounds and
    ordered, ids valid, and at least one entry has a region mention and one a faction mention."""
    for seed in (1, 2, 3):
        chron, snap = _jump(seed)
        entries = chron["entries"]
        assert entries, f"seed {seed}: no entries"
        readings = {}
        for ent in entries:
            _check_entry(ent, len(snap["regions"]), len(snap["factions"]), readings)
        kinds = {m["kind"] for e in entries for m in e["mentions"] + e["expanded_mentions"]}
        assert kinds == set(KINDS), f"seed {seed}: kinds seen {kinds}"
        assert any(e["text"] for e in entries), f"seed {seed}: every text is empty"


@needs_pipe
def test_r069_07_held_by_faction_mention_is_the_entrys_faction():
    """A faction mention right after ', held by ' is the entry's own faction ref (the region's first mention
    names its owner), so the span the sim sends is the one the frame's refs say."""
    pairs = 0
    for seed in (1, 2, 3):
        chron, _ = _jump(seed)
        for ent in chron["entries"]:
            for text, ms in ((ent["text"], ent["mentions"]), (ent["expanded_text"], ent["expanded_mentions"])):
                for m in ms:
                    if m["kind"] == "faction" and text[:m["start"]].endswith(", held by "):
                        pairs += 1
                        assert ent["refs"]["factions"] == [m["id"]], (
                            f"entry {ent['id']}: held-by faction {m['id']} vs refs {ent['refs']['factions']}")
    assert pairs > 0, "no held-by faction mention in three jumps"


@needs_pipe
def test_r069_07_text_survives_json_with_multibyte_characters():
    """Library text holds the em dash; a mention after one reads as a whole name by code point offset."""
    found = 0
    for seed in (1, 2, 3):
        chron, snap = _jump(seed)
        readings = {}
        for ent in chron["entries"]:
            for text, ms in ((ent["text"], ent["mentions"]), (ent["expanded_text"], ent["expanded_mentions"])):
                for m in ms:
                    if len(text[:m["start"]].encode("utf-8")) != m["start"]:
                        found += 1
                        check_form(text, [m], len(snap["regions"]), len(snap["factions"]), readings)
    assert found > 0, "no mention after a multi-byte character in three jumps"


@needs_pipe
def test_r069_07_same_seed_same_frame():
    """Determinism: the same seed and jump send byte-identical text and spans."""
    a, _ = _jump(2)
    b, _ = _jump(2)
    assert a["entries"] == b["entries"]


# ---- positive controls ----

_TEXT = "Halven, held by Ostrel — so it was said — outlasted Kaine."
_MS = [
    {"start": 0, "len": 6, "kind": "region", "id": 3},
    {"start": 16, "len": 6, "kind": "faction", "id": 1},
    {"start": 52, "len": 5, "kind": "faction", "id": 2},
]


def test_control_checker_accepts_correct_spans():
    assert _TEXT[16:22] == "Ostrel" and _TEXT[52:57] == "Kaine"
    check_form(_TEXT, _MS, 80, 8, {})


def test_control_planted_off_by_one_is_caught():
    bad = [dict(_MS[0]), dict(_MS[1], start=17), dict(_MS[2])]
    with pytest.raises(AssertionError):
        check_form(_TEXT, bad, 80, 8, {})


def test_control_stale_span_after_a_text_rewrite_is_caught():
    rewritten = "Then " + _TEXT
    with pytest.raises(AssertionError):
        check_form(rewritten, _MS, 80, 8, {})


def test_control_inconsistent_reading_for_one_id_is_caught():
    readings = {}
    check_form("Ostrel held.", [{"start": 0, "len": 6, "kind": "faction", "id": 1}], 80, 8, readings)
    with pytest.raises(AssertionError):
        check_form("Kaine held.", [{"start": 0, "len": 5, "kind": "faction", "id": 1}], 80, 8, readings)
