# spec: docs/northstar/plans/briefs/2026-09-21-px-batch-b-spec-content-boundary.md PX-10
"""Tests for scripts/specfactory/pack_validate.py.

Builds a throwaway synthetic era pack per unit test (mirrors
assets/eras/test_era's manifest shape: era_id, era_display_name,
era_accent_color, units, structures, environment, materials, faction_colors)
so most of this suite does not depend on the real assets/eras/** packs. Two
groups of tests do exercise real packs, using the real banned_words.txt:
docs/northstar/proving_ground/evidence/px10/{pack_clean,pack_broken} (PX-10),
and assets/eras/{settled_reach,greek_placeholder} (K2, docs/northstar/plans/
briefs/2026-09-22-two-day-push.md wave 3) -- both accept, they are
mechanically identical (R-146-02), and a copy of the Greek pack with a
banned word injected is rejected.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PACK_VALIDATE = REPO / "scripts" / "specfactory" / "pack_validate.py"
PX10_EVIDENCE = REPO / "docs" / "northstar" / "proving_ground" / "evidence" / "px10"


_FIXTURE_BUILDINGS = [
    {"id": "bld_a", "role": "production", "footprint": [3, 3], "hp": 200},
    {"id": "bld_b", "role": "house", "footprint": [2, 2], "hp": 100},
    {"id": "bld_c", "role": "worker-hut", "footprint": [2, 2], "hp": 80},
    {"id": "bld_d", "role": "forward-works", "footprint": [2, 2], "hp": 120},
]
# TD-VG-E-4: R-168-05 makes the building set part of every manifest.


def _base_manifest(era_id="synth_era", era_display_name="Synth Era"):
    return {
        "era_id": era_id,
        "era_display_name": era_display_name,
        "era_accent_color": "#123456",
        "era_spatial_scale": "A synthetic scale sentence.",
        "era_tone": "A synthetic tone sentence.",
        "era_order": 1,
        "units": {
            "vanguard": {
                "category": "line", "squad_count": 1, "visual_scale": 1.0, "movement": "flying",
                "tiers": {"1": {"scene": "units/line_unit.tscn"}},
            },
        },
        "structures": {},
        "environment": {},
        "materials": {"1": {"faction_color_treatment": "matte"}},
        "faction_colors": {"0": "#00ffff"},
        "buildings": [dict(b) for b in _FIXTURE_BUILDINGS],
        "doctrines": ["boom", "fortify", "press", "balanced"],
    }


def _write_pack(pack_dir: Path, manifest: dict, *, with_scene=True) -> Path:
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    if with_scene:
        units_dir = pack_dir / "units"
        units_dir.mkdir(exist_ok=True)
        (units_dir / "line_unit.tscn").write_text("[gd_scene]\n")
    return pack_dir


def _write_banned_words(tmp_path: Path, words=("prototype", "placeholder")) -> Path:
    p = tmp_path / "banned_words.txt"
    p.write_text("\n".join(words) + "\n")
    return p


def _run(pack_dir: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PACK_VALIDATE), str(pack_dir), *extra],
        capture_output=True, text=True,
    )


def test_clean_pack_passes(tmp_path):
    pack = _write_pack(tmp_path / "pack", _base_manifest())
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PACK OK" in proc.stdout


def test_missing_required_key_named(tmp_path):
    manifest = _base_manifest()
    del manifest["era_accent_color"]
    pack = _write_pack(tmp_path / "pack", manifest)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MISSING_REQUIRED_KEY" in proc.stdout
    assert "era_accent_color" in proc.stdout


def test_banned_word_in_display_name_named(tmp_path):
    manifest = _base_manifest(era_display_name="Prototype Frontier")
    pack = _write_pack(tmp_path / "pack", manifest)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "BANNED_WORD" in proc.stdout
    assert "prototype" in proc.stdout.lower()


def test_banned_word_in_naming_pool_named(tmp_path):
    manifest = _base_manifest()
    manifest["naming_pools"] = {"region_names": ["Prototype Hollow", "Fine Reach"]}
    pack = _write_pack(tmp_path / "pack", manifest)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "BANNED_WORD" in proc.stdout
    assert "naming_pools" in proc.stdout


def test_unit_id_containing_era_id_named(tmp_path):
    manifest = _base_manifest(era_id="brokenera")
    manifest["units"] = {"brokenera_vanguard": manifest["units"]["vanguard"]}
    pack = _write_pack(tmp_path / "pack", manifest)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "ERA_ID_IN_UNIT_ID" in proc.stdout
    assert "brokenera_vanguard" in proc.stdout


def test_missing_scene_named(tmp_path):
    pack = _write_pack(tmp_path / "pack", _base_manifest(), with_scene=False)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MISSING_SCENE" in proc.stdout
    assert "units/line_unit.tscn" in proc.stdout


def test_missing_optional_weather_class_accepted(tmp_path):
    manifest = _base_manifest()
    assert "weather" not in manifest
    pack = _write_pack(tmp_path / "pack", manifest)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_three_defects_all_named_together(tmp_path):
    manifest = _base_manifest(era_id="brokenera", era_display_name="Prototype Frontier")
    manifest["units"] = {"brokenera_vanguard": manifest["units"]["vanguard"]}
    del manifest["era_accent_color"]
    pack = _write_pack(tmp_path / "pack", manifest)
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MISSING_REQUIRED_KEY" in proc.stdout
    assert "era_accent_color" in proc.stdout
    assert "BANNED_WORD" in proc.stdout
    assert "ERA_ID_IN_UNIT_ID" in proc.stdout


def test_exit_2_on_missing_pack_dir(tmp_path):
    proc = _run(tmp_path / "does_not_exist")
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_missing_manifest_is_a_named_finding(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MISSING_MANIFEST" in proc.stdout


def test_json_output_shape(tmp_path):
    pack = _write_pack(tmp_path / "pack", _base_manifest())
    banned = _write_banned_words(tmp_path)
    proc = _run(pack, "--banned-words", str(banned), "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["fail_count"] == 0


def test_diff_mechanical_identical_packs(tmp_path):
    pack_a = _write_pack(tmp_path / "a", _base_manifest(era_id="era_a", era_display_name="Era A"))
    pack_b = _write_pack(tmp_path / "b", _base_manifest(era_id="era_b", era_display_name="Era B"))
    proc = subprocess.run(
        [sys.executable, str(PACK_VALIDATE), "--diff-mechanical", str(pack_a), str(pack_b)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "MECHANICAL DIFF OK" in proc.stdout


def test_diff_mechanical_flags_a_real_gameplay_difference(tmp_path):
    manifest_a = _base_manifest(era_id="era_a", era_display_name="Era A")
    manifest_b = _base_manifest(era_id="era_b", era_display_name="Era B")
    manifest_b["units"]["vanguard"]["squad_count"] = 4
    pack_a = _write_pack(tmp_path / "a", manifest_a)
    pack_b = _write_pack(tmp_path / "b", manifest_b)
    proc = subprocess.run(
        [sys.executable, str(PACK_VALIDATE), "--diff-mechanical", str(pack_a), str(pack_b)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MECHANICAL DIFF FAILED" in proc.stdout


# ---- integration: the real evidence fixtures this PX ships, real banned_words.txt ----

def test_real_pack_clean_accepted():
    proc = _run(PX10_EVIDENCE / "pack_clean")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PACK OK" in proc.stdout


def test_real_pack_broken_rejected_with_all_three_defects():
    proc = _run(PX10_EVIDENCE / "pack_broken")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MISSING_REQUIRED_KEY" in proc.stdout
    assert "era_accent_color" in proc.stdout
    assert "BANNED_WORD" in proc.stdout
    assert "ERA_ID_IN_UNIT_ID" in proc.stdout


# ---- K2 (docs/northstar/plans/briefs/2026-09-22-two-day-push.md wave 3): both
# live assets/eras/** packs accept, and a broken copy of the new pack is
# rejected -- the two-pack contract this piece's acceptance names.

SETTLED_REACH_PACK = REPO / "assets" / "eras" / "settled_reach"
GREEK_PLACEHOLDER_PACK = REPO / "assets" / "eras" / "greek_placeholder"


def test_real_settled_reach_pack_accepted():
    proc = _run(SETTLED_REACH_PACK)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PACK OK" in proc.stdout


def test_real_greek_placeholder_pack_accepted():
    proc = _run(GREEK_PLACEHOLDER_PACK)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PACK OK" in proc.stdout


def test_greek_placeholder_mechanically_identical_to_settled_reach():
    proc = subprocess.run(
        [sys.executable, str(PACK_VALIDATE), "--diff-mechanical",
         str(GREEK_PLACEHOLDER_PACK), str(SETTLED_REACH_PACK)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "MECHANICAL DIFF OK" in proc.stdout


def test_greek_placeholder_copy_with_injected_banned_word_rejected(tmp_path):
    import shutil
    broken = tmp_path / "greek_placeholder_broken"
    shutil.copytree(GREEK_PLACEHOLDER_PACK, broken)
    manifest_path = broken / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["era_display_name"] = "The Prototype Reach"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    proc = _run(broken)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "BANNED_WORD" in proc.stdout
    assert "prototype" in proc.stdout.lower()


# ---- A58 (docs/northstar/plans/2026-10-01-architect-rulings-2.md, Q-C4-E1-05
# and 07; R-146-03, R-110-05): era_spatial_scale, era_tone and era_order are
# required pack identity; test_only is an optional bool. Red on main until the
# validator and the three installed manifests carry them.

import pytest

A58_REQUIRED = ("era_spatial_scale", "era_tone", "era_order")
TEST_ERA_PACK = REPO / "assets" / "eras" / "test_era"


def test_a58_base_manifest_with_new_keys_passes_control(tmp_path):
    # positive control: the synthetic manifest carries all three and is accepted
    pack = _write_pack(tmp_path / "pack", _base_manifest())
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("key", A58_REQUIRED)
def test_a58_missing_new_key_named(tmp_path, key):
    manifest = _base_manifest()
    del manifest[key]
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "MISSING_REQUIRED_KEY" in proc.stdout
    assert key in proc.stdout


def test_a58_all_three_missing_all_named(tmp_path):
    manifest = _base_manifest()
    for key in A58_REQUIRED:
        del manifest[key]
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    for key in A58_REQUIRED:
        assert key in proc.stdout


@pytest.mark.parametrize("bad", ["1", 1.5, True, None, [1]])
def test_a58_era_order_must_be_int(tmp_path, bad):
    manifest = _base_manifest()
    manifest["era_order"] = bad
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "era_order" in proc.stdout


@pytest.mark.parametrize("key", ("era_spatial_scale", "era_tone"))
@pytest.mark.parametrize("bad", [5, None, ["x"], ""])
def test_a58_text_keys_must_be_nonempty_text(tmp_path, key, bad):
    manifest = _base_manifest()
    manifest[key] = bad
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert key in proc.stdout


@pytest.mark.parametrize("value", [True, False])
def test_a58_test_only_bool_accepted_optional(tmp_path, value):
    manifest = _base_manifest()
    manifest["test_only"] = value
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_a58_test_only_absent_accepted(tmp_path):
    manifest = _base_manifest()
    assert "test_only" not in manifest
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("bad", ["yes", 1, None])
def test_a58_test_only_must_be_bool_when_present(tmp_path, bad):
    manifest = _base_manifest()
    manifest["test_only"] = bad
    pack = _write_pack(tmp_path / "pack", manifest)
    proc = _run(pack, "--banned-words", str(_write_banned_words(tmp_path)))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "test_only" in proc.stdout


@pytest.mark.parametrize("pack_dir", [SETTLED_REACH_PACK, GREEK_PLACEHOLDER_PACK, TEST_ERA_PACK],
                         ids=["settled_reach", "greek_placeholder", "test_era"])
def test_a58_installed_pack_has_the_new_keys_and_validates(pack_dir):
    manifest = json.loads((pack_dir / "manifest.json").read_text())
    for key in ("era_spatial_scale", "era_tone"):
        assert isinstance(manifest.get(key), str) and manifest[key].strip(), f"{pack_dir.name}: {key}"
    order = manifest.get("era_order")
    assert isinstance(order, int) and not isinstance(order, bool), f"{pack_dir.name}: era_order"
    proc = _run(pack_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PACK OK" in proc.stdout


def test_a58_installed_era_orders_are_distinct_ints():
    orders = {}
    for pack_dir in (SETTLED_REACH_PACK, GREEK_PLACEHOLDER_PACK):
        orders[pack_dir.name] = json.loads((pack_dir / "manifest.json").read_text()).get("era_order")
    assert all(isinstance(v, int) for v in orders.values()), orders
    assert orders["settled_reach"] != orders["greek_placeholder"], orders


def test_a58_only_test_era_is_test_only():
    flags = {p.name: json.loads((p / "manifest.json").read_text()).get("test_only", False)
             for p in (SETTLED_REACH_PACK, GREEK_PLACEHOLDER_PACK, TEST_ERA_PACK)}
    assert flags == {"settled_reach": False, "greek_placeholder": False, "test_era": True}, flags


def test_a58_removing_a_key_from_an_installed_pack_copy_is_rejected(tmp_path):
    # positive control for the installed-pack checks: a copy missing era_tone fails
    import shutil
    broken = tmp_path / "settled_broken"
    shutil.copytree(SETTLED_REACH_PACK, broken)
    path = broken / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest.pop("era_tone", None)
    path.write_text(json.dumps(manifest, indent=2))
    proc = _run(broken)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "era_tone" in proc.stdout
