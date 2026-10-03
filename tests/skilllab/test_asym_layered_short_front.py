# spec: Architect ruling (matchup next item): layered arrangement beside interleaved, A174 draft
"""Side.arrangement "layered_short_front": types ranked by attack range ascending (ties by mix order), shortest
range nearest the enemy. asym.unit_stats is faked with per-name ranges; no engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.skilllab.asym as asym  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402

RANGES = {"Raider": 200.0, "Vanguard": 300.0, "Bombard": 500.0, "Bastion": 250.0, "Twin": 200.0}
LSF = "layered_short_front"


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    def fake(name):
        return {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0,
                "attack_range": RANGES[name], "speed": 5.0, "sensor_radius": 700.0,
                "layer_transition_time": 0.0, "aoe_radius": 0.0}
    monkeypatch.setattr(asym, "unit_stats", fake)


def _points(setup, side):
    """{unit: [(x, y)]} for one side, from the points groups."""
    out = {}
    for g in setup.groups:
        if g.side == side:
            pts = place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
            out.setdefault(g.unit, []).extend(pts)
    return out


def _build(mix, arrangement=LSF, other=None, size=16, enemy=16):
    return asym_play(size, Side("blob", mix=mix, arrangement=arrangement),
                     other or Side("blob"))(enemy, False)


def _by_nearness(setup, side):
    """Unit name per point, nearest the enemy first."""
    pts = [(x, u) for u, ps in _points(setup, side).items() for x, _ in ps]
    return [u for x, u in sorted(pts, key=lambda t: -t[0] if side == 0 else t[0])]


@pytest.mark.parametrize("side", (0, 1))
def test_short_range_type_is_nearest_the_enemy(side):
    sides = [Side("blob"), Side("blob")]
    sides[side] = Side("blob", mix=(("Raider", 1), ("Vanguard", 1)), arrangement=LSF)
    setup = asym_play(16, sides[0], sides[1])(16, False)
    order = _by_nearness(setup, side)
    assert order[:8] == ["Raider"] * 8 and order[8:] == ["Vanguard"] * 8


@pytest.mark.parametrize("side", (0, 1))
def test_mix_order_does_not_matter_ranges_decide(side):
    got = []
    for mix in ((("Raider", 1), ("Vanguard", 1)), (("Vanguard", 1), ("Raider", 1))):
        sides = [Side("blob"), Side("blob")]
        sides[side] = Side("blob", mix=mix, arrangement=LSF)
        got.append(_by_nearness(asym_play(16, *sides)(16, False), side))
    assert got[0] == got[1] and got[0][:8] == ["Raider"] * 8


def test_long_range_pair_ranks_by_range_too():
    order = _by_nearness(_build((("Bombard", 1), ("Bastion", 1))), 0)
    assert order[:8] == ["Bastion"] * 8 and order[8:] == ["Bombard"] * 8


def test_equal_ranges_tie_by_mix_order():
    for mix in ((("Raider", 1), ("Twin", 1)), (("Twin", 1), ("Raider", 1))):
        order = _by_nearness(_build(mix), 0)
        assert order[:8] == [mix[0][0]] * 8 and order[8:] == [mix[1][0]] * 8


def test_counts_are_the_largest_remainder_split():
    setup = _build((("Raider", 1), ("Vanguard", 1)), size=15, enemy=15)
    c = {u: len(p) for u, p in _points(setup, 0).items()}
    assert c == {"Raider": 8, "Vanguard": 7}      # the tie goes to the earlier name in mix order
    setup = _build((("Vanguard", 1), ("Raider", 1)), size=15, enemy=15)
    c = {u: len(p) for u, p in _points(setup, 0).items()}
    assert c == {"Vanguard": 8, "Raider": 7}
    assert sum(g.count for g in setup.groups if g.side == 0) == 15


def test_groups_are_points_groups():
    setup = _build((("Raider", 1), ("Vanguard", 1)))
    assert {g.formation for g in setup.groups if g.side == 0} == {"points"}


def test_positive_control_interleaved_is_not_ranked_by_range():
    order = _by_nearness(_build((("Raider", 1), ("Vanguard", 1)), arrangement="interleaved"), 0)
    assert set(order[:8]) == {"Raider", "Vanguard"}


def test_layered_keeps_mix_order_not_range():
    """The existing "layered" is unchanged: types ordered by mix order, so a long-range first type is in front."""
    order = _by_nearness(_build((("Vanguard", 1), ("Raider", 1)), arrangement="layered"), 0)
    assert order[:8] == ["Vanguard"] * 8


def test_pure_side_unchanged():
    a = _build((("Vanguard", 1),), arrangement=LSF)
    b = _build((("Vanguard", 1),), arrangement="interleaved")
    assert a.groups == b.groups


def test_custom_unit_type_resolves_through_base(monkeypatch):
    asked = []
    real = asym.unit_stats
    monkeypatch.setattr(asym, "unit_stats", lambda n: (asked.append(n), real(n))[1])
    types = {"Fast": {"base": "Raider"}, "Slow": {"base": "Bombard"}}
    setup = asym_play(16, Side("blob", mix=(("Slow", 1), ("Fast", 1)), arrangement=LSF), Side("blob"),
                      unit_types=types)(16, False)
    order = _by_nearness(setup, 0)
    assert order[:8] == ["Fast"] * 8 and order[8:] == ["Slow"] * 8
    assert "Fast" not in asked and "Slow" not in asked


def test_invalid_arrangement_still_raises():
    with pytest.raises(ValueError):
        asym_play(16, Side("blob", arrangement="layered_long_front"), Side("blob"))
    assert LSF in asym._ARRANGEMENTS and "layered" in asym._ARRANGEMENTS


def test_build_labels_untouched():
    a = asym_play(16, Side("blob", mix=(("Raider", 1), ("Vanguard", 1)), arrangement=LSF), Side("blob"))
    b = asym_play(16, Side("blob", mix=(("Raider", 1), ("Vanguard", 1))), Side("blob"))
    assert a.labels == b.labels
