"""A82: every faction id up to the faction cap prints its own name.

docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 29, A82 (third bullet),
under A55 (fifteen distinct faction names) and R-068-03 (a name is a vocabulary slot).
Today CHRON_FACTION_NAMES has 18 entries and csrc/chronicle.c indexes it modulo 18, so
faction 0 and faction 18 are both "the Dominion" on a world with more than 18 factions
(gen_faction_count runs 2 to 64; OM_MAX_FACTIONS is 64). The fix is a pool extended by
simple invented syllable combinations, with the sim table and library/chronicle/fragments.json
generated from one source (scripts/library/emit_chronicle_fragments.py today parses the C
table; the generator the fix settles on must keep that command reproducing the committed
JSON). The first 18 names stay exactly as they are so existing chronicle text is stable.

How the sim's name is read: a region's first mention prints "<region>, held by <faction>"
(R-068-04), so a world with one faction per region shows each faction's name.

Positive controls: the same checkers fed an 18-name wrap must report a clash at ids 0 and
18, and fed a distinct table none; the IP checker must flag a planted known name; the
agreement checker must flag a one-element difference.
"""
import json
import pathlib
import re
import subprocess
import sys

from conftest import set_owner

CAP = 64  # OM_MAX_FACTIONS (csrc/ouroboros_sim.h); ids 0..63

REPO = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "library" / "emit_chronicle_fragments.py"
COMMITTED = REPO / "library" / "chronicle" / "fragments.json"
HEADER = REPO / "csrc" / "ouroboros_sim.h"

# The 18 names the sim has printed since A55; ids 0..17 never change.
FIRST_18 = [
    "the Dominion", "the Concord", "the Ashen League", "the Iron Compact",
    "the Free Cities", "the Sable Court", "the Vanguard Accord", "the Twin Banners",
    "the Amber Throne", "the River Pact", "the Stonewrights", "the Northwind Host",
    "the Lantern Guild", "the Hollow Standard", "the Saltmarsh Union", "the Quiet Fleet",
    "the Copper Assembly", "the Evenfall Realm",
]

# Words from existing fiction that must not appear in a name (R: no IP exposure).
# Deliberately short and unambiguous; the checker, not the list, is what is pinned.
KNOWN_FICTION = [
    "jedi", "sith", "empire", "federation", "klingon", "romulan", "vulcan", "borg",
    "mordor", "gondor", "rohan", "shire", "hobbit", "westeros", "lannister", "stark",
    "targaryen", "hogwarts", "gryffindor", "slytherin", "narnia", "tatooine",
    "wakanda", "asgard", "hyrule", "zelda", "azeroth", "skyrim", "vault-tec",
    "umbrella", "weyland", "tyrell", "cylon", "covenant", "atreides", "harkonnen",
    "fremen", "stormcloak", "nilfgaard", "illuminati", "shinra", "aperture",
]


def first_clash(names):
    """First pair [id_a, id_b] with equal names, or [] when all differ."""
    seen = {}
    for i, n in enumerate(names):
        if n in seen:
            return [seen[n], i]
        seen[n] = i
    return []


def ip_hits(names):
    """[(id, word)] for every name containing a known-fiction word as a whole word."""
    hits = []
    for i, n in enumerate(names):
        for word in re.findall(r"[a-z][a-z-]*", n.lower()):
            if word in KNOWN_FICTION:
                hits.append((i, word))
    return hits


def first_difference(a, b):
    """Index of the first element where lists differ (length difference counts), or -1."""
    for i in range(max(len(a), len(b))):
        if i >= len(a) or i >= len(b) or a[i] != b[i]:
            return i
    return -1


def _c_names(lib, world_factory, owners=None, seed=1):
    """The sim's name for faction ids 0..CAP-1: region r is held by owners[r], its
    first mention prints '<region>, held by <faction>'."""
    owners = list(range(CAP)) if owners is None else owners
    w = world_factory(n_regions=CAP, seed=seed)
    out = [None] * CAP
    for r, f in enumerate(owners):
        set_owner(lib, w, r, f, held_since=-1)
    for r, f in enumerate(owners):
        first = lib.om_chronicle_render_region_mention(w, r, 1).decode("utf-8")
        assert ", held by " in first, f"region {r} held by faction {f}: first mention lacks the qualifier: {first!r}"
        out[f] = first.split(", held by ", 1)[1]
    return out


def _json_names():
    return json.loads(COMMITTED.read_text(encoding="utf-8"))["name_tables"]["faction_names"]


def test_control_modulo_18_pool_is_caught():
    wrap = [f"n{i % 18}" for i in range(CAP)]
    assert first_clash(wrap) == [0, 18]
    assert first_clash([f"n{i}" for i in range(CAP)]) == []


def test_control_ip_checker_flags_a_planted_name():
    assert ip_hits(["the Dominion", "the Jedi Council"]) == [(1, "jedi")]
    assert ip_hits(FIRST_18) == []


def test_control_agreement_checker_flags_one_element():
    a = [f"n{i}" for i in range(CAP)]
    b = list(a)
    b[40] = "other"
    assert first_difference(a, b) == 40
    assert first_difference(a, a[:-1]) == CAP - 1
    assert first_difference(a, list(a)) == -1


def test_cap_matches_the_header():
    m = re.search(r"#define\s+OM_MAX_FACTIONS\s+(\d+)", HEADER.read_text(encoding="utf-8"))
    assert m and int(m.group(1)) == CAP, "OM_MAX_FACTIONS changed: update CAP in this test"


def test_A82_all_cap_faction_ids_render_distinct_names(lib, world_factory):
    names = _c_names(lib, world_factory)
    assert all(n.strip() for n in names), "a faction id rendered an empty name"
    clash = first_clash(names)
    assert not clash, f"faction ids {clash} both print {names[clash[0]]!r}"
    lowered = first_clash([n.lower() for n in names])
    assert not lowered, f"faction ids {lowered} differ only in case"


def test_A82_first_18_names_are_unchanged(lib, world_factory):
    assert _c_names(lib, world_factory)[:18] == FIRST_18
    assert _json_names()[:18] == FIRST_18


def test_A82_at_least_fifteen_unique_names_A55(lib, world_factory):
    # Same bar as tests/test_faction_name_table.gd, on the sim side and on the JSON.
    assert len(set(_c_names(lib, world_factory)[:15])) == 15
    assert len(set(_json_names())) >= 15


def test_A82_names_are_plain_digit_free_and_read_in_prose(lib, world_factory):
    # Chronicle fragments print "{faction_name}'s ..." and "With {faction_name} pressing ...",
    # so a name is lowercase-article text that survives a possessive.
    for i, n in enumerate(_c_names(lib, world_factory)):
        assert not any(ch.isdigit() for ch in n), f"faction {i} name {n!r} has a digit"
        assert n.isprintable() and n == n.strip(), f"faction {i} name {n!r} is not clean text"
        assert n.startswith("the ") and len(n.split()) >= 2, f"faction {i} name {n!r} does not read as 'the <name>'"
        assert "'" not in n and "," not in n, f"faction {i} name {n!r} has punctuation that breaks mention parsing"


def test_A82_names_carry_no_known_fiction(lib, world_factory):
    assert ip_hits(_c_names(lib, world_factory)) == []
    assert ip_hits(_json_names()) == []


def test_A82_name_is_a_pure_function_of_the_id(lib, world_factory):
    base = _c_names(lib, world_factory, seed=1)
    other_seed = _c_names(lib, world_factory, seed=987654321)
    reversed_owners = _c_names(lib, world_factory, owners=list(reversed(range(CAP))), seed=5)
    assert other_seed == base, "faction names changed with the world seed"
    assert reversed_owners == base, "faction names changed with which region the faction holds"
    assert _c_names(lib, world_factory, seed=1) == base, "faction names changed between identical runs"


def test_A82_sim_and_json_agree_element_for_element_across_the_cap(lib, world_factory):
    c_names = _c_names(lib, world_factory)
    table = _json_names()
    assert len(table) >= CAP, f"fragments.json faction_names has {len(table)} entries, need at least {CAP}"
    i = first_difference(table[:CAP], c_names)
    assert i == -1, f"faction id {i}: json {table[i]!r} vs sim {c_names[i]!r} (regenerate the JSON)"
    assert first_clash(table) == [], f"fragments.json faction_names repeat: {first_clash(table)}"


def test_A82_regenerating_from_the_one_source_reproduces_the_committed_json(tmp_path):
    # The generator command (a Python script under scripts/library/, today
    # emit_chronicle_fragments.py; the fix may rename it, in which case update SCRIPT here)
    # must reproduce library/chronicle/fragments.json byte for byte, faction pool included.
    out = tmp_path / "out.json"
    r = subprocess.run([sys.executable, str(SCRIPT), str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    emitted = out.read_bytes()
    assert emitted == COMMITTED.read_bytes(), "regenerated fragments.json differs from the committed file"
    assert len(json.loads(emitted)["name_tables"]["faction_names"]) >= CAP


def test_A82_region_and_lineage_tables_are_untouched():
    t = json.loads(COMMITTED.read_text(encoding="utf-8"))["name_tables"]
    assert len(t["region_names"]) == 528 and t["region_names"][3] == "the Iron Vale"
    assert t["lineage_surnames"] == ["Voss", "Kestrel", "Thane", "Ashworth", "Marrow", "Corvane", "Halloway", "Sennett"]
