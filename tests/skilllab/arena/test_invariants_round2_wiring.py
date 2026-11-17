# Rule pins: R-087-03, R-087-04, R-087-09, R-093-02, R-004-06
"""Engine rules round 2, T3: the checker (the shipped Monitor, through arena/run.py::fight) on real catalogue fights, walkers, obstacles, sight on.

Pure predicates and the API: tests/skilllab/test_invariants_nearest.py, _visible.py, _tightened.py. Premises dumped by running the fights (Round 1 tip 81be98cd,
nothing changes with the seed on these layouts):
  L-0039 seed 10 sight on: 2314 ticks; acquisitions 60 = 54 nearest + 6 return fire (2 on the cohort turn, 4 off it, 4 of the 6 by splash), 0 unexplained; 30 of the 60 are
      beyond the unit's own sensor radius (Bombard, Bastion); R-093-02: 551 shots and 22,110 held-target ticks, 0 outside the previous frame's visible set;
      continuity: 4 unit-ticks above max speed + 1.3 wu, all beside a unit, none above by more than 0.1 wu: 0 under the new rule.
  L-0061 sight on: 1693 ticks; acquisitions 761 all explained; R-093-02: 0 in 1947 shots; continuity under the new rule: 538 unit-ticks (629 over max speed + slack,
      all beside a unit; today the checker reports 0). Recorded here, not asserted: it stays red-by-design until the engine fix F8 lands.
  L-0046 sight on: R-087-09 reports 230 held-target stalls today; 23 of them are out of attack range (unit 68, range 300, at 383 wu).
"""
import math
import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402


@lru_cache(maxsize=None)
def played(name, seed=10, sight="on"):
    """(monitor, recorder) of one whole catalogue fight through run.fight; the Monitor is the shipped one, the recorder the independent oracle."""
    made, orig = [], invariants.Monitor

    class Cap(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    invariants.Monitor = Cap
    try:
        with oracle.recording() as recs:
            run.fight(oracle.catalogue(name), seed, sight, CAP_SECONDS, 100000)
    finally:
        invariants.Monitor = orig
    return made[0], oracle.only(recs)


def of(mon, rule):
    return [v for v in mon.violations if v["rule"] == rule]


def test_control_the_monitor_runs_a_whole_real_fight_and_reads_its_suspensions():
    """Control (green today): L-0039 seed 10 sight on runs to its end through the shipped Monitor; sight on suspends nothing (2211 ticks; 2314 before Round 5, re-pinned after G1 to G5, the lab checker reports no violation of any rule on the new run)."""
    mon, rec = played("L-0039")
    assert mon.tick == len(rec.ticks) == 2211 and mon.suspended == {}


@pytest.mark.parametrize("name", ["L-0039", "L-0061"])
def test_R_087_03_every_acquisition_is_the_nearest_or_return_fire(name):
    """R-087-03 'it targets the nearest such enemy', R-087-06 return fire, R-087-08 cohort turn: over the whole fight the Monitor reports no R-087-03 violation
    (L-0039 seed 10: 60 acquisitions = 54 nearest + 6 return fire; green today because only swaps are checked; it must stay green once acquisitions are)."""
    mon, _ = played(name)
    assert of(mon, "R-087-03") == []


def test_R_087_03_the_report_says_which_rules_are_judged_in_this_run():
    """The Monitor's checker knows the nine rules and suspends none with sight on."""
    mon, _ = played("L-0039")
    assert mon.suspended == {} and "R-093-02" in invariants.RULES


@pytest.mark.parametrize("name", ["L-0039", "L-0061"])
def test_R_093_02_no_shot_and_no_held_target_is_outside_the_sides_visible_set(name):
    """R-093-02 'the target is in its side's visible set': over the whole fight with sight on, zero violations (L-0039: 551 shots, 22,110 held-target ticks)."""
    mon, _ = played(name)
    assert of(mon, "R-093-02") == [] and "R-093-02" not in mon.suspended


def test_R_093_02_the_monitor_flags_a_planted_unseen_target(monkeypatch):
    """R-093-02 on the real engine: Engine.unit_target reports, on tick 10 only, the farthest living enemy of side 0's first unit as its target (nobody sees across
    the field at tick 10). Red today: no such check."""
    real = Engine.unit_target
    real_step, state = Engine.step, {"n": 0, "unit": None, "far": None}

    def step(self, w):
        real_step(self, w)
        state["n"] += 1
        if state["n"] == 10:
            own = sorted(self._own[(w.value, 0)])
            foes = sorted(self._own[(w.value, 1)])
            state["unit"] = own[0]
            ux, uy = self.unit_pos(w, own[0])
            state["far"] = max(foes, key=lambda e: math.hypot(self.unit_pos(w, e)[0] - ux, self.unit_pos(w, e)[1] - uy))

    def reported(self, w, u):
        t = real(self, w, u)
        return state["far"] if state["n"] == 10 and u == state["unit"] else t
    monkeypatch.setattr(Engine, "step", step)
    monkeypatch.setattr(Engine, "unit_target", reported)
    made, orig = [], invariants.Monitor

    class Cap(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    monkeypatch.setattr(invariants, "Monitor", Cap)
    run.fight(oracle.catalogue("L-0039"), 10, "on", 3, 100000)
    mon = made[0]
    assert [(v["tick"], v["unit"]) for v in of(mon, "R-093-02")][:1] == [(10, state["unit"])], mon.violations[:3]


def test_R_087_09_the_monitor_reports_no_stall_outside_the_units_attack_range():
    """R-087-09 'a target within its attack range whose line of fire is blocked': every R-087-09 violation of L-0046 (sight on) has its target within the
    unit's attack range at that tick. Red today: 23 of 230 are out of range (unit 68, range 300, target at 383 wu)."""
    mon, rec = played("L-0046", 1)
    out = []
    for v in of(mon, "R-087-09"):
        post = rec.ticks[v["tick"] - 1]["post"]
        u = v["unit"]
        t = post[u]["tgt"]
        d = math.hypot(post[u]["x"] - post[t]["x"], post[u]["y"] - post[t]["y"])
        if d > rec.stats[rec.typ[u]]["attack_range"] + 1e-6:
            out.append((v["tick"], u, t, round(d)))
    assert out == [], "%d out of range, first %s" % (len(out), out[:3])


def test_continuity_control_L0039_has_no_leap_even_beside_a_friend():
    """continuity (R-004-08: a unit that changes layer does not jump; a same-layer push beside a unit is not judged): L-0039 seed 10 has 4 unit-ticks over max speed + slack,
    all within 0.1 wu and beside a unit: 0 violations (green today and after)."""
    mon, _ = played("L-0039")
    assert of(mon, "continuity") == []


def test_R_087_04_no_acquisition_is_beyond_the_units_notice_distance():
    """R-087-04 (current text): "When an enemy its side can see ... is within its notice distance, Then it acquires the nearest such enemy ... The notice distance is the unit's own attack range
    plus a margin of one tenth of that range (`DRAFT-notice-margin`) ... It is never the sensor radius: an enemy the side sees beyond the notice distance is not acquired" (R-087-06: a target
    taken by return fire is not judged). Replaces the strict xfail that pinned the old words "within its sensor radius" (Test-defect, ruling of 2026-11-17: acquire within attack range, never the
    sensor radius). L-0039 seed 10 sight on, per tick through the independent oracle: no pick of an enemy that stood beyond the notice distance in the state before the step. Red today for
    Bombard and Bastion, whose sensor radius is the larger and which the engine lets acquire out to it."""
    mon, rec = played("L-0039")
    bad = oracle.picks_beyond_notice(rec)
    assert not bad, "%d picks beyond the notice distance (%d units), first %s" % (len(bad), len({b[1] for b in bad}), bad[:3])


def test_R_087_04_control_the_oracle_sees_picks_in_this_fight():
    """Control (green today): L-0039 seed 10 has more than 50 acquisitions (the premise above: 60), so a zero count above means the picks stayed inside the distance, not that none happened."""
    mon, rec = played("L-0039")
    picks = sum(1 for tk in rec.ticks for u in rec.ids if tk["pre"][u]["alive"] and tk["post"][u]["alive"] and tk["post"][u]["tgt"] and tk["post"][u]["tgt"] != tk["pre"][u]["tgt"])
    assert picks > 50, picks
