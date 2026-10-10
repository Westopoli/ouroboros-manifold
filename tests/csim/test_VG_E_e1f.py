"""Visible-game lane E1, piece E1f (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 6): the building set per era
pack as manifest data. Proves R-168-05 and Q-168-04 a: every shipping pack's manifest.json carries a small fixed
`buildings` list, each row {id, role, footprint, hp}, role one of production / house / worker-hut / forward-works
(R-168-01, S-170, S-174 forward works); settled_reach and greek_placeholder both carry one with placeholder names
(R-168-05, names are era pack content); scripts/specfactory/pack_validate.py requires it (R-146-03 style FAIL, named).
Fenced: builders never edit this file. Not asserted: any cap on a base (Q-168-05 closed (a), no maximum in the beta),
any count, footprint units or hp value (no number was given); only shape and positivity.
Red on main: manifests have no `buildings` key and the validator never mentions it.
"""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "specfactory"))
import pack_validate  # noqa: E402

PACKS = ("settled_reach", "greek_placeholder")
ROLES = {"production", "house", "worker-hut", "forward-works"}


def load(pack):
    return json.loads((ROOT / "assets" / "eras" / pack / "manifest.json").read_text())


def copy_pack(pack, tmp_path, mutate=None):
    dst = tmp_path / pack
    shutil.copytree(ROOT / "assets" / "eras" / pack, dst)
    if mutate is not None:
        m = json.loads((dst / "manifest.json").read_text())
        mutate(m)
        (dst / "manifest.json").write_text(json.dumps(m))
    return dst


def building_findings(pack_dir):
    return [f for f in pack_pack(pack_dir) if "building" in f["message"].lower() or "building" in f["code"].lower()]


def pack_pack(pack_dir):
    return pack_validate.validate_pack(pack_dir)


def pos(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


# ---- isolation: the manifest data (R-168-05, Q-168-04 a)

@pytest.mark.parametrize("pack", PACKS)
def test_buildings_list_present_and_small(pack):
    b = load(pack).get("buildings")
    assert isinstance(b, list) and b, f"R-168-05: {pack} manifest has no non-empty `buildings` list"


@pytest.mark.parametrize("pack", PACKS)
def test_building_rows_have_the_fixed_fields(pack):
    for row in load(pack).get("buildings", []):
        assert isinstance(row, dict), row
        assert isinstance(row.get("id"), str) and row["id"].strip(), row
        assert row.get("role") in ROLES, f"{row}: role must be one of {sorted(ROLES)}"
        fp = row.get("footprint")
        assert pos(fp) or (isinstance(fp, list) and len(fp) == 2 and all(pos(x) for x in fp)), f"{row}: footprint"
        assert pos(row.get("hp")) and isinstance(row["hp"], int), f"{row}: hp must be a positive int"


@pytest.mark.parametrize("pack", PACKS)
def test_every_role_is_covered_and_ids_unique(pack):
    b = load(pack).get("buildings", [])
    assert {r.get("role") for r in b} == ROLES, "each of the four roles needs at least one building"
    ids = [r.get("id") for r in b]
    assert ids and len(ids) == len(set(ids)), "building ids must be unique"


@pytest.mark.parametrize("pack", PACKS)
def test_names_are_placeholders_not_era_named(pack):
    m = load(pack)
    for r in m.get("buildings", []):
        assert m["era_id"].lower() not in r["id"].lower(), "R-145-01: no identifier names an era"
    banned = pack_validate.load_banned_words(pack_validate.DEFAULT_BANNED_WORDS_FILE)
    for r in m.get("buildings", []):
        assert not pack_validate._banned_hits(r["id"], banned), r["id"]


def test_both_packs_share_the_mechanical_set():
    a, b = ({r["id"]: r["role"] for r in load(p).get("buildings", [])} for p in PACKS)
    assert a and a == b, "R-146-02: the building ids and roles are identical across eras (only names/art differ)"


# ---- isolation: the validator requires it

@pytest.mark.parametrize("pack", PACKS)
def test_real_packs_validate_clean(pack):
    fails = [f for f in pack_pack(ROOT / "assets" / "eras" / pack) if f["level"] == "FAIL"]
    assert not fails, fails


@pytest.mark.parametrize("pack", PACKS)
def test_missing_buildings_fails_validation_named(pack, tmp_path):
    d = copy_pack(pack, tmp_path, lambda m: m.pop("buildings", None))
    f = [x for x in building_findings(d) if x["level"] == "FAIL"]
    assert f, "pack_validate must FAIL, naming `buildings`, when the list is absent"


@pytest.mark.parametrize("mutation,label", [
    (lambda m: m["buildings"][0].update(role="barracks-of-doom"), "bad role"),
    (lambda m: m["buildings"][0].pop("hp"), "missing hp"),
    (lambda m: m["buildings"][0].pop("footprint"), "missing footprint"),
    (lambda m: m["buildings"][0].update(hp=0), "zero hp"),
    (lambda m: m.update(buildings=[]), "empty list"),
    (lambda m: m["buildings"].append(copy.deepcopy(m["buildings"][0])), "duplicate id"),
])
def test_malformed_buildings_fail_validation(mutation, label, tmp_path):
    d = copy_pack("settled_reach", tmp_path, lambda m: mutation(m) if "buildings" in m else pytest.fail(
        "R-168-05: settled_reach has no `buildings` list to mutate"))
    assert [x for x in building_findings(d) if x["level"] == "FAIL"], f"{label}: validator accepted it"


# ---- positive control for the detector: a well-formed list passes (integration of data + validator)

def test_control_wellformed_buildings_pass(tmp_path):
    good = [{"id": f"bld_{r}", "role": r, "footprint": [2, 2], "hp": 100} for r in sorted(ROLES)]
    d = copy_pack("settled_reach", tmp_path, lambda m: m.update(buildings=good))
    assert not [x for x in pack_pack(d) if x["level"] == "FAIL"], "a well-formed list must validate clean"
    assert not building_findings(d), "no finding may mention buildings for a well-formed list"
