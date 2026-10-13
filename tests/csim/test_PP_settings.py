"""PP-contract: the run-time settings call and the canvas call (cascade brief section 5 G1; plan appendix,
docs/northstar/plans/push/pp_contract.md sections 3 to 5).

Stories and rules this proves: the brief's G1 ("rule numbers settable at run time": default equals the
constant, in range is accepted, out of range is refused and changes nothing, set before spawn applies to the
whole fight, set mid-fight takes effect on the next tick) and the plan appendix row for `om_map_set_canvas`.
The rule numbers behind the settings are R-084-01 (category multiplier, used here to show a set is applied),
R-087-05 (leash), R-005-02 (cross-layer vision), S-162 and S-163 (ping and emission numbers).

Also here (rulings-2 Addendum 46): canvas limit OM_MAP_MAX_CANVAS (A133 Q-C3), settings survive om_tactical_reset
and are not hashed (A133 Q-C4), the layer range 0 to OM_LAYER_COUNT - 1 and the cover height rule (A132), and the
unknown-unit returns of the three read-only getters (A133). The getters' bodies are stubs in the contract wave, so
no behaviour beyond the unknown-unit return is tested here.

Not here, by design: what the switches DO to movement, targeting or sight. Other writers own that.

The new calls are not bound in tests/csim/conftest.py until the contract lands, so today every test fails on
`AttributeError: ... om_tactical_set_param` (or om_map_set_canvas). That is the expected red. Once the
contract lands but before PP-move and PP-mapgen do, the generated stubs return 0 and 0.0 and these tests fail on
behaviour. The defaults, ranges and order are read from the contract document's section 4 table.

Every refusal check has a positive control: an in-range set on the same parameter that must return 0 and
read back, so a call that refuses (or accepts) everything cannot pass."""
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


def test_control_table_has_every_member_and_the_six_named_defaults():
    """The table this file reads is whole: 66 members in order, the plan's six switches at their defaults.
    If the parser read nothing, every parametrized test below would silently vanish; this one would not."""
    assert COUNT == 66
    assert [p["value"] for p in PARAMS] == list(range(COUNT))
    for name, default in (("OM_TP_PURSUE_BY_STEERING", 1), ("OM_TP_ROUTE_AROUND_TERRAIN", 1),
                          ("OM_TP_LEASH_BEFORE_DAMAGE", 0), ("OM_TP_TARGET_POLICY", 0),
                          ("OM_TP_TARGET_BY_SIGHT", 1), ("OM_TP_ROUTE_ACROSS_LAYERS", 1)):
        assert BY_NAME[name]["default"] == default
        assert BY_NAME[name]["value"] == [p["name"] for p in PARAMS].index(name)


def _other_valid_value(p):
    """A value in range that is not the default."""
    if p["kind"] in ("bool", "int"):
        for v in (p["lo"], p["hi"], p["lo"] + 1.0):
            if p["lo"] <= v <= p["hi"] and v != p["default"]:
                return v
    mid = (p["lo"] + p["hi"]) / 2.0
    return mid if mid != p["default"] else p["hi"]


def _snapshot(lib, w):
    return [lib.om_tactical_get_param(w, p["value"]) for p in PARAMS]


@pytest.fixture
def w(world_factory):
    return world_factory(n_regions=1)


# ---- defaults ----

@pytest.mark.parametrize("p", PARAMS, ids=IDS)
def test_G1_every_parameter_defaults_to_its_documented_value(lib, w, p):
    assert lib.om_tactical_get_param(w, p["value"]) == pytest.approx(p["default"], abs=1e-12), p["name"]


# ---- in range: accepted and read back ----

@pytest.mark.parametrize("p", PARAMS, ids=IDS)
def test_G1_a_set_in_range_returns_0_and_reads_back(lib, w, p):
    v = _other_valid_value(p)
    assert lib.om_tactical_set_param(w, p["value"], v) == 0, f"{p['name']}={v}"
    assert lib.om_tactical_get_param(w, p["value"]) == pytest.approx(v, abs=1e-12)


@pytest.mark.parametrize("p", PARAMS, ids=IDS)
def test_G1_both_ends_of_the_range_are_inclusive(lib, w, p):
    for v in (p["lo"], p["hi"]):
        assert lib.om_tactical_set_param(w, p["value"], v) == 0, f"{p['name']}={v}"
        assert lib.om_tactical_get_param(w, p["value"]) == pytest.approx(v, abs=1e-12)


@pytest.mark.parametrize("p", PARAMS, ids=IDS)
def test_G1_a_set_changes_that_parameter_and_no_other(lib, w, p):
    before = _snapshot(lib, w)
    v = _other_valid_value(p)
    assert lib.om_tactical_set_param(w, p["value"], v) == 0
    after = _snapshot(lib, w)
    for q, b, a in zip(PARAMS, before, after):
        if q["name"] == p["name"]:
            assert a == pytest.approx(v, abs=1e-12)
        else:
            assert a == b, f"setting {p['name']} moved {q['name']}"


def test_G1_two_worlds_hold_their_own_settings(lib, world_factory):
    a, b = world_factory(n_regions=1), world_factory(n_regions=1)
    p = BY_NAME["OM_TP_ATTACK_MOVE_LEASH"]
    assert lib.om_tactical_set_param(a, p["value"], 0.0) == 0
    assert lib.om_tactical_get_param(a, p["value"]) == 0.0
    assert lib.om_tactical_get_param(b, p["value"]) == pytest.approx(p["default"], abs=1e-12)


# ---- out of range: refused, nothing changes (each with its positive control) ----

def _refusal_cases(p):
    """[(label, value)] that must be refused for this parameter."""
    cases = [("below lo", p["lo"] - 1.0), ("above hi", p["hi"] + 1.0),
             ("NaN", float("nan")), ("+inf", math.inf), ("-inf", -math.inf)]
    if p["kind"] in ("bool", "int"):
        cases.append(("fractional", p["lo"] + 0.5))
    return cases


@pytest.mark.parametrize("p", PARAMS, ids=IDS)
def test_G1_an_out_of_range_set_returns_minus_1_and_changes_nothing(lib, w, p):
    valid = _other_valid_value(p)
    # positive control: the in-range set on this very parameter succeeds and sticks
    assert lib.om_tactical_set_param(w, p["value"], valid) == 0, f"control: {p['name']}={valid} must be accepted"
    assert lib.om_tactical_get_param(w, p["value"]) == pytest.approx(valid, abs=1e-12)
    before = _snapshot(lib, w)
    for label, bad in _refusal_cases(p):
        rc = lib.om_tactical_set_param(w, p["value"], bad)
        assert rc == -1, f"{p['name']} {label} ({bad}) returned {rc}, expected -1"
        assert _snapshot(lib, w) == before, f"{p['name']} {label} changed a setting"


def test_G1_an_unknown_parameter_is_refused_and_changes_nothing(lib, w):
    # positive control: the last real member accepts a set
    last = PARAMS[-1]
    assert lib.om_tactical_set_param(w, last["value"], _other_valid_value(last)) == 0
    before = _snapshot(lib, w)
    for unknown in (COUNT, COUNT + 1, 1000, -1, -1000):
        assert lib.om_tactical_set_param(w, unknown, 1.0) == -1, f"param {unknown}"
        assert _snapshot(lib, w) == before, f"param {unknown} changed a setting"


def test_G1_get_of_an_unknown_parameter_returns_minus_1(lib, w):
    # positive control: a real member does not read -1 (every valid value is non-negative)
    assert lib.om_tactical_get_param(w, 0) != -1.0
    for unknown in (COUNT, COUNT + 1, -1):
        assert lib.om_tactical_get_param(w, unknown) == -1.0, f"param {unknown}"


def test_G1_a_null_world_is_refused(lib, w):
    assert lib.om_tactical_set_param(w, 0, 1.0) == 0, "control: a real world accepts the same call"
    assert lib.om_tactical_set_param(None, 0, 1.0) == -1
    assert lib.om_tactical_get_param(None, 0) == -1.0


# ---- before spawn, and mid-fight ----

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


def test_G1_the_reference_fight_lands_hits_at_the_default_multiplier(lib, world_factory):
    """Control for the fixture: the default fight lands at least two hits, each Raider base 9.0 x Strike->Line
    0.75 (R-084-01), so the ratio tests below measure what they say."""
    hits = _hits(lib, world_factory)
    assert len(hits) >= 2, hits
    for tick, dmg in hits.items():
        assert dmg == pytest.approx(9.0 * 0.75, abs=1e-6), (tick, dmg)


# ---- canvas ----

def test_PP_canvas_a_positive_size_is_accepted(lib, w):
    assert lib.om_map_set_canvas(w, 8000.0, 8000.0) == 0
    assert lib.om_map_set_canvas(w, 12000.0, 9000.0) == 0, "width and height are independent, and a new call replaces"
    assert lib.om_map_set_canvas(w, 1.0, 1.0) == 0, "any positive size is accepted"


@pytest.mark.parametrize("width,height", [
    (0.0, 8000.0), (8000.0, 0.0), (0.0, 0.0), (-1.0, 8000.0), (8000.0, -1.0), (-8000.0, -8000.0),
    (float("nan"), 8000.0), (8000.0, float("nan")), (math.inf, 8000.0), (8000.0, math.inf),
], ids=lambda v: str(v))
def test_PP_canvas_a_non_positive_or_non_finite_size_returns_minus_1(lib, w, width, height):
    assert lib.om_map_set_canvas(w, 8000.0, 8000.0) == 0, "control: a positive size is accepted on this world"
    assert lib.om_map_set_canvas(w, width, height) == -1, f"({width}, {height})"
    assert lib.om_map_set_canvas(w, 9000.0, 9000.0) == 0, "a refused call leaves the world able to take a good one"


def test_PP_canvas_a_null_world_returns_minus_1(lib, w):
    assert lib.om_map_set_canvas(w, 8000.0, 8000.0) == 0, "control"
    assert lib.om_map_set_canvas(None, 8000.0, 8000.0) == -1


def test_PP_canvas_a_side_above_the_limit_is_refused_and_the_limit_itself_is_accepted(lib, w):
    """A133 Q-C3: width or height above OM_MAP_MAX_CANVAS (28,000) returns -1. Control: exactly the limit is fine."""
    limit = _header_constant("OM_MAP_MAX_CANVAS")
    assert limit == 28000.0
    assert lib.om_map_set_canvas(w, limit, limit) == 0, "control: the limit itself is accepted"
    over = limit + 1.0
    for width, height in ((over, 8000.0), (8000.0, over), (over, over), (limit * 2, 100.0), (100.0, 1e12)):
        assert lib.om_map_set_canvas(w, width, height) == -1, f"({width}, {height})"
    assert lib.om_map_set_canvas(w, 8000.0, 8000.0) == 0, "a refused call leaves the world able to take a good one"


# ---- settings are configuration: survive reset, not hashed, a new world starts at defaults (A133 Q-C4) ----

def test_PP_a_set_does_not_change_the_state_checksum(lib, w):
    """Settings are not hashed (A133 Q-C4). The only world checksum today hashes regions and the tick, so the
    control moves the tick: the checksum must react to that, or the unchanged reads below prove nothing."""
    before = lib.om_world_get_state_checksum(w)
    lib.om_world_set_tick(w, 7)
    with_tick = lib.om_world_get_state_checksum(w)
    assert with_tick != before, "control: the checksum must react to a state change"
    lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    for name, v in (("OM_TP_ATTACK_MOVE_LEASH", 0.0), ("OM_TP_CATMULT_STRIKE_LINE", 1.5),
                    ("OM_TP_TARGETING_COHORTS", 7.0), ("OM_TP_PURSUE_BY_STEERING", 0.0)):
        assert lib.om_tactical_set_param(w, BY_NAME[name]["value"], v) == 0, name
        assert lib.om_world_get_state_checksum(w) == with_tick, f"setting {name} changed the checksum"
    lib.om_tactical_reset(w)
    assert lib.om_world_get_state_checksum(w) == with_tick, "a reset that keeps the settings leaves the hash alone"


# ---- cover height is a whole count of layers from the bottom (A132) ----

def _cover_count(lib, w):
    return lib.om_map_cover_count(w)


def _cover_height(lib, w, index):
    h = ctypes.c_double(-99.0)
    assert lib.om_map_cover_at(w, index, None, None, None, ctypes.byref(h)) == 1
    return h.value


@pytest.mark.parametrize("height", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
def test_E01_A132_a_whole_layer_count_height_from_0_to_5_is_accepted_and_stored(lib, w, height):
    """h blocks engine layers 0 to h-1; 0 adds an obstacle that blocks nothing; 5 blocks all five."""
    assert _header_constant("OM_LAYER_COUNT") == 5.0
    n = _cover_count(lib, w)
    idx = lib.om_map_add_cover(w, 10.0, 20.0, 5.0, height)
    assert idx == n + 1, f"height {height}: expected the 1-based index of a new row, got {idx}"
    assert _cover_count(lib, w) == n + 1
    assert _cover_height(lib, w, n) == height


@pytest.mark.parametrize("height", [
    0.5, 1.5, 4.999, 0.0001, -1.0, -0.5, -5.0, 5.0001, 5.5, 6.0, 100.0, 1e300,
    float("nan"), math.inf, -math.inf], ids=lambda v: str(v))
def test_E01_A132_a_fractional_negative_non_finite_or_above_5_height_is_refused(lib, w, height):
    """Refused: returns 0 and adds nothing. Control: a whole in-range height on the same world is accepted
    afterwards and gets row index 1, so the refused call left no row behind."""
    assert lib.om_map_add_cover(w, 10.0, 20.0, 5.0, height) == 0, f"height {height}"
    assert _cover_count(lib, w) == 0, f"height {height} left a row behind"
    assert lib.om_map_add_cover(w, 10.0, 20.0, 5.0, 3.0) == 1, "control: a whole height is accepted"
    assert _cover_count(lib, w) == 1


def test_E01_A132_the_height_limit_follows_the_layer_count_constant(lib, w):
    top = _header_constant("OM_LAYER_COUNT")
    assert lib.om_map_add_cover(w, 0.0, 0.0, 5.0, top) == 1, "control: OM_LAYER_COUNT itself is the top height"
    assert lib.om_map_add_cover(w, 0.0, 0.0, 5.0, top + 1.0) == 0


# ---- the three read-only getters (A133): unknown-unit returns only; bodies are stubs this wave ----

UNKNOWN_UNITS = (0, 99999, 0xFFFFFFFF)


def test_A133_getters_return_0_for_an_unknown_unit_and_write_nothing(lib, w):
    ax, ay = ctypes.c_double(-777.0), ctypes.c_double(-888.0)
    for uid in UNKNOWN_UNITS:
        assert lib.om_unit_get_group_id(w, uid) == 0, uid
        assert lib.om_unit_get_engaged(w, uid) == 0, uid
        assert lib.om_unit_get_leash_anchor(w, uid, ctypes.byref(ax), ctypes.byref(ay)) == 0, uid
        assert (ax.value, ay.value) == (-777.0, -888.0), f"unit {uid}: outputs must stay untouched"
        assert lib.om_unit_get_leash_anchor(w, uid, None, None) == 0, "NULL outputs are allowed"


def test_A133_getters_return_0_for_a_null_world(lib, w):
    unit = lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    assert lib.om_unit_alive(w, unit) == 1, "control: the unit exists in w"
    ax, ay = ctypes.c_double(-777.0), ctypes.c_double(-888.0)
    assert lib.om_unit_get_group_id(None, unit) == 0
    assert lib.om_unit_get_engaged(None, unit) == 0
    assert lib.om_unit_get_leash_anchor(None, unit, ctypes.byref(ax), ctypes.byref(ay)) == 0
    assert (ax.value, ay.value) == (-777.0, -888.0)


def test_A133_getters_on_a_fresh_live_unit_report_no_group_not_engaged_no_anchor(lib, w):
    """Positive control for the unknown-unit tests: the same calls on a unit that exists, which has had no
    order. Group 0 (no group), not engaged, no anchor, outputs untouched. This is a stub-compatible check;
    A3 adds the behaviour tests (a group id after a group order, an anchor after acquisition, engaged in a fight)."""
    unit = lib.om_unit_spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    assert lib.om_unit_alive(w, unit) == 1 and unit not in UNKNOWN_UNITS, "control: a real unit id"
    ax, ay = ctypes.c_double(-777.0), ctypes.c_double(-888.0)
    assert lib.om_unit_get_group_id(w, unit) == 0
    assert lib.om_unit_get_engaged(w, unit) == 0
    assert lib.om_unit_get_leash_anchor(w, unit, ctypes.byref(ax), ctypes.byref(ay)) == 0
    assert (ax.value, ay.value) == (-777.0, -888.0)
    assert lib.om_unit_get_leash_anchor(w, unit, None, None) == 0, "NULL outputs are allowed"
