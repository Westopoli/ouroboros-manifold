# Rule pins: R-087-01, R-087-06, R-096-02, R-005-09
"""Engine rule fixes 2026-11-11, Round 2, F9, whole fights: a unit with no target that is hit by an attacker it cannot see leaves the line of fire.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01): "Given an idle or attack-moving unit with no target that takes damage from an
attacker it cannot see or cannot reach, When the loop runs, Then it leaves the line of fire instead of standing or walking on blindly: it moves 200 wu
directly away from the damage direction and stops, and an attack-mover then resumes its attack-move toward its original point (R-096-02); once the attacker
is visible and in range it stands and fights. A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit; a repeat hit moves it again
(Westley 2026-11-06, the SC2 movement model)." The note under S-087: "The attack-mover relocation of R-087-01 is not built either (engine item,
csrc/unit.c:2169 and the flinch cancel at :2142)."

The single geometry is tests/csim/test_E11_R087_01_unseen_attacker_moves_the_unit.py. This file is the whole fight that showed the fault: the trap fight L-0080
(16 blue on hill blocks and an arc, 32 red in a pocket that attack-move out of it; catalogue/L-0080.toml) no longer resolves in 12,000 ticks once high ground can
fire down (R-087-10, F7): red units stand on the low ground with an arrived attack-move, are shot from the hill by blue units they cannot see (low ground never
sees up, E-01 R-005-09), hold no target and never move. Trace: engine-rules-baseline/r2d/ (L-0080 seed 1, first unit 47 at tick 2008).

Configuration: `run.fight(layout, seed 1, sight "on", 600 simulated seconds)`: the lab's stage 4 rule set, walking units, the layout's hills and boxes laid as the lab
lays them, targeting by sight on, reach 0 up 1 down. Nothing is switched off. 600 s is the lab's own cap (12,000 ticks): the first standing victim of L-0080 is hit at
tick 2008, past the 2,000 ticks `oracle.FIGHT_SECONDS` runs, so these tests run the whole cap (DRAFT-f9-seconds 600).

The judge is not the F0 checker (scripts/skilllab/invariants.py has no check for this rule). It is `engine_rules_unseen_oracle.standing_in_unseen_fire`, defined
there word for word: a living unit with no target, hit by an enemy its side does not see, that has stood within 50 wu of where the run of such hits began for
more than DRAFT-inv-unseen-fire-ticks 60 ticks while the hits continue (DRAFT-f9-hit-gap 60 ticks). These tests do NOT assert that the fight ends by any tick,
or who wins: that is the owner's to judge.

Premises dumped from the built tree (2026-11-11, Round 2 tip 1feed3c5, seed 1, sight on, 600 s):
  L-0080  12000 ticks (the cap)  494 unseen hits, all 494 from a higher layer than the victim   429 violations in 13 victims, first (tick 2008, unit 47, 61 ticks in)
  L-0061   1476 ticks             55 unseen hits, all 55 from a higher layer                       0 violations (the victims move off)
  L-0039   2314 ticks             11 unseen hits, none from a higher layer (cover boxes)           0 violations
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
import engine_rules_unseen_oracle as unseen  # noqa: E402

SECONDS = 600           # DRAFT-f9-seconds: the lab's cap
MIN_TICKS = 300         # detector bound: a fight shorter than this did not exercise the rule


# ------------------------------------------------------------------ the detector against a made-up fight (green today)

class _Rec:
    """The part of Recorder the measure reads: ticks and sides. Unit 1 (side 0, layer 0) is shot by unit 2 (side 1, layer 1) every 30 ticks for 300 ticks."""

    def __init__(self, move=0.0, seen=False, target=0, hit_every=30):
        self.side = {1: 0, 2: 1}
        self.ids = [1, 2]
        self.ticks = []
        for n in range(1, 301):
            x = 1000.0 + move * n
            row = {1: {"alive": True, "x": x, "y": 1000.0, "layer": 0, "tgt": target}, 2: {"alive": True, "x": 1200.0, "y": 1000.0, "layer": 1, "tgt": 0}}
            fires = [(2, 1)] if n % hit_every == 0 else []
            vis = {(0, 2): seen, (1, 1): True}
            self.ticks.append({"n": n, "pre": row, "post": row, "fires": fires, "vis_pre": vis, "vis_post": vis})


def test_R_087_01_control_the_measure_flags_a_unit_that_stands_in_unseen_fire():
    """Control (green today): the measure flags a unit with no target that stands still for 300 ticks while an enemy it does not see shoots it every 30
    ticks (hits from tick 30; violations from the first hit more than 60 ticks after the first: ticks 120 to 300 = 7), and flags none of the four things it must
    leave alone: a unit that walks off at 2 wu per tick (out of the 50 wu circle in 25 ticks), a shooter the victim's side sees, a victim that holds a target,
    and hits more than DRAFT-f9-hit-gap apart."""
    stood = unseen.standing_in_unseen_fire(_Rec())
    assert [b[0] for b in stood] == [120, 150, 180, 210, 240, 270, 300], "the measure missed a standing unit: %s" % stood
    assert unseen.standing_in_unseen_fire(_Rec(move=2.0)) == [], "flagged a unit that walks off"
    assert unseen.standing_in_unseen_fire(_Rec(seen=True)) == [], "flagged a unit shot by an enemy its side sees"
    assert unseen.standing_in_unseen_fire(_Rec(target=2)) == [], "flagged a unit that holds a target"
    assert unseen.standing_in_unseen_fire(_Rec(hit_every=61)) == [], "flagged hits more than the hit gap apart"


# ------------------------------------------------------------------ whole fights

def _played(name):
    rec = oracle.played(name, "on", SECONDS)
    assert len(rec.ticks) >= MIN_TICKS, "scene broken: %s ran %d ticks" % (name, len(rec.ticks))
    assert any(tk["fires"] for tk in rec.ticks), "scene broken: nobody fired in %s" % name
    return rec


@pytest.mark.parametrize("name", ["L-0061", "L-0039"])
def test_R_087_01_control_a_fight_where_the_hit_units_move_off_measures_zero(name):
    """R-087-01 control (green today, must stay): L-0061 (55 unseen hits, all from a higher layer) and L-0039 (11) fought with sight on to the end: the measure
    finds no unit standing in unseen fire. Proves the measure runs on a real fight and does not flag units that move, so the L-0080 test below is red for the
    rule's sake."""
    rec = _played(name)
    s = unseen.summary(rec)
    assert s["violations"] == 0, "%s: %s" % (name, s)


def test_R_087_01_premise_the_trap_fight_has_units_shot_from_the_hill_that_cannot_see_it():
    """Premise (green today): L-0080, seed 1, sight on, the whole 12,000-tick cap: units with no target are hit by enemies their side does not see (494 times
    today), every one of them from a higher layer than the victim (the hills). The count is dumped, not pinned: the test asserts only that there are some and
    that they come from above, which is the scene the rule is about."""
    rec = _played("L-0080")
    s = unseen.summary(rec)
    assert s["unseen_hits"] > 0, "scene broken: no unit was hit by an enemy its side does not see: %s" % s
    assert s["from_higher_layer"] == s["unseen_hits"], "premise: some unseen hits come from the same or a lower layer: %s" % s


def test_R_087_01_no_unit_stands_in_unseen_fire_for_more_than_60_ticks():
    """R-087-01, per tick over a whole fight, sight on, walking units, the layout's hills: no living unit with no target that is hit by an enemy its side does
    not see stands within 50 wu of where it was first hit for more than 60 ticks in a row while the hits continue; it leaves the line of fire (moves 200 wu
    directly away from the damage direction, then an attack-mover resumes its point), and a repeat hit moves it again. L-0080 seed 1. Red today: the red
    attack-movers that stand on the low ground are shot from the hill for ever (429 violating hits in 13 units, first unit 47 at tick 2008)."""
    rec = _played("L-0080")
    s = unseen.summary(rec)
    bad = unseen.standing_in_unseen_fire(rec)
    assert not bad, "L-0080: %d hits on units standing in unseen fire, %d units over %d ticks, first %s; summary %s" % (
        len(bad), len({b[1] for b in bad}), s["ticks"], bad[:3], s)
