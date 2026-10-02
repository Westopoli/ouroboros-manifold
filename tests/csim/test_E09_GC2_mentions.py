"""GC2 / A53 (R-069-07, S-069, Q-069-02): the sim sends each faction and region
name's position in a chronicle entry's text.

Contract: csrc/ouroboros_sim.h om_chronicle_mention_count / om_chronicle_mention_get.
Offsets are Unicode code point offsets into base_text (expanded=0) or
expanded_text (expanded=1) exactly as stored; every name the text prints through
a faction or region slot is one mention, and no other words are.

The oracle matches names in the final text, but only to judge the sim's answer;
the sim itself must not find mentions that way (it produces them while filling
the slots). Names come from om_chronicle_render_region_mention, not a copied
table, so the name-table rewrite (A55) cannot break these tests.

Positive controls: test_control_* run the same checker on a planted off-by-one
offset, a stale offset after a text rewrite, and a byte offset on multi-byte
text; each must be rejected.
"""
import ctypes
import re

import pytest

from conftest import (
    OmChronicleEntry,
    OmChronicleMention,
    OMTier,
    set_edge,
    set_owner,
    set_region,
)

FACTION, REGION = 0, 1
N_REGIONS = 12
N_FACTIONS = 3
UNCLAIMED = "an unclaimed people"
CATEGORY_SETS = (
    [10, 11, 12, 13, 14],
    [15, 16, 17, 20, 21],
    [22, 23, 20, 21, 10],
)


def _build(lib, world_factory, seed, cats, base):
    """12 regions in a ring; owners cycle through three factions, every fifth region unowned."""
    w = world_factory(n_regions=N_REGIONS, seed=seed)
    for r in range(N_REGIONS):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, (r + seed) % N_FACTIONS if r % 5 else -1, held_since=-1)
        set_edge(lib, w, r, (r + 1) % N_REGIONS)
    for i, cat in enumerate(cats):
        lib.om_chronicle_add_regional_event(w, (base + i * 3) % N_REGIONS, cat, 9.0 + i)
    lib.om_chronicle_distill_and_assemble(w)
    return w


def _sweep(lib, world_factory):
    """Every (world, entry index, entry) the fixture worlds produce."""
    out = []
    for seed in range(4):
        for cats in CATEGORY_SETS:
            w = _build(lib, world_factory, seed, cats, seed)
            for i in range(lib.om_chronicle_entry_count(w)):
                ent = OmChronicleEntry()
                if lib.om_chronicle_entry_get(w, i, ctypes.byref(ent)):
                    out.append((w, i, ent))
    assert len(out) >= 30, f"fixture too thin: {len(out)} rendered entries"
    return out


def _names(lib, w):
    """({region idx: name}, {faction id: name}) as the sim prints them."""
    regions, factions = {}, {}
    for r in range(N_REGIONS):
        regions[r] = lib.om_chronicle_render_region_mention(w, r, 0).decode("utf-8")
        owner = lib.om_region_owner(w, r)
        if owner >= 0 and owner not in factions:
            first = lib.om_chronicle_render_region_mention(w, r, 1).decode("utf-8")
            assert ", held by " in first, f"owned region {r} first mention lacks the qualifier: {first!r}"
            factions[owner] = first.split(", held by ", 1)[1]
    return regions, factions


def _mentions(lib, w, index, expanded):
    n = lib.om_chronicle_mention_count(w, index, expanded)
    out = []
    for k in range(n):
        m = OmChronicleMention()
        assert lib.om_chronicle_mention_get(w, index, expanded, k, ctypes.byref(m)) == 1
        out.append({"start": m.start, "len": m.len, "kind": m.kind, "id": m.id})
    m = OmChronicleMention()
    assert lib.om_chronicle_mention_get(w, index, expanded, n, ctypes.byref(m)) == 0, "get past the count must return 0"
    return out


def _variants(name):
    """The name as it stands mid-sentence and opening a sentence."""
    return {name, name[0].upper() + name[1:]}


def check_mentions(text, mentions, regions, factions, n_regions=N_REGIONS):
    """Raise AssertionError unless `mentions` is exactly right for `text`.
    Offsets are code points. Rules: each span reads as the named thing, ids are
    valid, spans are in order without overlap, and every printed occurrence of
    a region or faction name is covered by exactly one mention."""
    prev_end = 0
    for m in mentions:
        s, n = m["start"], m["len"]
        assert n > 0 and s >= prev_end, f"mention {m} out of order or overlapping (previous ended at {prev_end})"
        assert s + n <= len(text), f"mention {m} runs past the text ({len(text)} characters)"
        if m["kind"] == REGION:
            assert 0 <= m["id"] < n_regions, f"region id {m['id']} invalid"
            name = regions[m["id"]]
        else:
            assert m["kind"] == FACTION, f"unknown kind {m['kind']}"
            assert m["id"] in factions, f"faction id {m['id']} is no faction that owns a region"
            name = factions[m["id"]]
        assert text[s:s + n] in _variants(name), f"mention {m} reads {text[s:s + n]!r}, not {name!r}"
        prev_end = s + n
    covered = {(m["start"], m["len"]) for m in mentions}
    printed = []
    for name in list(regions.values()) + list(factions.values()):
        for v in _variants(name):
            printed += [(h.start(), len(v)) for h in re.finditer(re.escape(v), text)]
    assert sorted(set(printed)) == sorted(covered), (
        f"printed names {sorted(set(printed))} differ from mentions {sorted(covered)} in {text!r}")


def _form(ent, expanded):
    return (ent.expanded_text if expanded else ent.base_text).decode("utf-8")


@pytest.mark.parametrize("expanded", [0, 1])
def test_R_069_07_offsets_point_at_the_exact_name_in_the_text_as_sent(lib, world_factory, expanded):
    """Given a printed entry, When the sim sends its mentions, Then each start/len is a code point span of the
    final text that reads exactly as the faction or region it names, with a valid kind and id, in order, no
    overlap, and every name the text prints is a mention (S-069, R-069-07)."""
    for w, i, ent in _sweep(lib, world_factory):
        regions, factions = _names(lib, w)
        check_mentions(_form(ent, expanded), _mentions(lib, w, i, expanded), regions, factions)


def test_R_069_07_both_kinds_appear_and_the_sweep_has_teeth(lib, world_factory):
    """Given the fixture worlds, When mentions are counted, Then region and faction mentions both occur in both
    forms and the held-by qualifier produces a faction mention that follows its region mention (id = owner)."""
    seen = {(k, e): 0 for k in (FACTION, REGION) for e in (0, 1)}
    held_by_pairs = 0
    for w, i, ent in _sweep(lib, world_factory):
        for expanded in (0, 1):
            ms = _mentions(lib, w, i, expanded)
            for m in ms:
                seen[(m["kind"], expanded)] += 1
            text = _form(ent, expanded)
            for a, b in zip(ms, ms[1:]):
                if a["kind"] == REGION and b["kind"] == FACTION and text[a["start"] + a["len"]:b["start"]] == ", held by ":
                    held_by_pairs += 1
                    assert b["id"] == lib.om_region_owner(w, a["id"]), (
                        f"'held by' faction {b['id']} is not the owner of region {a['id']}")
    assert all(v > 0 for v in seen.values()), f"a kind never occurred: {seen}"
    assert held_by_pairs > 0, "no region mention with a held-by faction mention in the fixture"


def test_R_069_07_unowned_faction_slot_is_not_a_mention(lib, world_factory):
    """Given an entry whose faction slot printed 'an unclaimed people', When mentions are read, Then that phrase
    is not covered by any mention (no faction exists to centre on)."""
    found = 0
    for w, i, ent in _sweep(lib, world_factory):
        for expanded in (0, 1):
            text = _form(ent, expanded)
            at = text.find(UNCLAIMED)
            if at < 0:
                continue
            found += 1
            for m in _mentions(lib, w, i, expanded):
                assert m["start"] + m["len"] <= at or m["start"] >= at + len(UNCLAIMED), (
                    f"{m} covers {UNCLAIMED!r} in {text!r}")
    assert found > 0, "fixture never printed the unowned-faction phrase"


def test_R_069_07_offsets_are_code_points_when_text_has_multibyte_characters(lib, world_factory):
    """Given library text with multi-byte characters (em dash), When a mention follows one, Then its offset counts
    code points: the slice of the decoded text is the name, the byte offset would not be."""
    checked = 0
    for w, i, ent in _sweep(lib, world_factory):
        regions, factions = _names(lib, w)
        for expanded in (0, 1):
            text = _form(ent, expanded)
            raw = text.encode("utf-8")
            for m in _mentions(lib, w, i, expanded):
                if len(text[:m["start"]].encode("utf-8")) != m["start"]:
                    checked += 1
                    name = regions[m["id"]] if m["kind"] == REGION else factions[m["id"]]
                    assert text[m["start"]:m["start"] + m["len"]] in _variants(name)
                    assert raw[m["start"]:m["start"] + m["len"]].decode("utf-8", "replace") not in _variants(name), (
                        "offset equals the byte offset; it must be the code point offset")
    assert checked > 0, "fixture has no mention after a multi-byte character"


def test_R_069_07_no_mention_for_a_missing_entry_and_same_seed_same_spans(lib, world_factory):
    """Given an index past the entries, When mentions are read, Then the count is 0 and get returns 0; and two
    worlds built alike send identical spans (determinism)."""
    w = _build(lib, world_factory, 1, CATEGORY_SETS[0], 1)
    missing = lib.om_chronicle_entry_count(w) + 7
    for expanded in (0, 1):
        assert lib.om_chronicle_mention_count(w, missing, expanded) == 0
        assert lib.om_chronicle_mention_get(w, missing, expanded, 0, ctypes.byref(OmChronicleMention())) == 0
    a = _build(lib, world_factory, 2, CATEGORY_SETS[1], 2)
    b = _build(lib, world_factory, 2, CATEGORY_SETS[1], 2)
    for i in range(lib.om_chronicle_entry_count(a)):
        for expanded in (0, 1):
            assert _mentions(lib, a, i, expanded) == _mentions(lib, b, i, expanded)


# ---- positive controls: the checker must reject planted errors ----

_CONTROL_REGIONS = {0: "the Ashfall Reach", 1: "the Iron Vale"}
_CONTROL_FACTIONS = {0: "the Dominion"}
_CONTROL_TEXT = "The Iron Vale, held by the Dominion — so it was said — outlasted the Ashfall Reach."


def _control_mentions(text):
    out = []
    for kind, id_, name in ((REGION, 1, "The Iron Vale"), (FACTION, 0, "the Dominion"), (REGION, 0, "the Ashfall Reach")):
        out.append({"start": text.index(name), "len": len(name), "kind": kind, "id": id_})
    return sorted(out, key=lambda m: m["start"])


def test_control_checker_accepts_the_correct_mentions():
    check_mentions(_CONTROL_TEXT, _control_mentions(_CONTROL_TEXT), _CONTROL_REGIONS, _CONTROL_FACTIONS, n_regions=2)


def test_control_planted_off_by_one_is_caught():
    ms = _control_mentions(_CONTROL_TEXT)
    ms[1] = dict(ms[1], start=ms[1]["start"] + 1)
    with pytest.raises(AssertionError):
        check_mentions(_CONTROL_TEXT, ms, _CONTROL_REGIONS, _CONTROL_FACTIONS, n_regions=2)


def test_control_stale_offsets_after_a_text_rewrite_are_caught():
    ms = _control_mentions(_CONTROL_TEXT)
    rewritten = "Then " + _CONTROL_TEXT[0].lower() + _CONTROL_TEXT[1:]
    with pytest.raises(AssertionError):
        check_mentions(rewritten, ms, _CONTROL_REGIONS, _CONTROL_FACTIONS, n_regions=2)


def test_control_byte_offsets_on_multibyte_text_are_caught():
    raw = _CONTROL_TEXT.encode("utf-8")
    ms = []
    for m in _control_mentions(_CONTROL_TEXT):
        s = len(_CONTROL_TEXT[:m["start"]].encode("utf-8"))
        ms.append(dict(m, start=s, len=len(_CONTROL_TEXT[m["start"]:m["start"] + m["len"]].encode("utf-8"))))
    assert ms != _control_mentions(_CONTROL_TEXT) and raw
    with pytest.raises(AssertionError):
        check_mentions(_CONTROL_TEXT, ms, _CONTROL_REGIONS, _CONTROL_FACTIONS, n_regions=2)


def test_control_a_missed_name_is_caught():
    ms = _control_mentions(_CONTROL_TEXT)[:-1]
    with pytest.raises(AssertionError):
        check_mentions(_CONTROL_TEXT, ms, _CONTROL_REGIONS, _CONTROL_FACTIONS, n_regions=2)
