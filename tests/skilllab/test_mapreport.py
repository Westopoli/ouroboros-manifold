# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S, each map's naive-against-naive break-even beside every result
"""mapreport.naive_break_even / map_labels with a recording fake fight_fn. No Engine, no compiler."""
import dataclasses
import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.asym as asym_mod  # noqa: E402
import scripts.skilllab.plays as plays_mod  # noqa: E402
from scripts.skilllab import rows  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.breakeven import BreakEven, find_break_even  # noqa: E402
from scripts.skilllab.contract import Block, Cover, FightResult, ScanResult, Terrain  # noqa: E402
from scripts.skilllab.mapreport import MapReport, map_labels, naive_break_even  # noqa: E402
from scripts.skilllab.maps import sample_map  # noqa: E402
from scripts.skilllab.terrain import shift_terrain, with_terrain  # noqa: E402

CANVAS = (4000.0, 3000.0)
T = Terrain(canvas=CANVAS, blocks=(Block(-10.0, -200.0, 10.0, 200.0, 0, 2),), covers=(Cover(0.0, 300.0, 40.0, 1),))
SIZE = 4
KW = dict(replicates=2, near_replicates=4, max_rounds=2)
CUT = 5   # placeholder flip point of the fake, not a tolerance


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    stats = {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
             "speed": 5.0, "sensor_radius": 700.0, "layer_transition_time": 0.0, "aoe_radius": 0.0}
    monkeypatch.setattr(plays_mod, "unit_stats", lambda name: dict(stats))
    monkeypatch.setattr(asym_mod, "unit_stats", lambda name: dict(stats))


def _result(margin):
    return FightResult(outcome="side0" if margin > 0 else "side1", margin=margin, strength_left=(1.0, 0.0),
                       survivors=(1, 0), heads=(1, 1), ticks=10, first_contact_tick=0, firing=[(0, 1, 1)],
                       firing_unit_seconds=(0.25, 0.25))


class Recorder:
    """fight_fn: records every Setup; side0 wins while side 1 has fewer than CUT units."""

    def __init__(self):
        self.setups = []

    def __call__(self, setup, seed, swap):
        self.setups.append((setup, seed, swap))
        enemy = sum(g.count for g in setup.groups if g.side == 1)
        return _result(0.5 if enemy < CUT else -0.5)


def _reference(terrain, lo=3, hi=7, **kw):
    rec = Recorder()
    build = with_terrain(asym_play(SIZE, Side("blob"), Side("blob")), terrain)
    res = find_break_even(build, SIZE, lo, hi, fight_fn=rec, **kw)
    return res, rec


def test_signature_defaults():
    """Defaults: replicates 10, near_replicates 30, max_rounds 2, fight_fn and map_fn None."""
    p = inspect.signature(naive_break_even).parameters
    assert [p[k].default for k in ("replicates", "near_replicates", "max_rounds", "fight_fn", "map_fn")] == \
        [10, 30, 2, None, None]
    assert list(p)[:6] == ["kind", "seed", "terrain", "size", "enemy_from", "enemy_to"]


def test_map_report_fields_in_order():
    """MapReport is a dataclass with kind, seed, terrain, naive."""
    assert [f.name for f in dataclasses.fields(MapReport)] == ["kind", "seed", "terrain", "naive"]


def test_report_carries_inputs_and_a_break_even():
    """naive_break_even returns a MapReport holding kind, seed, the terrain object and a BreakEven over the scanned heads."""
    rec = Recorder()
    rep = naive_break_even("block", 7, T, SIZE, 3, 7, fight_fn=rec, **KW)
    assert isinstance(rep, MapReport) and isinstance(rep.naive, BreakEven)
    assert (rep.kind, rep.seed, rep.terrain) == ("block", 7, T)
    assert [c.enemy_heads for c in rep.naive.scan.cells] == [3, 4, 5, 6, 7]
    assert (rep.naive.beats, rep.naive.loses_to) == (CUT - 1, CUT)


def test_setups_carry_the_terrain_shifted_into_canvas_coordinates():
    """Every fought Setup has terrain shifted by half the canvas, and every unit and goal inside the canvas."""
    rec = Recorder()
    naive_break_even("block", 0, T, SIZE, 3, 7, fight_fn=rec, **KW)
    assert rec.setups
    want = shift_terrain(T, CANVAS[0] / 2, CANVAS[1] / 2)
    for setup, _, _ in rec.setups:
        assert setup.terrain == want and setup.terrain.canvas == CANVAS
        for g in setup.groups:
            assert 0 <= g.x <= CANVAS[0] and 0 <= g.y <= CANVAS[1]


def test_both_sides_are_blob_with_one_unit_type():
    """Naive against naive: each side is one blob group of a single unit type, the same type on both sides."""
    rec = Recorder()
    naive_break_even("open", 0, Terrain(canvas=CANVAS), SIZE, 3, 5, fight_fn=rec, **KW)
    for setup, _, _ in rec.setups:
        assert sorted(g.side for g in setup.groups) == [0, 1]
        assert all(g.formation == "blob" for g in setup.groups)
        assert len({g.unit for g in setup.groups}) == 1
        assert next(g.count for g in setup.groups if g.side == 0) == SIZE


def test_call_set_equals_find_break_even_on_the_wrapped_build():
    """The fights and the BreakEven equal a direct find_break_even on with_terrain(asym_play(blob, blob)), in order."""
    rec = Recorder()
    rep = naive_break_even("block", 3, T, SIZE, 3, 7, fight_fn=rec, **KW)
    ref, ref_rec = _reference(T, **KW)
    assert ref.refined and rec.setups == ref_rec.setups   # refinement ran, so the near cells are covered too
    assert rep.naive == ref


def test_deterministic_for_equal_calls():
    """Two calls with equal arguments and a deterministic fake give equal reports."""
    a = naive_break_even("block", 1, T, SIZE, 3, 7, fight_fn=Recorder(), **KW)
    b = naive_break_even("block", 1, T, SIZE, 3, 7, fight_fn=Recorder(), **KW)
    assert a == b


def test_map_fn_is_passed_through():
    """map_fn receives the jobs and answers them; the report equals the fight_fn one."""
    rec = Recorder()
    calls = []

    def map_fn(jobs):
        calls.append(len(jobs))
        return [rec(*j) for j in jobs]

    rep = naive_break_even("block", 0, T, SIZE, 3, 5, map_fn=map_fn, **KW)
    assert calls and rec.setups
    assert rep.naive == naive_break_even("block", 0, T, SIZE, 3, 5, fight_fn=Recorder(), **KW).naive


def test_fight_fn_and_map_fn_together_raise():
    """Passing both is a ValueError, as in find_break_even."""
    with pytest.raises(ValueError):
        naive_break_even("open", 0, Terrain(canvas=CANVAS), SIZE, 3, 5, fight_fn=Recorder(), map_fn=lambda j: [], **KW)


def _canned(beats, loses_to, multi):
    scan = ScanResult(size=SIZE, cells=[], beats=beats, loses_to=loses_to)
    return BreakEven(scan=scan, flips=[], multi_flip=multi, beats=beats, loses_to=loses_to, refined=[], rounds=0)


def test_map_labels_values():
    """map_labels returns exactly the five labels, taken from the report."""
    rep = MapReport(kind="wall", seed=4004, terrain=T, naive=_canned(3, 5, True))
    assert map_labels(rep) == {"map_kind": "wall", "map_seed": 4004, "naive_beats": 3, "naive_loses_to": 5,
                               "naive_multi_flip": True}


def test_map_labels_keep_none():
    """A break-even with no flip gives None labels, kept as None."""
    rep = MapReport(kind="open", seed=0, terrain=T, naive=_canned(None, None, False))
    got = map_labels(rep)
    assert got["naive_beats"] is None and got["naive_loses_to"] is None and got["naive_multi_flip"] is False
    assert set(got) == {"map_kind", "map_seed", "naive_beats", "naive_loses_to", "naive_multi_flip"}


def test_map_labels_do_not_collide_with_fixed_row_keys_and_feed_fight_row():
    """No label is a fixed row key, and fight_row accepts them as labels."""
    got = map_labels(MapReport(kind="open", seed=0, terrain=T, naive=_canned(3, 5, False)))
    assert not set(got) & set(rows._FIXED)
    row = rows.fight_row(_result(0.5), **got)
    assert row["map_kind"] == "open" and row["naive_beats"] == 3


def test_works_on_a_sampled_map():
    """A sampled lane map goes through naive_break_even (its terrain is in play coordinates, units stay inside)."""
    t = sample_map("lane", 2)
    rec = Recorder()
    rep = naive_break_even("lane", 2, t, SIZE, 3, 5, fight_fn=rec, **KW)
    assert rep.terrain == t and rec.setups
