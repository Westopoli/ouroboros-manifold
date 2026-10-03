# spec: Architect ruling A187 follow-up - the concave's focus lands on the goal (scripts/skilllab/asym.py)
"""Skilled sides get goal = centroid + (T - arc centre), so the engine's slot = pos + delta puts the arc focus on T.
Other roles keep their goals. `asym.unit_stats` is faked; no Engine."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.skilllab.asym as asym  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402

SENSORS = {"Vanguard": 700.0, "Warden": 500.0, "Raider": 333.5}
EPS = 1e-6


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    def fake(name):
        return {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
                "speed": 5.0, "sensor_radius": SENSORS[name], "layer_transition_time": 0.0, "aoe_radius": 0.0}
    monkeypatch.setattr(asym, "unit_stats", fake)


def _pts(g):
    return place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def _groups(setup, side):
    return [g for g in setup.groups if g.side == side]


def _centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _radius(n):
    return 150 + 12 * math.sqrt(n)


def _centre(g, radius):
    f = math.radians(g.facing_deg)
    return (g.x + radius * math.cos(f), g.y + radius * math.sin(f))


def _close(a, b):
    return abs(a[0] - b[0]) <= EPS and abs(a[1] - b[1]) <= EPS


@pytest.mark.parametrize("swap", [False, True])
@pytest.mark.parametrize("n", [16, 24])
def test_single_type_goal_lands_focus_on_enemy_anchor(n, swap):
    setup = asym_play(n, Side("skilled"), Side("blob"))(n, swap)
    (g,) = _groups(setup, 0)
    (e,) = _groups(setup, 1)
    t = (e.x, e.y)
    c = _centre(g, _radius(n))
    cen = _centroid(_pts(g))
    assert g.goal is not None
    assert _close(g.goal, (cen[0] + t[0] - c[0], cen[1] + t[1] - c[1]))


def test_skilled_vs_line():
    setup = asym_play(16, Side("skilled"), Side("line"))(16, False)
    (g,) = _groups(setup, 0)
    (e,) = _groups(setup, 1)
    c = _centre(g, _radius(16))
    cen = _centroid(_pts(g))
    assert _close(g.goal, (cen[0] + e.x - c[0], cen[1] + e.y - c[1]))
    assert e.goal is None


def test_skilled_vs_skilled_both_get_goals_toward_other_anchor():
    setup = asym_play(16, Side("skilled"), Side("skilled"))(16, False)
    for me, other in ((0, 1), (1, 0)):
        (g,) = _groups(setup, me)
        (e,) = _groups(setup, other)
        c = _centre(g, _radius(16))
        cen = _centroid(_pts(g))
        assert g.goal is not None
        assert _close(g.goal, (cen[0] + e.x - c[0], cen[1] + e.y - c[1]))


def test_focus_is_target():
    focus = (123.0, -456.0)
    setup = asym_play(16, Side("skilled", focus=focus), Side("blob"))(16, False)
    (g,) = _groups(setup, 0)
    radius = math.hypot(focus[0] - 0.0, focus[1] - 0.0)
    c = _centre(g, radius)
    cen = _centroid(_pts(g))
    assert _close(g.goal, (cen[0] + focus[0] - c[0], cen[1] + focus[1] - c[1]))


def test_mixed_skilled_side_all_groups_share_delta():
    mixed = asym_play(16, Side("skilled", mix=(("Vanguard", 1), ("Raider", 1))), Side("blob"))(16, False)
    single = asym_play(16, Side("skilled"), Side("blob"))(16, False)
    (sg,) = _groups(single, 0)
    (e,) = _groups(mixed, 1)
    c = _centre(sg, _radius(16))          # same geometry and shift as the mixed side's points
    delta = (e.x - c[0], e.y - c[1])
    gs = _groups(mixed, 0)
    assert len(gs) == 2
    for g in gs:
        cen = _centroid(_pts(g))
        assert g.goal is not None
        assert _close(g.goal, (cen[0] + delta[0], cen[1] + delta[1]))


def test_blob_and_line_goals_stay_none():
    for role in ("blob", "line"):
        setup = asym_play(16, Side(role), Side("skilled"))(16, False)
        assert all(g.goal is None for g in _groups(setup, 0))
    setup = asym_play(16, Side("skilled"), Side("line"))(16, False)
    assert all(g.goal is None for g in _groups(setup, 1))


def test_counter_goal_unchanged():
    setup = asym_play(16, Side("counter"), Side("blob"))(16, False)
    enemy = [p for g in _groups(setup, 1) for p in _pts(g)]
    want = max(enemy, key=lambda p: p[1])
    gs = _groups(setup, 0)
    assert gs and all(_close(g.goal, want) for g in gs)


def test_slots_arc_centre_sits_on_target_and_old_goal_misses_it():
    setup = asym_play(16, Side("skilled"), Side("blob"))(16, False)
    (g,) = _groups(setup, 0)
    (e,) = _groups(setup, 1)
    t = (e.x, e.y)
    pts = _pts(g)
    cen = _centroid(pts)
    slots = [(p[0] + g.goal[0] - cen[0], p[1] + g.goal[1] - cen[1]) for p in pts]
    for s in slots:
        assert abs(math.hypot(s[0] - t[0], s[1] - t[1]) - _radius(16)) <= EPS
    # positive control: goal None means the default goal T, so slots = T + (pos - centroid)
    c = _centre(g, _radius(16))
    old_centre = (t[0] + c[0] - cen[0], t[1] + c[1] - cen[1])
    assert math.hypot(old_centre[0] - t[0], old_centre[1] - t[1]) > 50
