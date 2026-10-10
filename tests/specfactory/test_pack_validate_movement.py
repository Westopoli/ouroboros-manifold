# spec: docs/northstar/plans/2026-10-06-terrain-stage3-spec.md piece 3f
"""Piece 3f tests (red first): era manifest roster rows carry "movement"
("walking" or "flying"), pack_validate requires it, and the cross-piece facts
the spec's "What the audit changed" / "What the pre-flight changed" tables fix
for 3f's consumers (TYPE_IDS table, flat movement_kinds, --era space form,
ui_data_bus key, named generate-failure error, the walkers ramp constants).

Source-shape checks for files other pieces own are text checks, so they fail
red now and pin the shape those pieces must land. Tests marked CONTROL are
positive controls: they pass on today's tree by design and prove the red tests
can go green (a synthetic pack with movement is accepted).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
PACK_VALIDATE = REPO / "scripts" / "specfactory" / "pack_validate.py"
ERAS = REPO / "assets" / "eras"
TYPE_IDS = {"raider": 0, "interceptor": 1, "vanguard": 2, "warden": 3,
            "bombard": 4, "bastion": 5}


def _text(rel: str) -> str:
    p = REPO / rel
    assert p.is_file(), f"{rel} does not exist"
    return p.read_text()


_FIXTURE_BUILDINGS = [
    {"id": "bld_a", "role": "production", "footprint": [3, 3], "hp": 200},
    {"id": "bld_b", "role": "house", "footprint": [2, 2], "hp": 100},
    {"id": "bld_c", "role": "worker-hut", "footprint": [2, 2], "hp": 80},
    {"id": "bld_d", "role": "forward-works", "footprint": [2, 2], "hp": 120},
]
# TD-VG-E-4: R-168-05 makes the building set part of every manifest.


def _manifest(units: dict):
    return {
        "era_id": "synth_era", "era_display_name": "Synth Era",
        "era_accent_color": "#123456", "era_spatial_scale": "s.", "era_tone": "t.",
        "era_order": 1, "units": units, "structures": {},
        "environment": {}, "materials": {"1": {"faction_color_treatment": "matte"}},
        "faction_colors": {"0": "#00ffff"},
        "buildings": [dict(b) for b in _FIXTURE_BUILDINGS],
        "doctrines": ["boom", "fortify", "press", "balanced"],
    }


def _unit(movement=None):
    u = {"category": "line", "squad_count": 1, "visual_scale": 1.0,
         "tiers": {"1": {"scene": "units/line_unit.tscn"}}}
    if movement is not None:
        u["movement"] = movement
    return u


def _pack(tmp_path, units):
    d = tmp_path / "pack"
    (d / "units").mkdir(parents=True)
    (d / "units" / "line_unit.tscn").write_text("[gd_scene]\n")
    (d / "manifest.json").write_text(json.dumps(_manifest(units)))
    return d


def _run(pack):
    return subprocess.run([sys.executable, str(PACK_VALIDATE), str(pack)],
                          capture_output=True, text=True)


# ---- pack_validate -------------------------------------------------------

def test_control_rows_with_movement_accepted(tmp_path):
    """CONTROL (green now): a roster with movement on every row passes."""
    pack = _pack(tmp_path, {"vanguard": _unit("walking"), "raider": _unit("flying")})
    proc = _run(pack)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_row_without_movement_rejected_and_named(tmp_path):
    """Spec 3f: 'pack_validate rejects a roster row without movement'.
    Red now: validator never reads movement, exits 0."""
    pack = _pack(tmp_path, {"vanguard": _unit("walking"), "raider": _unit(None)})
    proc = _run(pack)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "raider" in proc.stdout and "movement" in proc.stdout.lower()
    assert "vanguard" not in proc.stdout.replace("PACK FAILED", "")


def test_row_with_bad_movement_value_rejected(tmp_path):
    """The field is 'walking' or 'flying' (spec audit table). Red now."""
    pack = _pack(tmp_path, {"vanguard": _unit("swimming")})
    proc = _run(pack)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "movement" in proc.stdout.lower()


@pytest.mark.parametrize("era", ["settled_reach", "greek_placeholder"])
def test_real_manifest_passes_validator(era):
    """Spec 3f: 'both manifests pass'. Green now; stays green once the field
    is required (guards the manifest edit against the new rule)."""
    proc = _run(ERAS / era)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def _units(era):
    return json.loads((ERAS / era / "manifest.json").read_text())["units"]


def test_settled_reach_all_flying():
    """Spec 3f: settled_reach all flying. Red now: no movement field."""
    units = _units("settled_reach")
    assert units, "no roster"
    assert {k: v.get("movement") for k, v in units.items()} == {k: "flying" for k in units}


def test_greek_placeholder_walking_except_scout():
    """Spec 3f: greek_placeholder walking except the placeholder scout
    (flying, R-201-01). Red now: no movement field. The manifest has no scout
    row today; if one is added it must be flying and every other row walking."""
    units = _units("greek_placeholder")
    for name, row in units.items():
        want = "flying" if "scout" in name.lower() else "walking"
        assert row.get("movement") == want, f"{name}: {row.get('movement')!r} != {want!r}"
    assert units


def test_test_era_manifest_has_movement():
    """The validator's third pack (assets/eras/test_era) must also pass once
    movement is required; every row carries the field. Red now."""
    for name, row in _units("test_era").items():
        assert row.get("movement") in ("walking", "flying"), name
    assert _run(ERAS / "test_era").returncode == 0


# ---- TYPE_IDS table in era_config.gd (audit/pre-flight: 3f writes it) -----

def test_era_config_has_type_ids_table():
    """Pre-flight: 'const TYPE_IDS = {raider 0, ...}' in autoload/era_config.gd
    matching csrc/unit.c OM_UT_*. Red now: no table."""
    src = _text("autoload/era_config.gd")
    m = re.search(r"const\s+TYPE_IDS\b[^=]*=\s*\{(.*?)\}", src, re.S)
    assert m, "no `const TYPE_IDS = {...}` in era_config.gd"
    found = {k: int(v) for k, v in re.findall(r'"?(\w+)"?\s*:\s*(\d+)', m.group(1))}
    assert found == TYPE_IDS


def test_type_ids_match_sim_table():
    """CONTROL (green now): the spec's table equals csrc/unit.c OM_UT_*."""
    c = _text("csrc/unit.c")
    for name, tid in TYPE_IDS.items():
        assert re.search(rf"#define\s+OM_UT_{name.upper()}\s+{tid}\b", c), name


def test_era_active_id_is_var_set_from_arg_or_setting():
    """Audit: ACTIVE_ERA_ID becomes a var (was const, era_config.gd:3), set
    from the --era user arg, else the saved setting, else settled_reach.
    Red now: it is a const."""
    src = _text("autoload/era_config.gd")
    assert re.search(r"^var\s+ACTIVE_ERA_ID\b", src, re.M), "ACTIVE_ERA_ID is not a var"
    assert not re.search(r"^const\s+ACTIVE_ERA_ID\b", src, re.M)
    assert '"--era"' in src and "get_cmdline_user_args" in src
    assert "--era=" not in src, "space form `--era <id>`, not `--era=<id>`"
    assert "settled_reach" in src


def test_era_config_reads_kind_and_movement():
    """Audit 3e: EraConfig.kind() and EraConfig.movement_kinds() read the
    manifest; movement_kinds() returns the flat [t, k, t, k, ...] list.
    Red now."""
    src = _text("autoload/era_config.gd")
    assert re.search(r"func\s+kind\s*\(", src)
    assert re.search(r"func\s+movement_kinds\s*\(", src)
    assert '"movement"' in src and "TYPE_IDS" in src


# ---- --era <id> space form, daemon_client extra_args ----------------------

def test_daemon_client_extra_args_space_form():
    """Pre-flight: daemon_client.py gains extra_args appended after
    `--seed <n>` in the user-arg group; QA passes `--era <id>`. Red now."""
    src = _text("tests/qa/desktop/daemon_client.py")
    assert re.search(r"def __init__\(self[^)]*extra_args", src, re.S), "no extra_args parameter"
    assert "*self.extra_args" in src or "+ list(self.extra_args)" in src or "extend(self.extra_args)" in src
    assert "--era=" not in src


# ---- UIDataBus settings key -----------------------------------------------

def test_ui_data_bus_keeps_era_id_key():
    """Pre-flight: save/load rebuild from fixed key lists and drop unknown
    keys; 3e adds [game] era_id in both branches of _load_settings and in
    save_settings. Red now."""
    src = _text("autoload/ui_data_bus.gd")
    load = src[src.index("func _load_settings"):src.index("func _apply_stored_settings")]
    assert len(re.findall(r'"era_id"', load)) >= 2, "era_id missing from a _load_settings branch"
    assert 'config.get_value("game", "era_id"' in load
    save = src[src.index("func save_settings"):]
    assert 'config.set_value("game", "era_id"' in save
    assert '"era_id"' in save.split("config.set_value")[0], "era_id not in the clamped dict"


# ---- pipe: flat movement_kinds, order, named failure ----------------------

def test_pipe_parses_flat_movement_kinds_before_era_kind():
    """Pre-flight: flat `movement_kinds` via get_int_array in
    handle_mission_start; om_roster_set_movement_kind applied once before
    om_set_era_kind. Red now: the pipe does not read movement_kinds."""
    src = _text("csrc/pipe/om_pipe.c")
    assert re.search(r'get_int_array\([^)]*"movement_kinds"', src)
    a = src.find("om_roster_set_movement_kind(")
    b = src.find("om_set_era_kind(W")
    assert a != -1, "om_roster_set_movement_kind never called by the pipe"
    assert b != -1 and a < b, "movement kinds must be applied before om_set_era_kind"


def test_pipe_named_error_on_generate_failure():
    """Pre-flight/audit 3a/3b: the -1 generate failure answers
    write_error("mission_start", "terrain generate failed"), no silent flat
    mission. Red now: the string is only in docs; the pipe and mission.c do
    not raise it."""
    pipe = _text("csrc/pipe/om_pipe.c")
    mission = _text("csrc/mission.c")
    assert "terrain generate failed" in pipe
    assert "om_terrain_generate(" in mission, "mission.c never generates ground terrain"
    assert "om_terrain_clear(" in mission, "space missions must clear terrain"


def test_pipe_bad_movement_kinds_named_error():
    """docs/architecture.md (contract piece): odd length or kind not 0/1
    answers reason `bad movement_kinds`. Red now."""
    assert "bad movement_kinds" in _text("csrc/pipe/om_pipe.c")


def test_client_sends_movement_kinds_from_era_config():
    """Spec 3c: mission_start sends era_kind and movement_kinds from
    EraConfig. Red now."""
    src = _text("autoload/c_bridge.gd")
    # TD-T3-bridge-call: the autoload is resolved at runtime, so the call may
    # be dynamic (era.call("movement_kinds")).
    assert '"movement_kinds"' in src and (
        "EraConfig.movement_kinds()" in src or 'call("movement_kinds")' in src)
    assert '"era_kind"' in src


# ---- 3d ramp constants (origin/push/proto-walkers) ------------------------

BAND_COLOURS = [(0.40, 0.72, 0.42), (0.72, 0.80, 0.38), (0.90, 0.68, 0.30),
                (0.72, 0.48, 0.30), (0.92, 0.90, 0.88)]
STEEP_COLOUR = (0.85, 0.10, 0.85)


def _colours(text, name):
    m = re.search(rf"const\s+{name}\b[^=]*=\s*(.*)", text)
    assert m, f"{name} not found"
    return [tuple(float(x) for x in t) for t in re.findall(
        r"Color\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)", m.group(1))]


def test_control_ramp_constants_match_walkers_mockup():
    """CONTROL (green when the proto branch is fetched): the constants in
    this file equal the walkers mockup's on origin/push/proto-walkers."""
    r = subprocess.run(["git", "-C", str(REPO), "show",
                        "origin/push/proto-walkers:scenes/mockups/walkers/walkers_mockup.gd"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("origin/push/proto-walkers not fetched")
    assert _colours(r.stdout, "BAND_COLOURS") == BAND_COLOURS
    assert _colours(r.stdout, "STEEP_COLOUR") == [STEEP_COLOUR]


def test_terrain_layer_uses_the_walkers_ramp():
    """Pre-flight 3d: terrain_layer.gd carries BAND_COLOURS and STEEP_COLOUR
    (lerped 0.5 on unwalkable land); WATER_COLOUR unused (the sim has no
    water). Red now: the file does not exist."""
    src = _text("scenes/tactical_c/terrain_layer.gd")
    assert _colours(src, "BAND_COLOURS") == BAND_COLOURS
    assert _colours(src, "STEEP_COLOUR") == [STEEP_COLOUR]
    assert re.search(r"lerp\(\s*STEEP_COLOUR\s*,\s*0\.5\s*\)", src)
    assert "WATER_COLOUR" not in src
