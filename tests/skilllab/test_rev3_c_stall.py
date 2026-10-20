# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R7, test T9, defect D7); docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 50 (controls for decided_one_way_reach); ledger FINDING-lab-d7, FINDING-lab-d11 (Architect ruling 2026-10-20, implementation; Westley may veto); piece LAB-REV3-C
# Rule pins: R-164-01@511d57, R-164-03@e018aa
"""LAB-REV3-C, the two structural end conditions of fight(), on the fake engine (fast).

R-164-01 gives each type a reach (up, down) in layers: a unit on layer la reaches a unit on lb iff -down <= lb - la <= up. Effective range,
vision and knob scaling never enter either verdict below; only the reach table and the LIVE layers do.

  R7 / D7 / T9 `no_reach_stall`: from the first tick at which no living unit of either side can reach any living enemy, the fight ends
      there, as a finding row, never at the cap.
  FINDING-lab-d11 `decided_one_way_reach`: from the first tick at which every living unit of one side is unreachable by every living enemy
      and at least one unit of that side can reach a living enemy, the fight is decided for that side. RECORDED, NOT A STOP (Architect ruling
      2026-10-20, supersedes the stop; implementation; Westley may veto): verdict and decided_tick are set at the first decided tick and the
      fight PLAYS ON to elimination or the cap. Reason: a one-way scene is the game's own question (how fast a flyer force kills ground units
      that cannot reply; R-164-03 'reach is temporary' is tuned on it), so margin, damage and time-to-kill are data the lab keeps. One rule
      everywhere, no middle path by tick. The stall is the opposite: nothing can happen after mutual no-reach, so it still ends at its first tick.
      The two conditions are disjoint by construction.

BUILDER CONTRACT (the observable names; the tests pin these and nothing else about the implementation):
  contract.FightResult gets two defaulted fields (older call sites keep working):
      verdict: Optional[str] = None        None, or exactly "no_reach_stall" or "decided_one_way_reach" (the strings of
                                           contract.FROZEN_NAMES, see test_rev3_c_frozen_names.py)
      decided_tick: Optional[int] = None   the FIRST tick at which the fight was decided; set only with "decided_one_way_reach", else None
  A no_reach_stall fight:   outcome == "no_reach_stall" (RULED, Architect 2026-10-20, implementation, Westley may veto: the plan names the
                            finding; the outcome string is the finding's name), winner None, verdict "no_reach_stall",
                            ticks == the tick the condition first holds (read after the step that made it hold; a scene that starts
                            that way ends at tick 1 at the latest).
  A decided fight:          verdict "decided_one_way_reach" and decided_tick set at the first decided tick; the fight is stepped on; ticks >=
                            decided_tick. It ends (a) by elimination of the other side: outcome "side0" or "side1" (the decided side), the
                            tick of the last death; or (b) at the cap: READING (flagged to the Architect): outcome is the decided side's win
                            ("side0" or "side1"), NOT "cap", winner the same side, ticks == Setup.max_ticks, decided_tick < ticks. A
                            capped-but-decided row is a decided row: neither a cap row nor a defect (test_rev3_c_rows.py).
  Elimination wins: a fight never decided whose last enemy dies ends as before with verdict None; a fight decided early and then won by
                    elimination carries the verdict and decided_tick.
  Both are read from engine.profile_reach(w, type_id) and engine.unit_layer(w, u), every tick, so a mid-fight layer change counts.
  The cap (Setup.max_ticks) is Westley's and unchanged; a scene where reach runs both ways still ends at it as "cap".
Red today: the cap (outcome "cap", ticks == max_ticks) in every positive test; the negative controls are green on the base."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_rev3_c_support import DECIDED, STALL, G, kill, oracle, run, to_layer  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

CAP = 400


def verdict_of(r):
    return getattr(r, "verdict", None)


def decided_tick_of(r):
    return getattr(r, "decided_tick", None)


# ---------------------------------------------------------------------------------------------------- R7: mutual no-reach

def test_mutual_no_reach_from_the_start_ends_at_once_as_no_reach_stall():
    """R7, D7, T9: Vanguards on layer 0 against Vanguards on layer 2 (reach (0, 0) both): nobody can ever hit anybody. The fight ends
    as a no_reach_stall at the first tick, never at the cap. Red today: outcome cap, ticks == max_ticks."""
    r, f = run([G(0, "Vanguard", 3, 0), G(1, "Vanguard", 3, 2)], cap=CAP)
    assert oracle(f.living()) == ("mutual",)
    assert r.ticks < CAP, "the fight ran to the cap (%s at tick %d)" % (r.outcome, r.ticks)
    assert (r.outcome, verdict_of(r), r.winner) == (STALL, STALL, None)
    assert r.ticks <= 1 and decided_tick_of(r) is None


def test_mutual_no_reach_after_the_units_that_can_reply_are_dead_ends_at_that_tick():
    """D7: 'a stall once the units that can reply are dead'. Interceptor (2, 1) on layer 0 and Raider (1, 1) on layer 1 reach each other (so
    do the Vanguards behind them, one up and two up); at step 29 both die and the Vanguards left on layers 0 and 2 can reach nobody. The
    fight ends at tick 30, the tick the deaths are read. Red today: cap."""
    groups = [G(0, "Interceptor", 1, 0), G(0, "Vanguard", 2, 0), G(1, "Raider", 1, 1), G(1, "Vanguard", 2, 2)]
    r, f = run(groups, cap=CAP, events={29: [kill(0, 0), kill(1, 0)]})
    assert oracle(f.living()) == ("mutual",)
    assert r.ticks < CAP, "the fight ran to the cap (%s at tick %d)" % (r.outcome, r.ticks)
    assert (r.outcome, verdict_of(r), r.ticks) == (STALL, STALL, 30)


def test_control_the_same_scene_without_the_deaths_keeps_reach_both_ways_and_runs_to_the_cap():
    """Positive control (green on the base and after): with nobody dying, Interceptor and Raider still reach each other, so neither verdict
    is due and the fight ends at the cap, no tag."""
    groups = [G(0, "Interceptor", 1, 0), G(0, "Vanguard", 2, 0), G(1, "Raider", 1, 1), G(1, "Vanguard", 2, 2)]
    r, f = run(groups, cap=CAP)
    assert oracle(f.living()) is None
    assert (r.outcome, r.ticks, verdict_of(r)) == ("cap", CAP, None)


@pytest.mark.parametrize("swap", [False, True])
def test_a_reach_capable_type_with_no_target_layer_is_no_reach_stall_never_decided(swap):
    """The FINDING-lab-d11 case (e): the untouchable side (side 0, layer 0: the Raiders on layer 3 reach only layers 2 and 4) has no unit that
    can reach anyone either (its Interceptor reaches up to layer 2). Mutual no-reach: R7, not decided. Red today: cap."""
    groups = [G(0, "Interceptor", 1, 0), G(0, "Vanguard", 2, 0), G(1, "Raider", 2, 3)]
    r, f = run(groups, cap=CAP, swap=swap)
    assert oracle(f.living()) == ("mutual",)
    assert r.ticks < CAP, "the fight ran to the cap (%s at tick %d)" % (r.outcome, r.ticks)
    assert (verdict_of(r), r.outcome) == (STALL, STALL) and decided_tick_of(r) is None


def test_a_layer_change_mid_fight_is_read_live():
    """The layers are the live ones (a set_layer step moves a unit): Interceptor and Vanguard share layer 0 (reach both ways) until step 19
    moves the Vanguard to layer 3, out of the Interceptor's reach of 2: nobody reaches anybody, the stall is at tick 20. Red today: cap."""
    r, f = run([G(0, "Interceptor", 1, 0), G(1, "Vanguard", 1, 0)], cap=CAP, events={19: [to_layer(1, 0, 3)]})
    assert oracle(f.living()) == ("mutual",)
    assert r.ticks < CAP, "the fight ran to the cap (%s at tick %d)" % (r.outcome, r.ticks)
    assert (r.outcome, verdict_of(r), r.ticks) == (STALL, STALL, 20)


# ----------------------------------------------------------------------- the reach is the engine's (audit gap F4)

def test_a_setup_reach_override_of_zero_stalls_where_the_plays_table_would_not():
    """F4: a Raider whose Setup.unit_types entry says reach (0, 0), on layer 1 against Vanguards on layer 0: nobody can reach anybody, so the
    fight is a no_reach_stall at the first tick. plays_space._REACH says Raider (1, 1) and would see a fight (a builder that reads the static
    table instead of engine.profile_reach runs to the cap). Positive control in the same test: with the bible's (1, 1) the same scene is no stall.
    Red today: cap."""
    zero = {"Raider": {"base": "Raider", "reach": (0, 0)}}
    r, f = run([G(0, "Raider", 2, 1), G(1, "Vanguard", 2, 0)], cap=CAP, unit_types=zero)
    assert oracle(f.living()) == ("mutual",)
    assert r.ticks < CAP, "the fight ran to the cap (%s at tick %d)" % (r.outcome, r.ticks)
    assert (r.outcome, verdict_of(r), r.winner) == (STALL, STALL, None) and r.ticks <= 1
    base, fb = run([G(0, "Raider", 2, 1), G(1, "Vanguard", 2, 0)], cap=CAP)
    assert oracle(fb.living()) is None and (base.outcome, base.ticks, verdict_of(base)) == ("cap", CAP, None)


def test_a_setup_reach_override_that_raises_a_default_zero_type_decides_instead_of_stalling():
    """F4, the other direction: Vanguards on layer 0 against Vanguards on layer 2 are a mutual stall at the default (0, 0) (the first test of this
    file); a Setup entry giving the Vanguard reach (0, 2) lets the layer-2 side shoot down and nobody on layer 0 reach up: decided for side 1 at
    tick 1, never a stall. Architect ruling 2026-10-20, supersedes the stop: recorded, the fake does no damage, so the fight plays on to the cap
    and ends as the decided side's win (READING: not "cap"). Red today: cap."""
    wide = {"Vanguard": {"base": "Vanguard", "reach": (0, 2)}}
    r, f = run([G(0, "Vanguard", 2, 0), G(1, "Vanguard", 2, 2)], cap=CAP, unit_types=wide)
    assert oracle(f.living()) == ("decided", 1)
    assert (verdict_of(r), decided_tick_of(r)) == (DECIDED, 1) and r.outcome != STALL
    assert (r.outcome, r.winner, r.ticks) == ("side1", "side1", CAP)


# ---------------------------------------------------------------------------------------- FINDING-lab-d11: decided one way
# Architect ruling 2026-10-20, supersedes the stop: decided_one_way_reach is RECORDED (verdict and decided_tick at the first decided tick), the
# fight plays on to elimination or the cap.

@pytest.mark.parametrize("swap", [False, True])
@pytest.mark.parametrize("untouchable", [0, 1])
def test_one_way_reach_from_the_start_is_recorded_at_tick_one_and_the_fight_plays_on_to_the_cap(untouchable, swap):
    """FINDING-lab-d11: the Interceptors (2, 1) on layer 0 reach the Vanguards on layer 2, which cannot reach layer 0. Every unit of the
    Interceptor side is unreachable and one can reach: decided for that side, recorded at the first tick. The fake does no damage, so the
    fight is NOT stopped: it plays on to the cap and ends as the decided side's win (READING for the Architect: outcome "side0"/"side1", not
    "cap"; winner the same; decided_tick 1 < ticks == cap). Both orientations, both engine swaps. Red today: outcome cap, no verdict."""
    a, b = untouchable, 1 - untouchable
    groups = [G(a, "Interceptor", 2, 0), G(a, "Vanguard", 2, 0), G(b, "Vanguard", 3, 2)]
    r, f = run(sorted(groups, key=lambda g: g.side), cap=CAP, swap=swap)
    assert oracle(f.living()) == ("decided", a)
    side = "side%d" % a
    assert (verdict_of(r), decided_tick_of(r)) == (DECIDED, 1), "outcome %s at tick %d" % (r.outcome, r.ticks)
    assert (r.outcome, r.winner) == (side, side)
    assert r.ticks == CAP and decided_tick_of(r) < r.ticks, "the fight must play on after the decided tick (ticks %d)" % r.ticks


def test_a_decided_fight_plays_on_and_ends_by_elimination_after_the_decided_tick():
    """The unreachable side kills the other over a few ticks: Interceptor (side 0, layer 0) against three Vanguards on layer 2, which die at
    steps 9, 19 and 29 (read at ticks 10, 20, 30). Decided at tick 1 (recorded), the fight is stepped on and ends by elimination at tick 30,
    outcome side0 with the verdict and the first decided tick. Red today: the verdict is missing (and a build that stops at tick 1 fails
    ticks == 30)."""
    r, f = run([G(0, "Interceptor", 1, 0), G(1, "Vanguard", 3, 2)], cap=CAP,
               events={9: [kill(1, 0)], 19: [kill(1, 1)], 29: [kill(1, 2)]})
    assert oracle(f.living()) is None          # nobody left: the oracle's state at the end
    assert (r.outcome, r.winner, r.ticks) == ("side0", "side0", 30)
    assert (verdict_of(r), decided_tick_of(r)) == (DECIDED, 1)
    assert decided_tick_of(r) < r.ticks < CAP


def test_the_decided_tick_is_the_first_one_when_the_replying_unit_dies_and_the_fight_goes_on():
    """Interceptor (side 0, layer 0) and Raider (side 1, layer 1) reach each other; the Raider dies at step 29 (read at tick 30). Side 0 is then
    unreachable (the Vanguards of side 1 on layer 2 reach only layer 2) and its Interceptor reaches them: decided for side 0, decided_tick 30.
    The fight is not stopped: the two Vanguards die at steps 49 and 59 and it ends by elimination at tick 60 (decided_tick 30 < ticks 60).
    Red today: no verdict."""
    groups = [G(0, "Interceptor", 1, 0), G(0, "Vanguard", 2, 0), G(1, "Raider", 1, 1), G(1, "Vanguard", 2, 2)]
    r, f = run(groups, cap=CAP, events={29: [kill(1, 0)], 49: [kill(1, 1)], 59: [kill(1, 2)]})
    assert (r.outcome, r.winner, r.ticks) == ("side0", "side0", 60)
    assert (verdict_of(r), decided_tick_of(r)) == (DECIDED, 30)


def test_a_layer_change_that_takes_one_side_out_of_reach_records_the_decision_at_that_tick():
    """Live layers again: Interceptor and Vanguard share layer 0; at step 19 the Vanguard moves to layer 2, which the Interceptor still
    reaches (up 2) and the Vanguard no longer reaches layer 0. Decided for side 0, decided_tick 20; the Vanguard dies at step 39 and the fight
    ends by elimination at tick 40. Red today: no verdict."""
    r, f = run([G(0, "Interceptor", 1, 0), G(1, "Vanguard", 1, 0)], cap=CAP, events={19: [to_layer(1, 0, 2)], 39: [kill(1, 0)]})
    assert (r.outcome, verdict_of(r), decided_tick_of(r), r.ticks) == ("side0", DECIDED, 20, 40)


def test_the_decision_is_recorded_once_at_its_first_tick():
    """No later tick overwrites it: the decided tick stays the first one while the fight plays on (Vanguard on layer 2 for the whole run)."""
    r, _f = run([G(0, "Interceptor", 1, 0), G(1, "Vanguard", 1, 2)], cap=60)
    assert (verdict_of(r), decided_tick_of(r), r.ticks) == (DECIDED, 1, 60)


# ------------------------------------------------------------------------------------ negative controls (green on the base)

def test_control_one_reachable_unit_keeps_the_fight_undecided():
    """Side 0 holds an Interceptor on layer 0 and a Vanguard on layer 2; side 1 holds two Vanguards on layer 2. The Vanguard of side 0 can be
    reached by side 1, so 'every living unit of the side is unreachable' is false: no verdict (the cap ends it)."""
    r, f = run([G(0, "Interceptor", 1, 0), G(0, "Vanguard", 1, 2), G(1, "Vanguard", 2, 2)], cap=CAP)
    assert oracle(f.living()) is None
    assert (r.outcome, r.ticks, verdict_of(r), decided_tick_of(r)) == ("cap", CAP, None, None)


def test_control_reach_allowed_but_out_of_range_is_not_decided_and_not_stalled():
    """FINDING-lab-d11 negative control (the s3_layer_above 0.25 knob row): the reach table allows the hit both ways (Raiders on layers 1 and
    0), the groups stand 6000 wu apart, far outside any effective range. The verdicts are structural, so neither is due."""
    r, f = run([G(0, "Raider", 2, 1, x=-3000.0), G(1, "Raider", 2, 0, x=3000.0)], cap=CAP)
    assert oracle(f.living()) is None
    assert (r.outcome, r.ticks, verdict_of(r), decided_tick_of(r)) == ("cap", CAP, None, None)


def test_control_a_last_enemy_that_dies_is_an_ordinary_win_with_no_tag():
    """Elimination keeps its meaning where nobody was ever decided: Interceptor (side 0, layer 0) and Raider (side 1, layer 1) reach each other
    throughout (both sides could reach until the end); the Raider dies at step 49. Side 0 wins at tick 50 with no verdict (no living enemy is
    left to be reached or to reach). Architect ruling 2026-10-20, supersedes the stop: a fight decided early and then won by elimination is
    NOT this case; it carries the verdict (test_a_decided_fight_plays_on_and_ends_by_elimination_after_the_decided_tick)."""
    r, f = run([G(0, "Interceptor", 1, 0), G(1, "Raider", 1, 1)], cap=CAP, events={49: [kill(1, 0)]})
    assert (r.outcome, r.winner, r.ticks, verdict_of(r), decided_tick_of(r)) == ("side0", "side0", 50, None, None)
