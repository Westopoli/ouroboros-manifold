# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md "Rev 3 (proposed 2026-10-07)": placed formations, decided by survivors
"""Rev 3: Setup.decided_by_survivors, the `decided` outcome, scenes.placed_scene, a five-feature lhs_draw.

Assumed names (the spec section fixes them; the builder must match or the test-writer is told):
  - Setup.decided_by_survivors: bool = False. When True the stalemate window and the mop-up are not used: after first damage,
    400 consecutive ticks in which no living unit can_see a living enemy end the fight with outcome "decided".
  - FightResult.winner: Optional[str], "side0" | "side1" | "draw" for a "decided" fight, None for every other outcome.
    The winner is by remaining hp sums; a gap of at most 5% of the larger sum is "draw".
  - The blind count starts at the first tick on which nobody sees an enemy (after first damage) and ends the fight 400 ticks
    later, i.e. at tick first_blind_tick + 400. Sight on any tick resets it.
  - scenes.placed_scene(layout, play) -> build(enemy_heads, swap) like the other scenes; `layout` is a Terrain in play
    coordinates (maps.layout_map output), `play` a plays_space.PLAYS name; the first groups of the two sides sit
    plays_space.START_GAP (the plays' contact distance) apart, their midpoint on the layout's choke (the middle of the
    gap between the wall blocks); Setup.start_distance stays None; Setup.decided_by_survivors is True.
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


CHOKE = (240.0, 40.0)   # centre of the gap in LAYOUT below


def _gap_mid(terrain):
    """Midpoint of the gap between two blocks stacked at the same x (the choke)."""
    a, b = sorted(terrain.blocks, key=lambda k: k.y0)[:2]
    return ((a.x0 + a.x1) / 2, (a.y1 + b.y0) / 2)


LAYOUT = Terrain(canvas=(4000.0, 4000.0),
                 blocks=(Block(190.0, -800.0, 290.0, -10.0, 0, 4), Block(190.0, 90.0, 290.0, 800.0, 0, 4)))


@pytest.mark.parametrize("play", ["s2_spread_line", "s4_bait"])
def test_placed_scene_puts_the_formations_at_contact_distance_around_the_choke(play):
    """Rev 3 rule 1: anchors contact distance apart, the choke midpoint between them, start_distance not used."""
    setup = scenes.placed_scene(LAYOUT, play)(16, False)
    first = {}
    for g in setup.groups:
        first.setdefault(g.side, g)
    a, b = first[0], first[1]
    assert ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 == pytest.approx(plays_space.START_GAP)
    gx, gy = _gap_mid(setup.terrain)
    assert ((a.x + b.x) / 2, (a.y + b.y) / 2) == pytest.approx((gx, gy))
    assert setup.start_distance is None
    assert setup.decided_by_survivors is True


def test_placed_scene_follows_the_choke_when_the_layout_moves():
    """Rev 3 rule 1: shifting the layout's gap shifts the anchors by the same amount, distance unchanged."""
    moved = Terrain(canvas=LAYOUT.canvas, blocks=tuple(
        dataclasses.replace(k, y0=k.y0 + 120.0, y1=k.y1 + 120.0) for k in LAYOUT.blocks))
    mid = lambda s: (lambda f: ((f[0].x + f[1].x) / 2, (f[0].y + f[1].y) / 2))(
        {g.side: g for g in reversed(s.groups)})
    s0 = scenes.placed_scene(LAYOUT, "s2_spread_line")(16, False)
    s1 = scenes.placed_scene(moved, "s2_spread_line")(16, False)
    assert mid(s1)[1] - mid(s0)[1] == pytest.approx(120.0)
    assert _gap_mid(s1.terrain)[1] - _gap_mid(s0.terrain)[1] == pytest.approx(120.0)


# ---- five features --------------------------------------------------------------------------------------------

FIVE = {"choke_width_bodies": (0, 2, 4, 8), "detour_ratio": (0, 1.5, 3), "lane_count": (0, 1, 2),
        "blocked_layer_top": (0, 2, 4), "cover_density_corridor": (0, 0.1, 0.3)}


def test_lhs_draw_has_five_features_covering_every_value_in_18_layouts_and_no_start_distance():
    """Rev 3 cost change: 5 features, 4 x 3 x 3 x 3 x 3 = 324 layouts in the grid; start_distance is gone."""
    draw = depth.lhs_draw(18, 7)
    assert len(draw) == 18
    assert all(set(d) == set(FIVE) for d in draw)
    assert not any("start_distance" in d for d in draw)
    for k, values in FIVE.items():
        assert {d[k] for d in draw} == set(values), k
    assert dict(depth.VALUES) == FIVE
    assert json.dumps(depth.lhs_draw(18, 7), sort_keys=True) == json.dumps(draw, sort_keys=True)
