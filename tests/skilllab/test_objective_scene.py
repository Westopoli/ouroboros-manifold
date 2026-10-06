# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md (rev 2) section 4, piece P2 (objective scene)
"""P2: Setup.start_distance and Setup.objective, an objective scene, the stalemate window starting at first damage,
and the existing plays staying byte-identical.

Assumed names (the spec gives none; the builder must match or the test-writer is told): Setup fields `start_distance`
and `objective`, both default None, objective an (x, y); scenes.objective_scene(start_distance, unit="Vanguard",
size=16) returns a build(enemy_heads, swap) like the other scenes."""
import dataclasses
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes import FakeEngine  # noqa: E402
from scripts.skilllab import engine, plays, rows, scan, scenes  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

# sha256 of the rows of blob_play(8) cell 8 and line_play(8) cell 8, 2 replicates, recorded on origin/main before P2
DEFAULT_PLAYS_HASH = "c2d917ca33d02bec905583071a1ab873e007c8103326fa02785efaea65439ca7"


@pytest.fixture
def stub_place(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def _G(side):
    return Group(side=side, unit="Vanguard", count=1, formation="line", x=-300.0 if side == 0 else 300.0, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def _run(script, max_ticks, stalemate_ticks, **extra):
    s = Setup(groups=(_G(0), _G(1)), unit_types={}, max_ticks=max_ticks, stalemate_ticks=stalemate_ticks,
              sample_every=5, **extra)
    return fight(s, 0, False, engine=FakeEngine(script=script))


def _hit_at(*script_ticks):
    """Script: side 1's first unit loses 1 hp when the script runs at each of these ticks."""
    def poke(t, f):
        if t in script_ticks:
            u = f.units_of(1)[0]
            f.set_hp(u, f.units[u]["hp"] - 1)
    return poke


def test_setup_gains_start_distance_and_objective_defaulting_to_none():
    """Section 4 P2: Setup gains `start_distance` and `objective`, default None = today's behaviour."""
    fields = Setup.__dataclass_fields__
    assert "start_distance" in fields and "objective" in fields
    s = Setup(groups=(), unit_types={})
    assert (s.start_distance, s.objective) == (None, None)
    assert "quiet_from_first_damage" in fields and s.quiet_from_first_damage is False


def test_setup_accepts_both_fields_as_keywords():
    """Section 4 P2: both fields are settable on a Setup (frozen dataclass, so by constructor or replace)."""
    s = Setup(groups=(), unit_types={}, start_distance=2800.0, objective=(0.0, 0.0))
    assert (s.start_distance, s.objective) == (2800.0, (0.0, 0.0))


def test_objective_scene_sets_sides_d_apart():
    """Section 4 P2 tests column: sides start `d` apart (anchor distance in x, same y)."""
    for d in (1400.0, 2800.0):
        setup = scenes.objective_scene(d)(16, False)
        g0 = next(g for g in setup.groups if g.side == 0)
        g1 = next(g for g in setup.groups if g.side == 1)
        assert setup.start_distance == d
        assert (g1.x - g0.x, g1.y - g0.y) == (d, 0.0)


def test_objective_scene_sends_both_groups_to_the_objective_between_them():
    """Section 1 / section 4 P2: both groups attack-move to the objective, at the corridor's middle."""
    setup = scenes.objective_scene(2800.0)(16, False)
    assert setup.objective is not None
    g0 = next(g for g in setup.groups if g.side == 0)
    g1 = next(g for g in setup.groups if g.side == 1)
    for g in (g0, g1):
        assert g.order == "attack_move" and tuple(g.goal) == tuple(setup.objective)
    assert g0.x < setup.objective[0] < g1.x
    assert setup.quiet_from_first_damage is True


def test_objective_scene_has_16_v_16_by_default_and_takes_the_enemy_heads():
    """Section 4 P2: a build function like the other scenes; the enemy headcount is the scanned axis."""
    setup = scenes.objective_scene(1400.0)(24, False)
    assert sorted((g.side, g.count) for g in setup.groups) == [(0, 16), (1, 24)]


def test_no_damage_before_contact_ends_only_at_the_cap(stub_place):
    """Section 'What the audit changed', stalemate row: before first contact the only ends are the cap and a wipe."""
    r = _run(None, max_ticks=50, stalemate_ticks=10, quiet_from_first_damage=True)
    assert (r.outcome, r.ticks) == ("cap", 50)


def test_quiet_window_starts_at_first_damage(stub_place):
    """Same row: first damage at tick 30, window 10 quiet ticks after it, so the fight ends stalemate at tick 40."""
    r = _run(_hit_at(29), max_ticks=100, stalemate_ticks=10, quiet_from_first_damage=True)
    assert (r.outcome, r.ticks) == ("stalemate", 40)


def test_a_later_damage_restarts_the_quiet_window(stub_place):
    """Same row: a hit at tick 35 restarts the count, so the stalemate lands at tick 45."""
    r = _run(_hit_at(29, 34), max_ticks=100, stalemate_ticks=10, quiet_from_first_damage=True)
    assert (r.outcome, r.ticks) == ("stalemate", 45)


def test_flag_false_keeps_the_quiet_window_from_tick_zero(stub_place):
    """Ruling 2026-10-06: default (flag False) is today's rule, 10 quiet ticks from tick 0 ends stalemate at 10."""
    r = _run(_hit_at(29), max_ticks=100, stalemate_ticks=10)
    assert (r.outcome, r.ticks) == ("stalemate", 10)


def test_far_open_ground_fight_does_not_stalemate_before_contact():
    """Section 4 P2 tests column: a fight at d = 2,800 on open ground does not end "stalemate" before contact."""
    r = fight(scenes.objective_scene(2800.0)(16, False), 0, False, engine=engine.Engine())
    assert r.first_contact_tick > 0
    assert r.outcome != "stalemate" or r.ticks > r.first_contact_tick


def _rows_hash():
    engine.Engine()
    out = []
    for name, build in (("blob", plays.blob_play(8)), ("line", plays.line_play(8))):
        c = scan.cell(build, 8, 2)
        out += [rows.fight_row(f, play=name, enemy_heads=c.enemy_heads) for f in c.fights]
    return hashlib.sha256(repr(out).encode()).hexdigest()


def test_existing_plays_with_default_fields_are_byte_identical():
    """Section 4 P2 tests column: existing contact-distance plays are byte-identical, rows recorded before and after.
    The first assert is what makes this red on main (the fields do not exist); the hash was recorded on main."""
    s = plays.blob_play(8)(8, False)
    assert (s.start_distance, s.objective) == (None, None)
    assert _rows_hash() == DEFAULT_PLAYS_HASH
