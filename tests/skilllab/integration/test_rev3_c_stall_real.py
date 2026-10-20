# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R7, test T9, defects D7 and D8); docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 50 (controls for decided_one_way_reach); ledger FINDING-lab-d7, FINDING-lab-d11 (Architect ruling 2026-10-20, implementation; Westley may veto); piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C against the real engine: the structural end conditions on the real library and on the real range_up scenes.

THE ORACLE (tests/skilllab/test_rev3_c_support.py): an Engine subclass that, after every tick of the real world, applies the reach rule of
R-164-01 (-down <= layer(b) - layer(a) <= up, om_unit_profile_reach and om_unit_get_layer of the library, living units only) and records the first
tick of each state: {"mutual": t} (nobody reaches anybody) and {("decided", side): t} (every living unit of `side` is unreachable and one of
them reaches a living enemy). It changes nothing in the simulation. The fight under test must end AT the oracle's tick with the matching verdict.

Contract of the verdict fields: see test_rev3_c_stall.py (FightResult.verdict, FightResult.decided_tick, outcome "no_reach_stall" for the stall;
a decided fight keeps outcome "side0" or "side1"). Architect ruling 2026-10-20, supersedes the stop: decided_one_way_reach is RECORDED, not a stop:
decided_tick is the first decided tick (the oracle's) and the fight plays on to elimination or the cap; the stall still ends at its first tick.

What is here:
  fast (a few seconds):
    - a hand-built one-way scene (6 Interceptors on layer 0 against 6 Vanguards on layer 2): decided at the first tick (recorded), and the fight
      plays on to the Interceptors shooting the Vanguards dead (elimination, side 0);
    - a hand-built mutual scene (Vanguards two layers apart): a stall at the first tick (today: the cap).
  OM_LAB_SLOW=1 (10 to 40 s a fight), the real range_up / null-control scenes of layout 192 (sweep.smoke_layouts()["192"]):
    - T9, D7: the null control of s3_layer_above and of s3_types_by_reach (sweep.default_builds(play, "reach_zero", features), every type at
      reach (0, 0)): the layer-1 units can neither fire nor be fired at, the layer-0 units fight to the death, and what is left cannot reach
      anybody. Measured 2026-10-20 on this tree (seed 0, swap False, 16 heads): oracle mutual at tick 1732 (s3_layer_above, survivors (8, 8)
      at the cap) and 1670 (s3_types_by_reach, survivors (8, 12)); both ran to the cap. Setup.max_ticks is lowered to 4000 for speed only.
    - FINDING-lab-d11 positive controls: s3_types_by_reach, range_up 0.25, 20 side-1 heads, seed 2, swap False and swap True. On this tree
      (after LAB-REV2-L8M2, decision 50) these two fights end side 0 by elimination at ticks 7281 and 5469 and the oracle sees "decided side 0"
      at ticks 5554 and 4466 (asserted since the ruling of 2026-10-20: the sim is deterministic and recording changes nothing in it). OPEN: the Architect's named fight (seed 1, swap False, survivors (1, 3), capped at
      12000, the survivor untouchable from tick 7411) was measured on the L8M tip b35c4576; on this tree it ends side 1 at tick 5932 with no
      decided moment (of the six fights run on this tree, seeds 0 to 2 with swap False and True, only seed 2 shows one, in both swaps), so seed 2 stands in. The preconditions
      below fail loudly if a later tree stops showing the moment, so the seed gets re-picked, not the assertion weakened.
    - negative controls (green on the base): the same setup, seed 0 and seed 1 swap False, are ordinary wins with no tag (the oracle never fires);
      s3_layer_above, range_up 0.25, 48 heads, seed 1 swap True: the reach table allows the hit (13 enemies have reach (1, 1) though out of
      range), no tag, not a cap, and the side shot at re-engages (reengage[1] >= 1; LAB-REV2-L8M2)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "tests" / "skilllab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import sweep  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from test_rev3_c_support import DECIDED, STALL, oracle_engine  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")

INTERCEPTOR = {"base": "Interceptor", "reach": (2, 1)}


def verdict_of(r):
    return getattr(r, "verdict", None)


def decided_tick_of(r):
    return getattr(r, "decided_tick", None)


def hand(side0, side1, cap=3000, types=None):
    """side0 / side1: (unit, layer). 6 units each, blobs 600 wu apart on an open canvas."""
    g = lambda side, unit, layer: Group(side=side, unit=unit, count=6, formation="blob", x=300.0 if side == 0 else 900.0, y=400.0,
                                        facing_deg=0.0 if side == 0 else 180.0, layer=layer, order="attack_move", params={"radius": 60.0})
    return Setup(groups=(g(0, *side0), g(1, *side1)), unit_types=types if types is not None else {"Interceptor": INTERCEPTOR}, max_ticks=cap)


# ---------------------------------------------------------------------------------------------------- hand-built real scenes (fast)

def test_a_one_way_scene_on_the_real_engine_is_recorded_decided_at_the_first_tick_and_plays_on():
    """FINDING-lab-d11, Architect ruling 2026-10-20 (supersedes the stop): Interceptors (up 2) on layer 0, Vanguards (0, 0) on layer 2. The oracle
    sees 'decided side 0' at tick 1; the fight records exactly that (decided_tick 1, verdict) and PLAYS ON: the Interceptors shoot the Vanguards
    dead and side 0 wins by elimination. MEASUREMENT (2026-10-20, seed 0, swap False, on the base, which never sets a verdict): oracle decided at
    tick 1, elimination at tick 2265 (side 0). The elimination tick is not pinned (it is the sim's, not this piece's); a build that stops at the
    decision (ticks == 1) fails ticks > decided_tick. Red today: verdict None."""
    eng = oracle_engine()
    r = fight(hand(("Interceptor", 0), ("Vanguard", 2)), 0, False, engine=eng)
    assert eng.first.get(("decided", 0)) == 1, eng.first
    assert (r.outcome, r.winner, verdict_of(r), decided_tick_of(r)) == ("side0", "side0", DECIDED, 1), (r.outcome, r.ticks)
    assert r.ticks > decided_tick_of(r) and r.survivors[1] == 0, "the fight was stopped at tick %d; it must play on to elimination" % r.ticks


def test_a_mutual_no_reach_scene_on_the_real_engine_stalls_at_the_first_tick():
    """R7 on the real library: Vanguards on layer 0 and on layer 2. Red today: the cap (3000 ticks)."""
    eng = oracle_engine()
    r = fight(hand(("Vanguard", 0), ("Vanguard", 2)), 0, False, engine=eng)
    assert eng.first.get("mutual") == 1, eng.first
    assert r.ticks == 1, "ran %d ticks (outcome %s), the oracle saw the stall at tick 1" % (r.ticks, r.outcome)
    assert (r.outcome, r.winner, verdict_of(r)) == (STALL, None, STALL)


def test_control_reach_both_ways_on_the_real_engine_is_an_ordinary_fight():
    """Green today and after: Raiders on layer 1 against Raiders on layer 0 reach each other (1, 1): no verdict, the oracle never fires, and
    the fight ends the way fights end (a win, no tag)."""
    eng = oracle_engine()
    r = fight(hand(("Raider", 1), ("Raider", 0), types={"Raider": {"base": "Raider", "reach": (1, 1)}}), 0, False, engine=eng)
    assert eng.first == {}
    assert r.outcome in ("side0", "side1") and verdict_of(r) is None and decided_tick_of(r) is None


# --------------------------------------------------------------------------------------------- the real range_up scenes (OM_LAB_SLOW)

def scene(play, role, point, heads, swap, max_ticks=None):
    features = sweep.smoke_layouts()["192"]
    return sweep.Applied(sweep.default_builds(play, role, features), point, max_ticks)(heads, swap)


@SLOW
@pytest.mark.parametrize("play", ["s3_layer_above", "s3_types_by_reach"])
def test_the_null_control_scene_ends_as_no_reach_stall_when_what_is_left_cannot_reach(play):
    """T9, D7: reach (0, 0) for every type (the null control's build). Red today: outcome cap at 4000 (the oracle's mutual moment is before it)."""
    eng = oracle_engine()
    r = fight(scene(play, "reach_zero", sweep._vision(0.5), 16, False, max_ticks=4000), 0, False, engine=eng)
    assert "mutual" in eng.first, "precondition: the oracle never saw a mutual no-reach moment (%s)" % (eng.first,)
    assert r.ticks == eng.first["mutual"], "outcome %s at tick %d; the oracle saw nobody able to reach anybody at tick %d" % (
        r.outcome, r.ticks, eng.first["mutual"])
    assert (r.outcome, r.winner, verdict_of(r)) == (STALL, None, STALL)


# RETIRED positive control (Architect's named fight, FINDING-lab-d11 first trace): s3_types_by_reach, range_up 0.25, 20 side-1 heads, SEED 1, swap
# False, survivors (1, 3), capped at 12000, the survivor untouchable from tick 7411. It was measured on the LAB-REV2-L8M tip b35c4576. After
# LAB-REV2-L8M2 (decision 50: a side that is shot at but out of range re-engages) the same fight ends side 1 at tick 5932 with no decided moment
# (the oracle never fires), so it is no longer a positive control; it stays in this file only as this comment, and test_control_the_same_scene_
# without_a_decided_moment_is_an_ordinary_win below keeps seed 1 as a negative control. The stand-in is SEED 2, below.
STAND_IN = {False: (5554, 7281), True: (4466, 5469)}      # swap -> (oracle's decided tick, elimination tick), measured 2026-10-20


@SLOW
@pytest.mark.parametrize("swap", [False, True])
def test_the_decided_one_way_fight_is_recorded_at_its_first_tick_and_plays_on_to_elimination(swap):
    """FINDING-lab-d11 positive control (stand-in seed 2; see the comment above and the module docstring). Architect ruling 2026-10-20, supersedes
    the stop: the decision is RECORDED at the oracle's tick and the fight plays on to the elimination the base reaches.
    PREMISE DUMP (measured 2026-10-20 on this tree, one fight per process, oracle_engine().first read after the fight):
        swap False: outcome side0 by elimination at tick 7281, survivors (3, 0), first = {("decided", 0): 5554}
        swap True : outcome side0 by elimination at tick 5469, survivors (5, 0), first = {("decided", 0): 4466}
    Asserted (the sim is deterministic and recording changes nothing in it): verdict decided_one_way_reach, decided_tick 5554 / 4466, side 0
    wins by elimination at tick 7281 / 5469 (ticks 1727 / 1003 after the decision). The precondition fails loudly if a later tree stops showing
    the moment, so the seed gets re-picked, not the assertion weakened. Red today: verdict None, decided_tick None (the elimination is the same)."""
    eng = oracle_engine()
    r = fight(scene("s3_types_by_reach", "play", sweep._range_up(0.25), 20, swap), 2, swap, engine=eng)
    decided_at, ended_at = STAND_IN[swap]
    assert eng.first.get(("decided", 0)) == decided_at, "precondition: the oracle's decided tick is %s, expected %d; re-pick the seed" % (eng.first, decided_at)
    assert (r.outcome, r.winner, r.ticks) == ("side0", "side0", ended_at), (r.outcome, r.ticks)
    assert (verdict_of(r), decided_tick_of(r)) == (DECIDED, decided_at)


@SLOW
@pytest.mark.parametrize("seed", [0, 1])
def test_control_the_same_scene_without_a_decided_moment_is_an_ordinary_win(seed):
    """FINDING-lab-d11 negative control (b), unchanged by the ruling of 2026-10-20: same setup, swap False, seeds 0 and 1: no decided moment, so
    an ordinary win, never a cap, no tag. Green today."""
    eng = oracle_engine()
    r = fight(scene("s3_types_by_reach", "play", sweep._range_up(0.25), 20, False), seed, False, engine=eng)
    assert not any(k != "mutual" and k[0] == "decided" for k in eng.first), "precondition: the oracle saw a decided moment (%s)" % (eng.first,)
    assert r.outcome in ("side0", "side1"), (r.outcome, r.ticks)
    assert verdict_of(r) is None and decided_tick_of(r) is None


@SLOW
def test_control_reach_allowed_out_of_range_row_ends_by_reengage_with_no_tag():
    """FINDING-lab-d11 negative control (c), decision 50: s3_layer_above, range_up 0.25, 48 side-1 heads, seed 1, swap True. The reach table
    allows the hit (13 enemies have reach (1, 1) though out of effective range): the structural verdicts are not due. The fight ends by the
    re-engage of the side shot at (reengage[1] >= 1) and is not a cap. Green today."""
    eng = oracle_engine()
    r = fight(scene("s3_layer_above", "play", sweep._range_up(0.25), 48, True), 1, True, engine=eng)
    assert eng.first == {}, "precondition: the oracle fired (%s)" % (eng.first,)
    assert r.outcome != "cap" and r.reengage[1] >= 1, (r.outcome, r.ticks, r.reengage)
    assert verdict_of(r) is None and decided_tick_of(r) is None
