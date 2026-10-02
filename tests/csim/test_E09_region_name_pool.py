"""A66 (f): every region of a 512-region world prints its own name.

docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 26, A66 (f),
under R-068-03 (region name is a vocabulary slot) and R-068-04 (region mention).
Today CHRON_REGION_NAMES has 16 entries and csrc/chronicle.c indexes it modulo 16,
so region 0 and region 16 print the same name. The fix is a pool built from simple
invented syllable combinations (csrc/chronicle.c) with library/chronicle/fragments.json
regenerated from it by scripts/library/emit_chronicle_fragments.py.

Positive controls: the same checker fed a modulo-16 table must report a clash at
ids 0 and 16, and fed a distinct table must report none.
"""
import json
import pathlib
import subprocess
import sys

N_IDS = 512  # OM_MAX_REGIONS on HDR5 (A64); ids 0..511

REPO = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "library" / "emit_chronicle_fragments.py"
COMMITTED = REPO / "library" / "chronicle" / "fragments.json"


def first_clash(names):
    """First pair [id_a, id_b] with equal names, or [] when all differ."""
    seen = {}
    for i, n in enumerate(names):
        if n in seen:
            return [seen[n], i]
        seen[n] = i
    return []


def _c_names(lib, w):
    # is_first_mention=0 prints the bare name (R-068-04); copy the buffer at once.
    return [
        lib.om_chronicle_render_region_mention(w, region_idx=i, is_first_mention=0).decode("utf-8")
        for i in range(N_IDS)
    ]


def test_control_modulo_16_pool_is_caught():
    pool = [f"name{i}" for i in range(16)]
    assert first_clash([pool[i % 16] for i in range(N_IDS)]) == [0, 16]
    assert first_clash([f"name{i}" for i in range(N_IDS)]) == []


def test_A66f_all_512_region_ids_render_distinct_names(lib, world_factory):
    w = world_factory(n_regions=2)
    names = _c_names(lib, w)
    assert all(n.strip() for n in names), "a region id rendered an empty name"
    clash = first_clash(names)
    assert not clash, f"region ids {clash} both print {names[clash[0]]!r}"


def test_A66f_names_are_plain_and_digit_free(lib, world_factory):
    w = world_factory(n_regions=2)
    for i, n in enumerate(_c_names(lib, w)):
        assert not any(ch.isdigit() for ch in n), f"region {i} name {n!r} has a digit (R-068-03)"
        assert n.isprintable() and n == n.strip(), f"region {i} name {n!r} is not clean text"


def test_A66f_fragments_json_region_table_matches_c_pool(lib, world_factory):
    w = world_factory(n_regions=2)
    c_names = _c_names(lib, w)
    table = json.loads(COMMITTED.read_text(encoding="utf-8"))["name_tables"]["region_names"]
    assert len(table) >= N_IDS, f"fragments.json region_names has {len(table)} entries, need at least {N_IDS}"
    assert table[:N_IDS] == c_names, "fragments.json region_names differ from the C pool (regenerate with emit_chronicle_fragments.py)"
    assert first_clash(table) == [], f"fragments.json region_names repeat: {first_clash(table)}"


def test_A66f_emit_script_reproduces_region_table(tmp_path):
    out = tmp_path / "out.json"
    r = subprocess.run([sys.executable, str(SCRIPT), str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    emitted = json.loads(out.read_text(encoding="utf-8"))["name_tables"]["region_names"]
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))["name_tables"]["region_names"]
    assert emitted == committed
    assert len(emitted) >= N_IDS
