# spec: docs/northstar/research/layer_dynamics/README.md section 4 (guard cells: degenerate plays the rule set must not be fooled by)
"""guard: guard_play placements (all_siege, camp_top_layer, max_range_blob) and guard_flags.
`asym.unit_stats` is faked as in test_asym; guard must read unit stats through the asym module attribute
(asym.unit_stats) so the fake applies. No engine, no compiler. Pass marks are inputs; the tolerance below is a placeholder."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.asym as asym  # noqa: E402
from scripts.skilllab.contract import FightResult, ScanResult, Setup  # noqa: E402
from scripts.skilllab.evidence import Thresholds  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402
from scripts.skilllab.guard import GUARD_CELLS, guard_flags, guard_play  # noqa: E402

SENSORS = {"Vanguard": 700.0, "Warden": 500.0, "Bombard": 900.0, "Spire": 800.0}
DRAFT_UNCONFIRMED_GUARD_TOLERANCE_UNITS = 2   # draft, not confirmed by Westley; placeholder for the test


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    def fake(name):
        if name not in SENSORS:
            raise ValueError("unknown unit type %r" % (name,))
        return {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
                "speed": 5.0, "sensor_radius": SENSORS[name], "layer_transition_time": 0.0, "aoe_radius": 0.0}
    monkeypatch.setattr(asym, "unit_stats", fake)


def _side(setup, side):
    return [g for g in setup.groups if g.side == side]


def _pts(setup, side):
    out = []
    for g in _side(setup, side):
        out += place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
    return out


def _gap(setup):
    return min(x for x, _ in _pts(setup, 1)) - max(x for x, _ in _pts(setup, 0))


def test_guard_cells_names():
    """The three guard cells, in this order."""
    assert GUARD_CELLS == ("all_siege", "camp_top_layer", "max_range_blob")


def test_all_siege_shape():
    """Side 0 is one blob of siege units only, size strong, layer 0, attack-move; side 1 a naive blob of line units."""
    s = guard_play("all_siege", 9)(7, False)
    assert isinstance(s, Setup) and len(s.groups) == 2
    g0, g1 = s.groups
    assert (g0.side, g0.unit, g0.count, g0.formation, g0.layer, g0.order, g0.facing_deg) == (
        0, "Bombard", 9, "blob", 0, "attack_move", 0.0)
    assert (g1.side, g1.unit, g1.count, g1.formation, g1.layer, g1.order, g1.facing_deg) == (
        1, "Vanguard", 7, "blob", 0, "attack_move", 180.0)


def test_all_siege_custom_names():
    """siege= and line= choose the unit types."""
    g0, g1 = guard_play("all_siege", 4, siege="Spire", line="Warden")(4, False).groups
    assert (g0.unit, g1.unit) == ("Spire", "Warden")


def test_camp_top_layer_shape():
    """Side 0 camps: a blob of line units on the top layer with order idle; the enemy attack-moves on layer 0."""
    g0, g1 = guard_play("camp_top_layer", 6)(8, False).groups
    assert (g0.side, g0.unit, g0.count, g0.formation, g0.layer, g0.order) == (0, "Vanguard", 6, "blob", 4, "idle")
    assert (g1.side, g1.unit, g1.count, g1.formation, g1.layer, g1.order) == (1, "Vanguard", 8, "blob", 0, "attack_move")


def test_camp_top_layer_layer_argument_and_negative_control():
    """top_layer sets the camp layer; the other guards never leave layer 0 or idle."""
    assert guard_play("camp_top_layer", 5, top_layer=2)(5, False).groups[0].layer == 2
    for name in ("all_siege", "max_range_blob"):
        g0 = guard_play(name, 5, ranges={"Vanguard": 1.0, "Bombard": 2.0})(5, False).groups[0]
        assert (g0.layer, g0.order) == (0, "attack_move")


def test_max_range_blob_picks_longest_range():
    """Side 0 is a blob of the unit with the longest attack_range among the names in ranges."""
    ranges = {"Vanguard": 100.0, "Bombard": 300.0, "Warden": 200.0}
    g0, g1 = guard_play("max_range_blob", 5, ranges=ranges)(6, False).groups
    assert (g0.unit, g0.count, g0.formation, g0.order, g0.layer) == ("Bombard", 5, "blob", "attack_move", 0)
    assert g1.unit == "Vanguard"
    ranges["Warden"] = 400.0
    assert guard_play("max_range_blob", 5, ranges=ranges)(6, False).groups[0].unit == "Warden"


@pytest.mark.parametrize("name,kw,sensors", [
    ("all_siege", {}, ("Bombard", "Vanguard")),
    ("camp_top_layer", {}, ("Vanguard",)),
    ("max_range_blob", {"ranges": {"Vanguard": 1.0, "Spire": 9.0}}, ("Spire", "Vanguard")),
])
def test_contact_gap_is_max_sensor_plus_one(name, kw, sensors):
    """Nearest fronts sit at the largest sensor radius among the units in play, plus 1."""
    s = guard_play(name, 10, **kw)(12, False)
    assert _gap(s) == pytest.approx(max(SENSORS[n] for n in sensors) + 1, abs=1e-6)


@pytest.mark.parametrize("name", GUARD_CELLS)
def test_counts_exact_and_swap_ignored(name):
    """Unit counts equal the headcounts; build(n, True) equals build(n, False); two calls are identical."""
    kw = {"ranges": {"Vanguard": 1.0, "Bombard": 2.0}} if name == "max_range_blob" else {}
    b = guard_play(name, 11, **kw)
    s = b(7, False)
    assert sum(g.count for g in _side(s, 0)) == 11 and sum(g.count for g in _side(s, 1)) == 7
    assert len(_pts(s, 0)) == 11 and len(_pts(s, 1)) == 7
    assert b(7, True) == s and guard_play(name, 11, **kw)(7, False) == s


def test_different_names_give_different_setups():
    """Negative control: the three guards are not the same play."""
    ranges = {"Vanguard": 1.0, "Bombard": 2.0, "Warden": 3.0}   # longest range must differ from the default siege unit
    setups = [guard_play(n, 6, ranges=ranges)(6, False) for n in GUARD_CELLS]
    first = [x.groups[0] for x in setups]
    assert first[0] != first[1] and first[1] != first[2] and first[0] != first[2]


def test_unknown_name_is_value_error():
    """An unknown guard name raises ValueError at construction or first build."""
    with pytest.raises(ValueError):
        guard_play("nonsense", 5)(5, False)


@pytest.mark.parametrize("size,heads", [(0, 5), (-1, 5), (5, 0), (5, -2)])
@pytest.mark.parametrize("name", GUARD_CELLS)
def test_size_and_enemy_heads_must_be_positive(name, size, heads):
    """size < 1 or enemy_heads < 1 raises ValueError (at construction or build)."""
    kw = {"ranges": {"Vanguard": 1.0, "Bombard": 2.0}} if name == "max_range_blob" else {}
    with pytest.raises(ValueError):
        guard_play(name, size, **kw)(heads, False)


# ---------- guard_flags ----------

def _t(tol=DRAFT_UNCONFIRMED_GUARD_TOLERANCE_UNITS):
    return Thresholds(c0_tolerance_units=0, c1_min_firing_advantage=0.0, c1_map_share=0.0, c2_rank_agreement=0.0,
                      c2_off_trend_margin=0.0, c2_off_trend_share=0.0, c3_stack_gain=0.0, c4_max_share=0.0,
                      c5_min_loss=0.0, c6_return_share=0.0, c6_map_share=0.0, c8_map_share=0.0,
                      c7_ceiling_targets=(0.0, 0.0), c9_length_bounds_ticks=(0, 0), guard_tolerance_units=tol)


def _scan(beats):
    return ScanResult(size=10, cells=[], beats=beats, loses_to=None if beats is None else beats + 1)


def test_guard_flag_positive_control():
    """A guard beating 20 against a mirror of 15 with tolerance 2 flags (holds False, value 5)."""
    (v,) = guard_flags(_scan(15), {"all_siege": _scan(20)}, _t())
    assert v.holds is False and v.value == 5 and v.detail.startswith("unconfirmed definition:")


def test_guard_flag_negative_control():
    """Beating 16 against 15 stays inside tolerance 2: not flagged."""
    (v,) = guard_flags(_scan(15), {"all_siege": _scan(16)}, _t())
    assert v.holds is True and v.value == 1


def test_guard_flag_tolerance_boundary():
    """A difference equal to the tolerance does not flag; one more does."""
    assert guard_flags(_scan(15), {"g": _scan(17)}, _t(2))[0].holds is True
    assert guard_flags(_scan(15), {"g": _scan(18)}, _t(2))[0].holds is False


def test_guard_flag_tolerance_is_read_from_input():
    """The same scans flag at tolerance 0 and pass at tolerance 10."""
    assert guard_flags(_scan(15), {"g": _scan(20)}, _t(0))[0].holds is False
    assert guard_flags(_scan(15), {"g": _scan(20)}, _t(10))[0].holds is True


def test_guard_flag_worse_than_mirror_is_fine():
    """A guard that breaks even below the mirror is not fooling anything."""
    (v,) = guard_flags(_scan(15), {"g": _scan(9)}, _t())
    assert v.holds is True and v.value == -6


def test_guard_flag_missing_beats_is_not_judged():
    """Either side missing beats gives holds None, value None."""
    for mirror, guard in ((15, None), (None, 20), (None, None)):
        (v,) = guard_flags(_scan(mirror), {"g": _scan(guard)}, _t())
        assert v.holds is None and v.value is None and v.detail.startswith("unconfirmed definition:")


def test_guard_flags_one_per_scan_in_given_order():
    """One Verdict per guard scan, in the dict's insertion order; none for none."""
    scans = {"camp_top_layer": _scan(15), "all_siege": _scan(30), "max_range_blob": _scan(16)}
    out = guard_flags(_scan(15), scans, _t())
    assert [v.holds for v in out] == [True, False, True]
    assert guard_flags(_scan(15), {}, _t()) == []
