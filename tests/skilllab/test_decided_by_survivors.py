# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md Rev 3 (decided by survivors) and Rev 4 (the hold condition); placement tests are in test_placed_by_feature.py
"""Rev 3: Setup.decided_by_survivors, the `decided` outcome, scenes.placed_scene, a five-feature lhs_draw.

Assumed names (the spec section fixes them; the builder must match or the test-writer is told):
  - Setup.decided_by_survivors: bool = False. When True the stalemate window and the mop-up are not used: after first damage,
    400 consecutive ticks in which no living unit can_see a living enemy end the fight with outcome "decided".
  - FightResult.winner: Optional[str], "side0" | "side1" | "draw" for a "decided" fight, None for every other outcome.
    The winner is by remaining hp sums; a gap of at most 5% of the larger sum is "draw".
  - The blind count starts at the first tick on which nobody sees an enemy (after first damage) and ends the fight 400 ticks
    later, i.e. at tick first_blind_tick + 400. Sight on any tick resets it.
  - placement (Rev 4 supersedes Rev 3's translated formations) is tested in test_placed_by_feature.py.
"""
import dataclasses
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.formations as formations_mod  # noqa: E402
import scripts.skilllab.fight as fight_mod  # noqa: E402
from fakes_timeline import TimelineFakeEngine  # noqa: E402
from scripts.skilllab import depth, plays, plays_space, scan, scenes  # noqa: E402
from scripts.skilllab.contract import WIN_MARGIN, Block, FightResult, Group, Setup, Terrain  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from test_objective_scene import DEFAULT_PLAYS_HASH, _rows_hash  # noqa: E402

BLIND = 400


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


def _run(damage, sees, max_ticks=3000, **setup_kw):
    """damage(f): called at script tick 29 (the fight sees it at tick 30); sees(tick) -> do the sides see each other.
    stalemate_ticks is 10 on purpose: with the flag set it must not end anything."""
    def script(t, f):
        if t == 29:
            damage(f)

    eng = TimelineFakeEngine(script=script, can_see_fn=lambda f, o, e: sees(f.step_count))
    s = Setup(groups=(_G(0), _G(1)), unit_types={}, max_ticks=max_ticks, stalemate_ticks=10, sample_every=5,
              decided_by_survivors=True, **setup_kw)
    return fight(s, 0, False, engine=eng)


def _hp1(hp):
    """Damage script: side 1's unit drops to `hp` (side 0's stays 100)."""
    return lambda f: f.set_hp(f.units_of(1)[0], hp)


def test_setup_gains_decided_by_survivors_defaulting_to_false():
    """Rev 3 rule 2: Setup gains `decided_by_survivors: bool`, default False = today's rules."""
    assert "decided_by_survivors" in Setup.__dataclass_fields__
    assert Setup(groups=(), unit_types={}).decided_by_survivors is False


def test_decided_after_400_blind_ticks_from_first_blind_tick_winner_by_hp(stub_place):
    """Rule 2: damage at tick 30, sight until tick 100, first blind tick 101: ends ('decided', 501), winner side0 (100 v 40 hp).
    stalemate_ticks=10 and no hp change after tick 30 would end it at 40 under the old rule."""
    r = _run(_hp1(40), sees=lambda t: t <= 100)
    assert (r.outcome, r.ticks) == ("decided", 101 + BLIND)
    assert r.winner == "side0"


def test_decided_winner_is_the_side_with_more_hp(stub_place):
    """Rule 2: the survivors decide; flip the damage onto side 0 and side 1 wins."""
    r = _run(lambda f: f.set_hp(f.units_of(0)[0], 40), sees=lambda t: t <= 100)
    assert (r.outcome, r.winner) == ("decided", "side1")


def test_hp_within_5_percent_is_a_draw(stub_place):
    """Rule 2: 100 v 97 hp (3% apart) is a draw; the outcome is still 'decided'."""
    r = _run(_hp1(97), sees=lambda t: t <= 100)
    assert (r.outcome, r.ticks, r.winner) == ("decided", 101 + BLIND, "draw")


def test_hp_just_outside_the_5_percent_band_has_a_winner(stub_place):
    """Rule 2: 100 v 94 hp (6% of the larger sum) is not a draw."""
    r = _run(_hp1(94), sees=lambda t: t <= 100)
    assert (r.outcome, r.winner) == ("decided", "side0")


def test_blind_ticks_before_any_damage_do_not_end_the_fight(stub_place):
    """Rule 2: before first damage the only ends are the cap and a wipe; 600 blind ticks, no damage, ends at the cap."""
    eng = TimelineFakeEngine(can_see_fn=lambda f, o, e: False)
    s = Setup(groups=(_G(0), _G(1)), unit_types={}, max_ticks=600, stalemate_ticks=10, sample_every=5,
              decided_by_survivors=True)
    r = fight(s, 0, False, engine=eng)
    assert (r.outcome, r.ticks, r.winner) == ("cap", 600, None)


def test_sight_returning_before_400_resets_the_blind_count(stub_place):
    """Rule 2: blind 101 to 299 (199 ticks), sight 300 to 349, blind again from 350: ends ('decided', 350 + 400)."""
    r = _run(_hp1(40), sees=lambda t: t <= 100 or 300 <= t <= 349)
    assert (r.outcome, r.ticks) == ("decided", 350 + BLIND)


def test_sight_every_few_ticks_never_decides(stub_place):
    """Rule 2: 399 blind ticks then one tick of sight, repeated: no 400-tick run exists, so the fight runs to the cap."""
    r = _run(_hp1(40), sees=lambda t: t <= 100 or (t - 100) % 400 == 0, max_ticks=1500)
    assert (r.outcome, r.ticks, r.winner) == ("cap", 1500, None)


def test_a_wipe_still_ends_the_fight_as_before(stub_place):
    """Rule 2: a side wiped out ends the fight as 'side0' with no winner field set (unchanged outcomes)."""
    r = _run(_hp1(0), sees=lambda t: True)
    assert (r.outcome, r.ticks, r.winner) == ("side0", 30, None)


# ---- scan.cell_result ------------------------------------------------------------------------------------------

def _fr(outcome, margin, winner):
    return FightResult(outcome=outcome, margin=margin, strength_left=(1.0, 0.0), survivors=(1, 1), heads=(1, 1), ticks=1,
                       first_contact_tick=0, firing=[], firing_unit_seconds=(0.0, 0.0), winner=winner)


def test_cell_result_scores_decided_by_the_winner_like_a_wipe():
    """Rule 2 scoring: a decided cell is won when side 0 is the winner in every fight and the mean margin clears WIN_MARGIN."""
    won = scan.cell_result(8, [_fr("decided", 0.5, "side0")] * 4, WIN_MARGIN)
    assert won.won is True
    lost = scan.cell_result(8, [_fr("decided", -0.5, "side1")] * 4, WIN_MARGIN)
    assert lost.won is False


def test_cell_result_a_decided_draw_is_not_a_win_even_with_a_margin_above_the_bar():
    """Rule 2 scoring: winner 'draw' (hp within 5%) counts as not won, whatever the normalised margin says."""
    c = scan.cell_result(8, [_fr("decided", 0.5, "draw")] * 4, WIN_MARGIN)
    assert c.won is False


def test_cell_result_one_side1_win_among_decided_fights_is_not_won():
    """Rule 2 scoring: like a wipe, the win must hold across the swapped fights too."""
    c = scan.cell_result(8, [_fr("decided", 0.9, "side0")] * 3 + [_fr("decided", -0.1, "side1")], WIN_MARGIN)
    assert c.won is False


# ---- existing scenes unchanged; placed_scene ------------------------------------------------------------------

def test_existing_scenes_stay_byte_identical_with_the_flag_at_its_default():
    """Rev 3 / P2 pattern: the field defaults False on blob_play and the rows of blob_play(8) and line_play(8) hash as before."""
    s = plays.blob_play(8)(8, False)
    assert s.decided_by_survivors is False
    assert _rows_hash() == DEFAULT_PLAYS_HASH


# ---- Rev 4 rule 2: the hold condition -------------------------------------------------------------------------
# Assumed names (spec Rev 4 gives "hold_ticks = 1,200" and "the defender's anchor" but not the fields; builder must match):
#   Setup.hold_ticks: int = 1200; Setup.defender_side: int = 0; Setup.hold_anchor: Optional[tuple] = None ((x, y), None = no hold rule).
#   With hold_anchor set, at tick first_damage + hold_ticks, if >= half the defender side's living units are within 300 wu of
#   hold_anchor and no living unit of the other side is, the fight ends outcome "held", winner = the defender's side name.

HOLD, RADIUS = 1200, 300.0


def _held_run(defender, script_extra=None, count=2, max_ticks=3000):
    anchor = (-300.0, 0.0) if defender == 0 else (300.0, 0.0)

    def script(t, f):
        if t == 29:
            f.set_hp(f.units_of(1)[0], 40)
        if script_extra:
            script_extra(t, f)

    eng = TimelineFakeEngine(script=script, can_see_fn=lambda f, o, e: True)
    g0, g1 = dataclasses.replace(_G(0), count=count), dataclasses.replace(_G(1), count=count)
    s = Setup(groups=(g0, g1), unit_types={}, max_ticks=max_ticks, stalemate_ticks=10, sample_every=5,
              decided_by_survivors=True, hold_ticks=HOLD, defender_side=defender, hold_anchor=anchor)
    return fight(s, 0, False, engine=eng)


def test_setup_gains_the_hold_fields():
    """Rev 4 rule 2: hold_ticks (1,200 draft), defender_side and hold_anchor are Setup fields with defaults that change nothing."""
    f = Setup.__dataclass_fields__
    assert {"hold_ticks", "defender_side", "hold_anchor"} <= set(f)
    s = Setup(groups=(), unit_types={})
    assert (s.hold_ticks, s.hold_anchor) == (1200, None)


@pytest.mark.parametrize("defender,winner", [(0, "side0"), (1, "side1")])
def test_held_ends_1200_ticks_after_first_damage_with_the_defender_winning(stub_place, defender, winner):
    """Rev 4 rule 2: damage first seen at tick 30, the defender keeps all units at its anchor, no attacker near:
    ends ('held', 30 + 1200) with the defender as winner, whichever side defends (sight never lapses, so not 'decided')."""
    r = _held_run(defender)
    assert (r.outcome, r.ticks, r.winner) == ("held", 30 + HOLD, winner)


def test_held_needs_at_least_half_the_defenders_near_the_anchor(stub_place):
    """Rev 4 rule 2: 1 of 2 defenders within 300 wu is half, enough; the other walks off at tick 100."""
    away = lambda t, f: f.set_pos(f.units_of(0)[1], -1500.0, 900.0) if t == 100 else None
    r = _held_run(0, away)
    assert (r.outcome, r.ticks, r.winner) == ("held", 30 + HOLD, "side0")


def test_held_not_reached_with_fewer_than_half_near_the_anchor(stub_place):
    """Rev 4 rule 2: 1 of 3 near the anchor is under half: no hold, the fight runs to the cap."""
    def away(t, f):
        if t == 100:
            for u in f.units_of(0)[1:]:
                f.set_pos(u, -1500.0, 900.0)
    r = _held_run(0, away, count=3)
    assert (r.outcome, r.ticks, r.winner) == ("cap", 3000, None)


def test_an_attacker_inside_the_radius_prevents_held(stub_place):
    """Rev 4 rule 2: a living attacker within 300 wu of the defender's anchor at tick 1,230: no hold."""
    r = _held_run(0, lambda t, f: f.set_pos(f.units_of(1)[0], -250.0, 0.0) if t == 100 else None)
    assert (r.outcome, r.ticks, r.winner) == ("cap", 3000, None)


def test_hold_rule_is_inert_without_an_anchor(stub_place):
    """Rev 4 rule 2: hold_anchor None (the default) never ends a fight as held."""
    eng = TimelineFakeEngine(script=lambda t, f: f.set_hp(f.units_of(1)[0], 40) if t == 29 else None,
                             can_see_fn=lambda f, o, e: True)
    s = Setup(groups=(_G(0), _G(1)), unit_types={}, max_ticks=2000, stalemate_ticks=10, decided_by_survivors=True)
    assert fight(s, 0, False, engine=eng).outcome == "cap"


def test_cell_result_scores_held_as_a_defender_win():
    """Rev 4 rule 2 scoring: held is like a wipe for the defender; side 0 the defender and winner in every fight is a win."""
    assert scan.cell_result(8, [_fr("held", 0.5, "side0")] * 4, WIN_MARGIN).won is True


def test_cell_result_held_by_the_other_side_is_not_won():
    """Rev 4 rule 2 scoring: held with winner side1 (side 1 defends) is a loss for side 0."""
    assert scan.cell_result(8, [_fr("held", -0.5, "side1")] * 4, WIN_MARGIN).won is False


def test_cell_result_one_lost_hold_among_held_fights_is_not_won():
    """Rev 4 rule 2 scoring: the win must hold across the swapped fights, as for a wipe."""
    c = scan.cell_result(8, [_fr("held", 0.9, "side0")] * 3 + [_fr("held", -0.1, "side1")], WIN_MARGIN)
    assert c.won is False



# ---- six features kept ----------------------------------------------------------------------------------------

SIX = {"choke_width_bodies": (0, 2, 4, 8), "detour_ratio": (0, 1.5, 3), "lane_count": (0, 1, 2),
       "blocked_layer_top": (0, 2, 4), "cover_density_corridor": (0, 0.1, 0.3), "start_distance": (1400, 2800)}


def test_lhs_draw_keeps_six_features_including_start_distance_covering_every_value_in_18_layouts():
    """Rev 3: placement replaces walking, not the feature; 4 x 3 x 3 x 3 x 3 x 2 = 648 layouts in the grid."""
    draw = depth.lhs_draw(18, 7)
    assert len(draw) == 18
    assert all(set(d) == set(SIX) for d in draw)
    for k, values in SIX.items():
        assert {d[k] for d in draw} == set(values), k
    assert dict(depth.VALUES) == SIX
    assert json.dumps(depth.lhs_draw(18, 7), sort_keys=True) == json.dumps(draw, sort_keys=True)
