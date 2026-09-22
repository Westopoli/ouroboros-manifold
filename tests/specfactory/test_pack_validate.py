# spec: docs/northstar/plans/briefs/2026-09-21-px-batch-b-spec-content-boundary.md PX-10
"""Tests for scripts/specfactory/pack_validate.py.

Builds a throwaway synthetic era pack per unit test (mirrors
assets/eras/test_era's manifest shape: era_id, era_display_name,
era_accent_color, units, structures, environment, materials, faction_colors)
so this suite does not depend on the real assets/eras/** packs. The last two
tests exercise the real docs/northstar/proving_ground/evidence/px10/
{pack_clean,pack_broken} fixtures this PX ships, using the real
banned_words.txt.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PACK_VALIDATE = REPO / "scripts" / "specfactory" / "pack_validate.py"
PX10_EVIDENCE = REPO / "docs" / "northstar" / "proving_ground" / "evidence" / "px10"


def _base_manifest(era_id="synth_era", era_display_name="Synth Era"):
    return {
        "era_id": era_id,
        "era_display_name": era_display_name,
        "era_accent_color": "#123456",
        "units": {
            "vanguard": {
                "category": "line", "squad_count": 1, "visual_scale": 1.0,
                "tiers": {"1": {"scene": "units/line_unit.tscn"}},
            },
        },
        "structures": {},
        "environment": {},
        "materials": {"1": {"faction_color_treatment": "matte"}},
        "faction_colors": {"0": "#00ffff"},
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
