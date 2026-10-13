"""E1g narrowed (spec rev 8, K-e2 amendment): the doctrine list as era-pack data.
R-179-01 (E-17 S-193): four doctrines boom, fortify, press, balanced.
Every era manifest carries a "doctrines" list of exactly those ids; pack_validate
reports a manifest without the list or with a missing id. No mix numbers, setter or
default doctrine here (K-e3)."""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "specfactory"))
import pack_validate  # noqa: E402

IDS = {"boom", "fortify", "press", "balanced"}
PACKS = sorted(p.parent for p in (ROOT / "assets" / "eras").glob("*/manifest.json"))


def _fails(pack_dir):
    return [f for f in pack_validate.validate_pack(pack_dir) if f["level"] == "FAIL"]


def _doctrine_fails(pack_dir):
    return [f for f in _fails(pack_dir) if "doctrine" in (f["code"] + f["message"]).lower()]


def _variant(tmp_path, mutate):
    dst = tmp_path / "pack"
    shutil.copytree(ROOT / "assets" / "eras" / "test_era", dst)
    m = json.loads((dst / "manifest.json").read_text())
    mutate(m)
    (dst / "manifest.json").write_text(json.dumps(m))
    return dst


@pytest.mark.parametrize("pack", PACKS, ids=[p.name for p in PACKS])
def test_R_179_01_every_era_manifest_carries_the_four_doctrines(pack):
    m = json.loads((pack / "manifest.json").read_text())
    d = m.get("doctrines")
    assert isinstance(d, list), f"{pack.name}: no doctrines list"
    assert len(d) == 4 and set(d) == IDS, f"{pack.name}: {d}"


def test_R_179_01_validator_reports_missing_list(tmp_path):
    pack = _variant(tmp_path, lambda m: m.pop("doctrines", None))
    assert _doctrine_fails(pack), "validator did not report a missing doctrines list"


@pytest.mark.parametrize("gone", sorted(IDS))
def test_R_179_01_validator_reports_missing_id(tmp_path, gone):
    pack = _variant(tmp_path, lambda m: m.__setitem__("doctrines", sorted(IDS - {gone})))
    assert _doctrine_fails(pack), f"validator did not report missing id {gone}"


def test_R_179_01_positive_control_validator_passes_the_four(tmp_path):
    pack = _variant(tmp_path, lambda m: m.__setitem__("doctrines", ["boom", "fortify", "press", "balanced"]))
    assert _doctrine_fails(pack) == []
    assert _fails(pack) == []
