# spec: batch runner spec addendum 3 (batch3_spec.md) - scripts/skilllab/positions.py, the three position plays
"""bait_play, ambush_play, fall_back_play: Setup rewrite and timeline Steps. unit_stats faked, no engine."""
import dataclasses
import inspect
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import formations, positions, timeline  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.contract import Step  # noqa: E402
from tests.skilllab.fakes_batches import fake_sensors  # noqa: E402


@pytest.fixture(autouse=True)
def _sensors(monkeypatch):
    fake_sensors(monkeypatch)


def _base(size, enemy=16, swap=False):
    return asym_play(size, Side("blob"), Side("blob"))(enemy, swap)


def _points(g):
    return formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def _bait_k(size, share=0.25):
    return max(1, round(size * share))


def test_defaults_are_the_documented_draft_numbers():
    assert inspect.signature(positions.bait_play).parameters["tick"].default == 100
    assert inspect.signature(positions.bait_play).parameters["share"].default == 0.25
    assert inspect.signature(positions.ambush_play).parameters["tick"].default == 100
    assert inspect.signature(positions.fall_back_play).parameters["tick"].default == 100


@pytest.mark.parametrize("name,fn", [("bait", positions.bait_play), ("ambush", positions.ambush_play),
                                     ("fall_back", positions.fall_back_play)])
def test_labels(name, fn):
    labels = fn(16).labels
    assert name in labels["play_side0"]
    assert labels["status_side0"] == "draft"
    assert labels["play_side1"] == "blob" and labels["status_side1"] == "naive"


@pytest.mark.parametrize("size", [4, 10, 16, 32])
def test_bait_group_counts_and_group_order(size):
    k = _bait_k(size)
    setup = positions.bait_play(size)(16, False)
    assert [g.side for g in setup.groups] == [0, 0, 1]            # side 0 first (bait, main body), then side 1
    bait, main, enemy = setup.groups
    assert (bait.count, main.count) == (k, size - k)
    assert bait.formation == main.formation == "points"
    assert len(bait.params["points"]) == k and len(main.params["points"]) == size - k
    assert enemy.count == 16


def test_bait_default_share_gives_four_of_sixteen():
    bait, main, _ = positions.bait_play(16)(16, False).groups
    assert (bait.count, main.count) == (4, 12)


def test_bait_takes_the_points_nearest_the_enemy_and_partitions_the_blob():
    size = 16
    orig = _base(size)
    pts = sorted(_points(orig.groups[0]))
    by_x = sorted(pts, key=lambda p: -p[0])                       # side 0 faces +x: largest x is nearest the enemy
    bait, main, _ = positions.bait_play(size)(16, False).groups
    assert sorted(bait.params["points"]) == sorted(by_x[:4])
    assert sorted(main.params["points"]) == sorted(by_x[4:])
    assert sorted(bait.params["points"] + main.params["points"]) == pts
    assert min(p[0] for p in bait.params["points"]) >= max(p[0] for p in main.params["points"])


def test_bait_group_fields_copy_the_blob_group():
    orig = _base(16).groups[0]
    bait, main, _ = positions.bait_play(16)(16, False).groups
    for g in (bait, main):
        assert (g.side, g.unit, g.layer, g.facing_deg, g.goal) == (0, orig.unit, orig.layer, orig.facing_deg, None)
        assert (g.x, g.y) == (0.0, 0.0)
    assert bait.order == "attack_move" and main.order == "idle"


def test_bait_steps_exactly():
    size = 16
    setup = positions.bait_play(size)(16, False)
    bait, main, _ = setup.groups
    cx = statistics.fmean(p[0] for p in main.params["points"])
    cy = statistics.fmean(p[1] for p in main.params["points"])
    assert len(setup.timeline) == 2
    s0, s1 = setup.timeline
    assert (s0.group, s0.when, s0.order) == (0, ("tick", 100), "move")
    assert s0.goal == pytest.approx((cx, cy))
    assert s1 == Step(1, ("tick", 100), "attack_move")            # goal None: the enemy's first anchor


def test_bait_custom_tick_and_share():
    setup = positions.bait_play(16, tick=250, share=0.5)(16, False)
    bait, main, _ = setup.groups
    assert (bait.count, main.count) == (8, 8)
    assert [s.when for s in setup.timeline] == [("tick", 250), ("tick", 250)]


def test_bait_at_least_one_unit_in_the_bait():
    bait, main, _ = positions.bait_play(2, share=0.1)(16, False).groups
    assert (bait.count, main.count) == (1, 1)


def test_bait_leaves_the_enemy_untouched():
    plain = _base(16)
    enemy = positions.bait_play(16)(16, False).groups[-1]
    assert enemy == plain.groups[-1] and enemy.order == "attack_move"


def test_ambush_idles_side_zero_and_springs_it():
    setup = positions.ambush_play(16)(16, False)
    assert [(g.side, g.count, g.order) for g in setup.groups] == [(0, 16, "idle"), (1, 16, "attack_move")]
    assert setup.timeline == (Step(0, ("tick", 100), "attack_move"),)
    assert setup.groups[0].formation == "blob"


def test_ambush_custom_tick_and_enemy_untouched():
    setup = positions.ambush_play(16, tick=40)(12, False)
    assert setup.timeline == (Step(0, ("tick", 40), "attack_move"),)
    assert setup.groups[1] == _base(16, 12).groups[1]


def test_fall_back_steps_exactly():
    setup = positions.fall_back_play(16)(16, False)
    g = setup.groups[0]
    assert [(x.side, x.order) for x in setup.groups] == [(0, "attack_move"), (1, "attack_move")]
    assert setup.timeline == (Step(0, ("tick", 100), "move", goal=(g.x, g.y)),
                              Step(0, ("tick", 200), "attack_move"))


def test_fall_back_custom_tick_doubles():
    setup = positions.fall_back_play(8, tick=30)(8, False)
    assert [s.when for s in setup.timeline] == [("tick", 30), ("tick", 60)]


@pytest.mark.parametrize("make", [positions.bait_play, positions.ambush_play, positions.fall_back_play])
@pytest.mark.parametrize("swap", [False, True])
def test_setups_pass_timeline_validate(make, swap):
    for size, enemy in ((16, 8), (16, 24), (4, 4)):
        timeline.validate(make(size)(enemy, swap))


@pytest.mark.parametrize("make", [positions.bait_play, positions.ambush_play, positions.fall_back_play])
def test_validation_errors(make):
    with pytest.raises(ValueError):
        make(0)
    with pytest.raises(ValueError):
        make(-3)
    with pytest.raises(ValueError):
        make(16, tick=0)
    with pytest.raises(ValueError):
        make(16, tick=-1)


@pytest.mark.parametrize("share", [0, 0.0, 1, 1.0, -0.1, 1.5])
def test_bait_share_outside_open_unit_interval(share):
    with pytest.raises(ValueError):
        positions.bait_play(16, share=share)


def test_bait_needs_two_units():
    with pytest.raises(ValueError):
        positions.bait_play(1)
    positions.bait_play(2)


@pytest.mark.parametrize("make", [positions.bait_play, positions.ambush_play, positions.fall_back_play])
def test_deterministic_and_swap_keeps_structure(make):
    build = make(16)
    assert build(16, False) == make(16)(16, False)
    a, b = build(16, False), build(16, True)
    assert dataclasses.replace(a, groups=()) == dataclasses.replace(b, groups=())
    assert [(g.side, g.count, g.order) for g in a.groups] == [(g.side, g.count, g.order) for g in b.groups]
