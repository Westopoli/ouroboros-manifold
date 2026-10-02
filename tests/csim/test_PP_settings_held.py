"""PP-contract tests held out of the A1 landing branch: they are RED until a later wave lands the code that
turns them green (PP-unit: om_command_set_layer, per-tick set-param read in the fight; PP-fog: om_command_ping;
PP-move/mapgen: block_rect layer range; settings surviving om_tactical_reset and a new world starting at the
defaults). Moved verbatim from tests/csim/test_PP_settings.py with the helpers they need; no assertion changed.
Stories and rules proved are those named in that file's docstring."""
import ctypes
import math
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "northstar" / "plans" / "push" / "pp_contract.md"
HEADER = REPO / "csrc" / "ouroboros_sim.h"


def _header_constant(name):
    m = re.search(rf"^[ \t]*#define[ \t]+{name}[ \t]+([0-9.]+)", HEADER.read_text(), re.M)
    assert m, f"{name} is not defined in csrc/ouroboros_sim.h (A132/A133 name it as a header constant)"
    return float(m.group(1))


def _load_params():
    rows, inside = [], False
    for line in DOC.read_text().splitlines():
        if line.startswith("| # | member |"):
            inside = True
            continue
        if not inside:
            continue
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0].startswith("---"):
            continue
        name = cells[1].strip("`")
        if name == "OM_TP__COUNT":
            continue
        rows.append({"value": int(cells[0]), "name": name, "kind": cells[2],
                     "default": float(cells[3]), "lo": float(cells[4]), "hi": float(cells[5])})
    return rows


PARAMS = _load_params()
COUNT = len(PARAMS)
BY_NAME = {p["name"]: p for p in PARAMS}
IDS = [p["name"] for p in PARAMS]




def _other_valid_value(p):
    """A value in range that is not the default."""
    if p["kind"] in ("bool", "int"):
        for v in (p["lo"], p["hi"], p["lo"] + 1.0):
            if p["lo"] <= v <= p["hi"] and v != p["default"]:
                return v
    mid = (p["lo"] + p["hi"]) / 2.0
    return mid if mid != p["default"] else p["hi"]


@pytest.fixture
def w(world_factory):
    return world_factory(n_regions=1)



RAIDER, VANGUARD = 0, 2           # OMUnitType in test_E11_S084_flat_damage.py: Strike attacker, Line target
STRIKE_LINE = BY_NAME["OM_TP_CATMULT_STRIKE_LINE"]
FIGHT_TICKS = 40


def _hits(lib, world_factory, *, set_before_spawn=None, set_after_tick=None, then_refuse=None):
    """Per-tick damage a Raider (explicit attack-target order, abilities off) deals to a Vanguard 100 wu away,
    as {tick: damage} over FIGHT_TICKS ticks. set_before_spawn: a value for CATMULT_STRIKE_LINE set before any
    unit exists; set_after_tick: (value, n), set after n steps; then_refuse: an out-of-range value tried right
    after the before-spawn set, which must be refused."""
    w = world_factory(n_regions=1)
    lib.om_tactical_disable_abilities(w)
    if set_before_spawn is not None:
        assert lib.om_tactical_set_param(w, STRIKE_LINE["value"], set_before_spawn) == 0
    if then_refuse is not None:
        assert lib.om_tactical_set_param(w, STRIKE_LINE["value"], then_refuse) == -1
    attacker = lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    target = lib.om_unit_spawn(w, VANGUARD, 1, 100.0, 0.0, 0)
    lib.om_command_attack_target(w, attacker, target)
    hits, hp = {}, lib.om_unit_hp(w, target)
    for tick in range(1, FIGHT_TICKS + 1):
        if set_after_tick is not None and tick == set_after_tick[1] + 1:
            assert lib.om_tactical_set_param(w, STRIKE_LINE["value"], set_after_tick[0]) == 0
        lib.om_tactical_step(w)
        now = lib.om_unit_hp(w, target)
        if now < hp:
            hits[tick] = hp - now
        hp = now
    return hits

def test_G1_a_set_before_any_unit_spawns_applies_to_the_whole_fight(lib, world_factory):
    ref = _hits(lib, world_factory)
    new = _hits(lib, world_factory, set_before_spawn=1.5)       # 1.5 / 0.75 = exactly x2
    assert list(new) == list(ref), "same hit ticks"
    for tick in ref:
        assert new[tick] == pytest.approx(2.0 * ref[tick], abs=1e-9), tick


def test_G1_a_set_after_spawn_and_before_the_first_step_applies_to_every_hit(lib, world_factory):
    ref = _hits(lib, world_factory)
    new = _hits(lib, world_factory, set_after_tick=(1.5, 0))
    assert list(new) == list(ref)
    for tick in ref:
        assert new[tick] == pytest.approx(2.0 * ref[tick], abs=1e-9), tick


def test_G1_a_set_mid_fight_takes_effect_on_the_next_tick(lib, world_factory):
    """Set after tick 4: hits on ticks 1 to 4 are unchanged, hits from tick 5 on are doubled. The control is
    that both groups exist, so a set that applied to nothing, or to everything, fails."""
    set_at = 4
    ref = _hits(lib, world_factory)
    new = _hits(lib, world_factory, set_after_tick=(1.5, set_at))
    assert list(new) == list(ref)
    early = [t for t in ref if t <= set_at]
    late = [t for t in ref if t > set_at]
    assert late, "fixture: at least one hit must land after the set"
    for tick in early:
        assert new[tick] == pytest.approx(ref[tick], abs=1e-9), f"tick {tick} is before the set"
    for tick in late:
        assert new[tick] == pytest.approx(2.0 * ref[tick], abs=1e-9), f"tick {tick} is after the set"


def test_G1_a_refused_set_leaves_the_fight_as_it_was(lib, world_factory):
    """The in-range 1.5 is set, then 11.0 (above the range) is refused: the fight still runs at 1.5, doubled,
    not reverted to the default and not at 11.0. The doubling is the positive control that 1.5 applied."""
    ref = _hits(lib, world_factory)
    new = _hits(lib, world_factory, set_before_spawn=1.5, then_refuse=STRIKE_LINE["hi"] + 1.0)
    assert list(new) == list(ref)
    for tick in ref:
        assert new[tick] == pytest.approx(2.0 * ref[tick], abs=1e-9), tick


def test_PP_settings_survive_om_tactical_reset(lib, w):
    p = BY_NAME["OM_TP_ATTACK_MOVE_LEASH"]
    q = BY_NAME["OM_TP_CATMULT_STRIKE_LINE"]
    assert lib.om_tactical_set_param(w, p["value"], 123.0) == 0
    assert lib.om_tactical_set_param(w, q["value"], 1.5) == 0
    unit = lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    assert lib.om_unit_alive(w, unit) == 1 and lib.om_unit_count(w) == 1, "control: there is tactical state to reset"
    lib.om_tactical_reset(w)
    assert lib.om_unit_count(w) == 0, "control: the reset really cleared the tactical state"
    assert lib.om_tactical_get_param(w, p["value"]) == 123.0
    assert lib.om_tactical_get_param(w, q["value"]) == 1.5
    other = BY_NAME["OM_TP_VANTAGE_MULT"]
    assert lib.om_tactical_get_param(w, other["value"]) == pytest.approx(other["default"], abs=1e-12)


def test_PP_a_new_world_starts_at_the_defaults_after_another_world_was_set(lib, world_factory):
    """No setting leaks between worlds, and none outlives om_tactical_reset into a world made later."""
    a = world_factory(n_regions=1)
    for p in PARAMS:
        assert lib.om_tactical_set_param(a, p["value"], _other_valid_value(p)) == 0, p["name"]
    lib.om_tactical_reset(a)
    b = world_factory(n_regions=1)
    for p in PARAMS:
        assert lib.om_tactical_get_param(b, p["value"]) == pytest.approx(p["default"], abs=1e-12), p["name"]
    assert lib.om_tactical_get_param(a, PARAMS[6]["value"]) == pytest.approx(_other_valid_value(PARAMS[6]), abs=1e-12), \
        "control: world a still holds what was set"


def test_E01_A132_block_rect_takes_layers_0_to_4_and_refuses_5(lib, w):
    top = int(_header_constant("OM_LAYER_COUNT")) - 1
    assert lib.om_map_set_canvas(w, 8000.0, 8000.0) == 0
    assert lib.om_map_block_rect(w, 0.0, 0.0, 300.0, 300.0, 0, top) == 0, "control: the whole range 0 to 4 is accepted"
    assert lib.om_map_block_rect(w, 0.0, 0.0, 300.0, 300.0, top, top) == 0, "control: the top layer alone"
    assert lib.om_map_block_rect(w, 0.0, 0.0, 300.0, 300.0, 0, top + 1) == -1
    assert lib.om_map_block_rect(w, 0.0, 0.0, 300.0, 300.0, top + 1, top + 1) == -1
    assert lib.om_map_block_rect(w, 0.0, 0.0, 300.0, 300.0, 2, 1) == -1, "layer_lo above layer_hi"


def test_E01_A132_command_set_layer_takes_layers_0_to_4_and_refuses_5(lib, w):
    """Red until PP-unit lands om_command_set_layer (a stub returns 0 for everything); A135 pending list."""
    top = int(_header_constant("OM_LAYER_COUNT")) - 1
    unit = lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    ids = (ctypes.c_uint32 * 1)(unit)
    assert lib.om_command_set_layer(w, ids, 1, top) == 0, "control: the top layer is accepted"
    assert lib.om_command_set_layer(w, ids, 1, 0) == 0, "control: the bottom layer is accepted"
    assert lib.om_command_set_layer(w, ids, 1, top + 1) == -1


def test_E01_A132_command_ping_refuses_a_layer_at_or_above_the_count_with_reason_4(lib, world_factory):
    """Red until PP-fog lands om_command_ping (a stub returns 0); A135 pending list. A fresh world each call
    so cooldown cannot cause the refusal."""
    top = int(_header_constant("OM_LAYER_COUNT")) - 1

    def ping(layer):
        w = world_factory(n_regions=1)
        caster = lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
        return lib.om_command_ping(w, caster, layer, 100.0, 0.0)

    assert ping(top) == 0, "control: the top layer is a valid ping layer"
    assert ping(top + 1) == 4
