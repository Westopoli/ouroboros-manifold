# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-12 (asymmetric plays, item 1 of Phase S)
"""asym: group shapes per role, largest-remainder mixes, interleaved/layered assignment, counter geometry,
contact placement from the max sensor radius, validation, two_sizes, determinism and engine independence.
`asym.unit_stats` is faked (700 Vanguard, 500 Warden, 333.5 Raider); no Engine, no compiler."""
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.asym as asym  # noqa: E402
from scripts.skilllab.asym import Side, asym_play, two_sizes  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402
from scripts.skilllab.plays import blob_play  # noqa: E402

SENSORS = {"Vanguard": 700.0, "Warden": 500.0, "Raider": 333.5}
ROLES = ("blob", "line", "skilled", "counter")
FORMATION = {"blob": "blob", "line": "line", "skilled": "concave", "counter": "column"}


def _approx(x):
    return pytest.approx(x, abs=1e-6, rel=0)


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    """Replace asym.unit_stats with a fake sensor table; records the names asked. Unknown names raise ValueError."""
    asked = []

    def fake(name):
        asked.append(name)
        if name not in SENSORS:
            raise ValueError("unknown unit type %r" % (name,))
        return {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
                "speed": 5.0, "sensor_radius": SENSORS[name], "layer_transition_time": 0.0, "aoe_radius": 0.0}

    monkeypatch.setattr(asym, "unit_stats", fake)
    return asked


def _groups(setup, side):
    return [g for g in setup.groups if g.side == side]


def _points(setup, side):
    """All unit points of a side as place() returns them, in group order."""
    out = []
    for g in _groups(setup, side):
        out += place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
    return out


def _gap(setup):
    """Distance along x between side 0's front-most unit and side 1's front-most unit."""
    return min(x for x, _ in _points(setup, 1)) - max(x for x, _ in _points(setup, 0))


def _centred(pts):
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    return sorted((round(x - cx, 4), round(y - cy, 4)) for x, y in pts)


def _mean_x(group):
    pts = group.params["points"]
    return sum(x for x, _ in pts) / len(pts)


def test_role_group_shapes_single_type():
    """Each role is one Group with its own formation, params, facing, layer, order; goal None except skilled and counter (the skilled goal is pinned in test_asym_concave_goal.py)."""
    expect = {
        "blob": {"radius": 80 + 12 * math.sqrt(16)},
        "line": {"spacing": 30},
        "skilled": {"arc_deg": 120, "radius": 150 + 12 * math.sqrt(16)},
        "counter": {"spacing": 30, "cols": 3},
    }
    for role in ("blob", "line", "skilled"):
        s = asym_play(16, Side(role), Side("blob"))(16, False)
        g0, g1 = s.groups
        assert isinstance(s, Setup) and len(s.groups) == 2
        assert (g0.side, g0.unit, g0.count, g0.formation, g0.facing_deg, g0.layer, g0.order, g0.y) == (
            0, "Vanguard", 16, FORMATION[role], 0.0, 0, "attack_move", 0.0)
        assert (g0.goal is None) == (role != "skilled")
        assert g0.params == pytest.approx(expect[role])
        assert (g1.side, g1.facing_deg, g1.formation, g1.y) == (1, 180.0, "blob", 0.0)
    c0, _ = asym_play(16, Side("counter"), Side("line"))(16, False).groups
    assert (c0.side, c0.count, c0.formation, c0.facing_deg, c0.layer, c0.order) == (0, 16, "column", 0.0, 0, "attack_move")
    assert c0.params == {"spacing": 30, "cols": 3}


@pytest.mark.parametrize("role", ROLES[:3])
def test_role_formation_differs_from_other_roles(role):
    """Negative control: the formation name tells roles apart."""
    other = [r for r in ROLES[:3] if r != role]
    g = asym_play(9, Side(role), Side("blob"))(9, False).groups[0]
    for o in other:
        assert g.formation != asym_play(9, Side(o), Side("blob"))(9, False).groups[0].formation


@pytest.mark.parametrize("role0", ROLES)
@pytest.mark.parametrize("role1", ROLES)
@pytest.mark.parametrize("sizes", [(16, 9), (5, 24), (1, 1)])
def test_single_type_counts_exact(role0, role1, sizes):
    """Per-side counts equal the headcounts exactly, for every role pair (counter-counter included)."""
    if role0 == role1 == "counter":
        return   # counter vs counter is unspecified
    s = asym_play(sizes[0], Side(role0), Side(role1))(sizes[1], False)
    assert sum(g.count for g in _groups(s, 0)) == sizes[0]
    assert sum(g.count for g in _groups(s, 1)) == sizes[1]
    assert len(_points(s, 0)) == sizes[0] and len(_points(s, 1)) == sizes[1]


def test_group_order_is_side0_groups_then_side1_groups_in_mix_order():
    """Setup.groups lists side 0's groups in mix order, then side 1's."""
    s = asym_play(8, Side("blob", mix=(("Vanguard", 1), ("Warden", 1))),
                  Side("line", mix=(("Raider", 1), ("Vanguard", 1))))(8, False)
    assert [(g.side, g.unit) for g in s.groups] == [(0, "Vanguard"), (0, "Warden"), (1, "Raider"), (1, "Vanguard")]


@pytest.mark.parametrize("size,weights,counts", [
    (16, (1, 1), (8, 8)), (16, (3, 1), (12, 4)), (16, (2, 1, 1), (8, 4, 4)),
    (5, (1, 1), (3, 2)), (7, (1, 1, 1), (3, 2, 2)), (7, (2, 1), (5, 2)), (10, (3, 2), (6, 4)),
])
@pytest.mark.parametrize("arrangement", ["interleaved", "layered"])
def test_mixed_split_largest_remainder(size, weights, counts, arrangement):
    """Largest remainder, ties to the earlier name; one points Group per name; counts sum to size; points match counts."""
    names = ("Vanguard", "Warden", "Raider")[:len(weights)]
    mix = tuple(zip(names, weights))
    s = asym_play(size, Side("line", mix=mix, arrangement=arrangement), Side("blob"))(8, False)
    gs = _groups(s, 0)
    assert [g.unit for g in gs] == list(names) and [g.count for g in gs] == list(counts)
    assert sum(g.count for g in gs) == size
    for g in gs:
        assert g.formation == "points" and set(g.params) == {"points"} and len(g.params["points"]) == g.count
        assert (g.side, g.facing_deg, g.layer, g.order, g.goal) == (0, 0.0, 0, "attack_move", None)
    assert len(_groups(s, 1)) == 1 and _groups(s, 1)[0].formation == "blob"


@pytest.mark.parametrize("role", ["blob", "line", "skilled"])
def test_mixed_points_are_the_roles_formation(role):
    """The union of the mix's points is the role's formation for all units (equal up to translation); no point is shared."""
    mix = (("Vanguard", 3), ("Warden", 1))
    s = asym_play(12, Side(role, mix=mix), Side("blob"))(8, False)
    union = _points(s, 0)
    params = {"blob": {"radius": 80 + 12 * math.sqrt(12)}, "line": {"spacing": 30},
              "skilled": {"arc_deg": 120, "radius": 150 + 12 * math.sqrt(12)}}[role]
    ref = place(FORMATION[role], 12, 0.0, 0.0, 0.0, params)
    assert _centred(union) == _centred(ref)
    assert len(set(union)) == 12


def test_zero_share_name_gets_no_group():
    """2 units with weights 10:1 gives the second name 0 units: no error, no Group for it, counts still sum."""
    s = asym_play(2, Side("line", mix=(("Vanguard", 10), ("Warden", 1))), Side("blob"))(4, False)
    gs = _groups(s, 0)
    assert "Warden" not in [g.unit for g in gs]
    assert sum(g.count for g in gs) == 2 and all(g.count >= 1 for g in gs)
    assert len(_points(s, 0)) == 2


def test_single_name_mix_matches_plays_groups_where_roles_coincide():
    """One name: one Group with the role's formation (not points); blob vs blob equals blob_play on every Group field but placement."""
    a = asym_play(16, Side("blob"), Side("blob"))(16, False)
    b = blob_play(16)(16, False)
    assert len(a.groups) == len(b.groups) == 2
    for ga, gb in zip(a.groups, b.groups):
        assert (ga.side, ga.unit, ga.count, ga.formation, ga.facing_deg, ga.layer, ga.order, ga.goal, ga.params) == (
            gb.side, gb.unit, gb.count, gb.formation, gb.facing_deg, gb.layer, gb.order, gb.goal, gb.params)
        assert ga.formation != "points"
    assert (a.abilities, a.max_ticks, a.sample_every, a.point) == (b.abilities, b.max_ticks, b.sample_every, b.point)


def test_layered_puts_first_unit_nearer_the_enemy():
    """Layered: the first mix entry's mean x is nearer the enemy than the second's (side 0 faces +x, side 1 faces -x);
    reference arithmetic for a 16-unit blob of two types 1:1 gives a mean gap of about 100 wu, so > 50."""
    mix = (("Vanguard", 1), ("Warden", 1))
    s = asym_play(16, Side("blob", mix=mix, arrangement="layered"), Side("blob", mix=mix, arrangement="layered"))(16, False)
    a0, b0, a1, b1 = s.groups
    assert _mean_x(a0) - _mean_x(b0) > 50
    assert _mean_x(b1) - _mean_x(a1) > 50


def test_layered_three_types_are_ordered_by_distance():
    """Layered 2:1:1: mean x strictly decreases from the first to the last mix entry for side 0."""
    mix = (("Vanguard", 2), ("Warden", 1), ("Raider", 1))
    s = asym_play(16, Side("blob", mix=mix, arrangement="layered"), Side("blob"))(16, False)
    xs = [_mean_x(g) for g in _groups(s, 0)]
    assert xs[0] > xs[1] > xs[2]


def test_interleaved_spreads_types_and_differs_from_layered():
    """Interleaved 16-unit 1:1 blob: the two types' mean x differ by under 20 wu (reference arithmetic with alternating
    hand-out gives about 11); layered gives over 50. Negative control: the layered Setup differs from the interleaved one."""
    mix = (("Vanguard", 1), ("Warden", 1))
    inter = asym_play(16, Side("blob", mix=mix), Side("blob"))(16, False)
    lay = asym_play(16, Side("blob", mix=mix, arrangement="layered"), Side("blob"))(16, False)
    ia, ib = _groups(inter, 0)
    la, lb = _groups(lay, 0)
    assert abs(_mean_x(ia) - _mean_x(ib)) < 20
    assert abs(_mean_x(la) - _mean_x(lb)) > 50
    assert inter != lay
    default = asym_play(16, Side("blob", mix=mix, arrangement="interleaved"), Side("blob"))(16, False)
    assert default == inter


def test_interleaved_line_types_alternate_along_the_line():
    """Interleaved 16-unit 1:1 line: each type's mean y is within one spacing (30) of the other's.
    Negative control: assigning the first 8 points to one type would differ by 240, which this bound rejects."""
    mix = (("Vanguard", 1), ("Warden", 1))
    s = asym_play(16, Side("line", mix=mix), Side("blob"))(16, False)
    a, b = _groups(s, 0)
    ma = sum(y for _, y in a.params["points"]) / 8
    mb = sum(y for _, y in b.params["points"]) / 8
    assert abs(ma - mb) <= 30 + 1e-6
    pts = place("line", 16, 0.0, 0.0, 0.0, {"spacing": 30})
    block = abs(sum(y for _, y in pts[:8]) / 8 - sum(y for _, y in pts[8:]) / 8)
    assert block == _approx(240.0) and block > 30 + 1e-6


def _enemy_extent(setup, side):
    pts = _points(setup, side)
    ys = [y for _, y in pts]
    return (max(ys) - min(ys)) / 2.0, max(pts, key=lambda p: p[1])


@pytest.mark.parametrize("enemy,heads", [("line", 16), ("line", 5), ("blob", 9), ("skilled", 12)])
def test_counter_geometry_side0(enemy, heads):
    """Counter: one column group at y = the enemy's half y-extent (positive), goal = the enemy's max-y point, every
    point strictly y > 0, spacing 30, 3 cols. Negative control: the goal is not the enemy centre."""
    s = asym_play(16, Side("counter"), Side(enemy))(heads, False)
    (c,) = _groups(s, 0)
    half, end = _enemy_extent(s, 1)
    assert c.formation == "column" and c.params == {"spacing": 30, "cols": 3} and c.count == 16
    assert c.y == _approx(half) and half > 0
    assert c.goal == (_approx(end[0]), _approx(end[1]))
    assert c.goal[1] == _approx(half)
    centre = (sum(x for x, _ in _points(s, 1)) / heads, sum(y for _, y in _points(s, 1)) / heads)
    assert abs(c.goal[1] - centre[1]) > 1.0
    assert all(y > 0 for _, y in _points(s, 0))
    assert c.facing_deg == 0.0 and c.order == "attack_move"
    assert (_groups(s, 1)[0].goal is None) == (enemy != "skilled")


def test_counter_geometry_side1_mirrors_side0():
    """Side 1 as counter also sits on the positive-y end of side 0's formation, facing 180, goal = side 0's max-y point."""
    s = asym_play(10, Side("line"), Side("counter"))(12, False)
    (c,) = _groups(s, 1)
    half, end = _enemy_extent(s, 0)
    assert half == _approx(135.0)
    assert c.y == _approx(half) and c.facing_deg == 180.0
    assert c.goal == (_approx(end[0]), _approx(end[1]))
    assert all(y > 0 for _, y in _points(s, 1))


def test_counter_vs_line_example_numbers():
    """Hand arithmetic: an enemy line of 16 at spacing 30 spans y = +-225, so the column sits at y 225 with goal y 225."""
    s = asym_play(16, Side("counter"), Side("line"))(16, False)
    (c,) = _groups(s, 0)
    assert c.y == _approx(225.0) and c.goal[1] == _approx(225.0)
    assert min(y for _, y in _points(s, 0)) == _approx(195.0)


@pytest.mark.parametrize("role0", ROLES)
@pytest.mark.parametrize("role1", ROLES)
def test_contact_gap_exact_per_role_pair(role0, role1):
    """Nearest fronts are exactly max sensor (700 Vanguard) + 1 apart on x, centred on x = 0; counter-counter is unspecified."""
    if role0 == role1 == "counter":
        return
    for size, heads in ((16, 9), (4, 4)):
        s = asym_play(size, Side(role0), Side(role1))(heads, False)
        assert _gap(s) == _approx(701.0)
        f0 = max(x for x, _ in _points(s, 0))
        f1 = min(x for x, _ in _points(s, 1))
        assert (f0 + f1) / 2 == _approx(0.0)


def test_contact_gap_uses_max_sensor_over_both_mixes(_fake_stats):
    """Mixed pair with different sensors: the gap is the largest sensor over every name in both mixes, plus 1."""
    s = asym_play(8, Side("blob", mix=(("Warden", 1), ("Raider", 1))), Side("line", mix=(("Raider", 1),)))(8, False)
    assert _gap(s) == _approx(501.0)
    s = asym_play(8, Side("blob", mix=(("Raider", 1),)), Side("line", mix=(("Raider", 1), ("Vanguard", 1))))(8, False)
    assert _gap(s) == _approx(701.0)
    s = asym_play(8, Side("blob", mix=(("Raider", 1),)), Side("line", mix=(("Raider", 1),)))(8, False)
    assert _gap(s) == _approx(334.5)
    assert {"Warden", "Raider", "Vanguard"} <= set(_fake_stats)


def test_contact_gap_derived_type_uses_base_stats(_fake_stats):
    """A name found in unit_types with a base takes the base name's sensor; the derived name is never looked up."""
    types = {"VanguardLong": {"base": "Vanguard", "scale": {"attack_range": 1.2}, "set": {}}}
    s = asym_play(8, Side("blob", mix=(("VanguardLong", 1),)), Side("blob", mix=(("Raider", 1),)), unit_types=types)(8, False)
    assert _gap(s) == _approx(701.0)
    assert "VanguardLong" not in _fake_stats and "Vanguard" in _fake_stats


def test_contact_gap_uses_actual_points_not_a_formula():
    """Front extent is read from place(): a concave's arc ends reach further forward than its anchor, so the anchor-to-anchor
    distance is not the gap. Negative control: anchors differ from the point-based gap."""
    s = asym_play(16, Side("skilled"), Side("skilled"))(16, False)
    g0, g1 = s.groups
    assert _gap(s) == _approx(701.0)
    assert g1.x - g0.x != _approx(701.0)


def test_unit_types_copied_and_swap_ignored():
    """unit_types is a copy of the argument; swap does not change the Setup; other Setup fields stay at contract defaults."""
    types = {"VanguardLong": {"base": "Vanguard", "scale": {"attack_range": 1.2}, "set": {}}}
    s = asym_play(6, Side("blob", mix=(("VanguardLong", 1),)), Side("line"), unit_types=types)(6, False)
    assert s.unit_types == types and s.unit_types is not types
    s.unit_types["extra"] = {}
    assert "extra" not in types
    d = Setup(groups=(), unit_types={})
    assert (s.abilities, s.max_ticks, s.sample_every, s.trace, s.settings) == (
        d.abilities, d.max_ticks, d.sample_every, d.trace, d.settings)
    play = asym_play(6, Side("blob"), Side("line"))
    assert play(6, True) == play(6, False)
    assert asym_play(6, Side("blob"), Side("line"))(6, False).unit_types == {}


def test_determinism_two_builds_equal():
    """Same arguments, equal Setups; and a different size gives a different Setup (positive control)."""
    mix = (("Vanguard", 2), ("Warden", 1))
    a = asym_play(10, Side("skilled", mix=mix, arrangement="layered"), Side("counter"))(7, False)
    b = asym_play(10, Side("skilled", mix=mix, arrangement="layered"), Side("counter"))(7, False)
    assert a == b
    assert a != asym_play(11, Side("skilled", mix=mix, arrangement="layered"), Side("counter"))(7, False)


def test_side_defaults():
    """Side defaults: one Vanguard, interleaved; Side is frozen."""
    s = Side("blob")
    assert (s.role, s.mix, s.arrangement) == ("blob", (("Vanguard", 1),), "interleaved")
    with pytest.raises(Exception):
        s.role = "line"


@pytest.mark.parametrize("call", [
    lambda: asym_play(8, Side("wizard"), Side("blob"))(8, False),
    lambda: asym_play(8, Side("blob"), Side("wizard"))(8, False),
    lambda: asym_play(8, Side("blob", arrangement="stacked"), Side("blob"))(8, False),
    lambda: asym_play(8, Side("blob"), Side("blob", arrangement="stacked"))(8, False),
    lambda: asym_play(0, Side("blob"), Side("blob"))(8, False),
    lambda: asym_play(-3, Side("blob"), Side("blob"))(8, False),
    lambda: asym_play(8, Side("blob"), Side("blob"))(0, False),
    lambda: asym_play(8, Side("blob", mix=()), Side("blob"))(8, False),
    lambda: asym_play(8, Side("blob"), Side("blob", mix=()))(8, False),
    lambda: asym_play(8, Side("blob", mix=(("Vanguard", 0),)), Side("blob"))(8, False),
    lambda: asym_play(8, Side("blob", mix=(("Vanguard", 1), ("Warden", -1))), Side("blob"))(8, False),
])
def test_validation_raises_value_error(call):
    """Unknown role, unknown arrangement, size or enemy_heads < 1, empty mix, non-positive weight: ValueError (at asym_play or at build)."""
    with pytest.raises(ValueError):
        call()


def test_validation_positive_control_valid_call_does_not_raise():
    """Positive control for the validation table: the same shape with valid inputs builds."""
    assert asym_play(1, Side("blob"), Side("blob"))(1, False).groups


def test_two_sizes_returns_one_play_per_size():
    """two_sizes gives {size: build}; each build uses that size as side 0's headcount."""
    d = two_sizes((8, 16), Side("blob"), Side("line"))
    assert list(d) == [8, 16]
    assert sum(g.count for g in _groups(d[8](5, False), 0)) == 8
    assert sum(g.count for g in _groups(d[16](5, False), 0)) == 16
    assert d[8](5, False) == asym_play(8, Side("blob"), Side("line"))(5, False)
    assert list(two_sizes([24, 4], Side("blob"), Side("line"))) == [24, 4]


@pytest.mark.parametrize("sizes", [(8,), (), (8, 8), (4, 8, 16), (0, 16), (-4, 16)])
def test_two_sizes_rejects_anything_but_two_distinct_positive_sizes(sizes):
    """ValueError unless exactly two distinct positive sizes."""
    with pytest.raises(ValueError):
        two_sizes(sizes, Side("blob"), Side("line"))


def test_two_sizes_passes_unit_types_through():
    """unit_types reach every play."""
    types = {"VanguardLong": {"base": "Vanguard", "scale": {"attack_range": 1.2}, "set": {}}}
    d = two_sizes((4, 8), Side("blob", mix=(("VanguardLong", 1),)), Side("blob"), unit_types=types)
    assert all(b(4, False).unit_types == types for b in d.values())


def test_importing_asym_does_not_load_the_engine():
    """A fresh interpreter importing asym has not imported the engine module (no compile)."""
    code = ("import sys; sys.path.insert(0, %r); import scripts.skilllab.asym; "
            "assert 'scripts.skilllab.engine' not in sys.modules;" % str(ROOT))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr



# ---------------------------------------------------------------- LAB-REV2-L2 (Q-LAB-03, rulings 2 and 6)

@pytest.mark.parametrize("a,b", [("blob", "blob"), ("line", "line"), ("blob", "line"), ("line", "blob")])
@pytest.mark.parametrize("heads", [8, 16, 48])
def test_ruling_6_a_naive_meeting_has_one_point_between_the_fronts(a, b, heads):
    """Ruling 6: both sides attack-move to one point; for blob and line sides it is the point midway between the fronts, which
    asym_play places `gap` apart about x = 0. Each group's goal stays None."""
    s = asym_play(16, Side(a), Side(b))(heads, False)
    assert s.point == pytest.approx((0.0, 0.0), abs=1e-6)
    assert all(g.goal is None for g in s.groups)
    assert s.orders_per_unit is False      # LAB-REV2 flip ruler (TD-LAB-REV2-flip, decision 40): the group order is the default


@pytest.mark.parametrize("kw", ["approach", "mopup"])
def test_q_lab_03_asym_play_no_longer_takes_approach_or_mopup(kw):
    with pytest.raises(TypeError):
        asym_play(6, Side("blob"), Side("line"), **{kw: True})
    assert asym_play(6, Side("blob"), Side("line"))(6, False).groups


@pytest.mark.parametrize("name", ["APPROACH", "APPROACH_STOP", "MOPUP", "MOPUP_INTERVAL_TICKS"])
def test_q_lab_03_asym_module_does_not_re_export_the_retired_constants(name):
    assert not hasattr(asym, name)


def test_ruling_2_both_sides_of_a_mix_play_use_the_same_unit_names_and_no_stat_variants():
    """Ruling 2: same units, same values, both sides. With one mix for both sides and no unit_types, no stat variant exists."""
    mix = (("Vanguard", 1), ("Warden", 1))
    s = asym_play(8, Side("blob", mix=mix), Side("blob", mix=mix))(8, False)
    assert s.unit_types == {}
    assert {g.unit for g in s.groups if g.side == 0} == {g.unit for g in s.groups if g.side == 1}
