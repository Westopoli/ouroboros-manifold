# Rule pins: R-087-09
"""Round 6, the lab checker's R-087-09 judges by the engine's own give-up count (`scripts/skilllab/invariants.py` `_held`; engine: `om_tac_giveup`, csrc/unit.c).

R-087-09 (docs/bible/epics/E-11-units-and-combat.md), word for word: "Given an idle or attack-moving unit with a target within its attack range whose line of
fire is blocked by units, cover or ground, When evaluated, Then it steers around the blockers by the probe of blocked movement (R-097-03) until it reaches a spot
with a clear line, and if it finds none within 1 s (20 ticks) it drops the target and acquires another (...)."

THE ENGINE'S COUNT, as read from `om_tac_giveup` and as logged by the tracer (r6-t2: GU lines of the lc3 build) on the two fights below:
  - Each tick, a unit that holds a target it cannot shoot counts one tick. The run (target, ref, count) restarts when the target is another one, or when the
    distance to it is more than 1 wu below `ref`, the distance when the current run began (`dist < ref - 1.0`); a restart sets ref to that distance and the count
    to 0 before the tick is counted. A shootable target clears the run. The 20th counted tick drops the target.
  - The engine reads positions at the top of its tick: the positions the PREVIOUS frame ended with. A target taken during tick M is counted on tick M itself,
    with the distance of frame M-1. So the count belonging to frame M (the frame that shows the target held) is made of the distances of frames M-1, M-2, ...:
    at frame M, x(M) = distance between the unit and the target in frame M-1; the run restarts when x(M) < ref - 1, and the count is the number of frames since.
  - The run does not care about the attack range; it counts from the tick the target was first held unshootable.
THE CHECKER, so: it counts as above, on the previous frame's distances, from the frame the target is first shown; it reports on the frame whose count passes 20
(the 21st counted frame), once per run, and only on a frame where the target is within the unit's attack range (the rule's own words; the tests in
test_invariants_tightened.py pin that part and stay as they are). "A hold of exactly 20 counted ticks is not reported and 21 is."
Not tested here, left as the builder finds it: what the checker does when the previous frame has no row for the unit (the target is taken on frame 1).

Ruling (Round 6 brief, Westley): "the checker judges R-087-09 by the engine's own definition of the count, exactly: the engine's anchor and restart rule, on the
distances the engine saw (the previous frame's positions). No slack tick is added."

Planted frames (pure checker, only R-087-09): unit 1 stands at (100, 100), enemy 2 at (100 + D(k), 100) in frame k, frame 0 holds no target, frames 1..n hold enemy
2, never shootable. The real sequences are the two fixtures in giveup_count_frames.json, cut from the fights the tracer followed (seed 1, sight on, the lab's run):
L-0057 unit 24 (range 250, target 12, the engine dropped it at tick 393; the checker reported tick 391) and L-0046 unit 21 (range 800, target 115, the engine
dropped it at tick 1633; the checker reported tick 1632). The engine's counts there, from the GU log: L-0046 run restarts on ticks 1604, 1606, 1610, 1614, count 20 on
tick 1633; L-0057 run restarts on tick 374 (the first reading 248.06 wu), count 20 on tick 393.
Whole fights, same judge: tests/skilllab/arena/test_engine_rules_f5_giveup.py (unchanged; it turns green when the checker is right).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_invariants import _Module, row, rules, trace  # noqa: E402,F401

FIXTURES = json.loads((Path(__file__).resolve().parent / "giveup_count_frames.json").read_text())


@pytest.fixture(scope="module")
def inv():
    return _Module()


def _planted(inv, dists, held, rng=500.0, enemy=2, shootable=False):
    """R-087-09 violations (tick, unit) of unit 1 holding enemy 2 in frames 1..held, the enemy standing `dists[k]` wu from it in frame k (frame 0 has no target)."""
    frames = [{1: row(100, 100), 2: row(100 + dists(0), 100, side=1)}]
    for k in range(1, held + 1):
        frames.append({1: row(100, 100, target=enemy, shootable=shootable), 2: row(100 + dists(k), 100, side=1)})
    rep = inv.check(trace(*frames), rules(inv, attack_range={1: rng}), only=["R-087-09"])
    return [(v["tick"], v["unit"]) for v in rep.violations]


# ------------------------------------------------------------------ the 20 / 21 line

@pytest.mark.parametrize("held,expected", [(20, []), (21, [(21, 1)]), (30, [(21, 1)])], ids=["20-ticks-silent", "21-ticks-flagged", "30-ticks-flagged-once"])
def test_R_087_09_control_twenty_counted_ticks_are_silent_and_the_twenty_first_is_flagged(inv, held, expected):
    """R-087-09, control (green today): the target stands still 400 wu away inside range 500, unshootable; held 20 frames: no report; the 21st: one report, on that
    frame; held on to 30: still the one report."""
    assert _planted(inv, lambda k: 400.0, held) == expected


# ------------------------------------------------------------------ the anchor

def test_R_087_09_the_count_starts_where_the_engines_run_starts_not_where_the_unit_enters_range(inv):
    """R-087-09, the engine's anchor: the run began on frame 1 (the target stood 300.9 wu away, range 300, so out of range), and from frame 11 it stands 299.95 wu
    away, in range (0.95 wu nearer: no restart). The engine has counted 21 ticks on frame 21: reported there. A counter anchored where the unit first has it in
    range counts 11 on frame 21 and reports on frame 31."""
    assert _planted(inv, lambda k: 300.9 if k <= 10 else 299.95, 40, rng=300.0) == [(21, 1)]


def test_R_087_09_the_first_reading_of_a_new_run_is_the_previous_frames(inv):
    """R-087-09, the engine reads the top of its tick: the target was taken on frame 1 and the engine's first reading is frame 0's 400 wu; frame 1's 398.9 wu is
    1.1 wu nearer: the run restarts on frame 2 (count 1) and its 21st count is frame 22. A count anchored on frame 1's own distance never restarts and reports on frame 21."""
    assert _planted(inv, lambda k: 400.0 if k == 0 else 398.9, 40) == [(22, 1)]


# ------------------------------------------------------------------ the restart, on the previous frame's distances

def test_R_087_09_closing_in_by_more_than_one_wu_restarts_the_count_one_frame_after_the_closing(inv):
    """R-087-09, the restart on previous-frame distances: 400 wu through frame 15, 398.5 wu from frame 16 (1.5 nearer). The engine reads 398.5 on frame 17 and
    restarts there, its 21st count is frame 37. A checker reading the frame's own distance restarts on frame 16 and reports on frame 36 (the stale-frame effect)."""
    assert _planted(inv, lambda k: 400.0 if k <= 15 else 398.5, 45) == [(37, 1)]


def test_R_087_09_control_creeping_closer_restarts_against_the_runs_start_not_the_last_frame(inv):
    """R-087-09, control (green today): the target comes 0.4 wu nearer every frame for 60 frames. Each restart's ref is the distance the run began at, so the run
    restarts every third frame (1.2 wu below ref) and never reaches 21: silent. A checker that compared with the last frame (0.4 wu) would report on frame 21."""
    assert _planted(inv, lambda k: 400.0 - 0.4 * k, 60) == []


def test_R_087_09_control_a_new_target_a_clear_line_or_a_unit_closing_in_starts_over(inv):
    """R-087-09, control (green today): 15 frames on enemy 2, then 15 on enemy 4, both 400 wu away and unshootable: silent. The same with enemy 2 for 15 frames,
    3 shootable frames, 15 more unshootable: silent (a shootable target clears the run)."""
    frames = [{1: row(100, 100), 2: row(500, 100, side=1), 4: row(500, 140, side=1)}]
    for k in range(1, 31):
        frames.append({1: row(100, 100, target=2 if k <= 15 else 4, shootable=False), 2: row(500, 100, side=1), 4: row(500, 140, side=1)})
    assert inv.check(trace(*frames), rules(inv, attack_range={1: 500.0}), only=["R-087-09"]).violations == []
    frames = [{1: row(100, 100), 2: row(500, 100, side=1)}]
    for k in range(1, 34):
        frames.append({1: row(100, 100, target=2, shootable=not 16 <= k <= 18), 2: row(500, 100, side=1)})
    assert inv.check(trace(*frames), rules(inv, attack_range={1: 500.0}), only=["R-087-09"]).violations == []


# ------------------------------------------------------------------ the two real sequences

def _frames(key, repeat_last_from=None, extra=0):
    """The fixture's frames as a trace; with `repeat_last_from`, the frame of that tick is repeated on `extra` further ticks (the engine's give-up taken out)."""
    fix = FIXTURES[key]
    out = []
    for f in fix["frames"]:
        out.append({"tick": f["tick"], "units": {int(i): dict(r) for i, r in f["units"].items()}, "fires": []})
    if repeat_last_from is not None:
        keep = [f for f in out if f["tick"] <= repeat_last_from]
        last = keep[-1]
        for n in range(1, extra + 1):
            keep.append({"tick": last["tick"] + n, "units": {i: dict(r) for i, r in last["units"].items()}, "fires": []})
        out = keep
    return out, fix


def _judge(inv, key, **kw):
    frames, fix = _frames(key, **kw)
    rep = inv.check(frames, rules(inv, attack_range={fix["unit"]: fix["attack_range"]}), only=["R-087-09"])
    return [(v["tick"], v["unit"]) for v in rep.violations if v["unit"] == fix["unit"]]


@pytest.mark.parametrize("key,last_held", [("L-0057", 392), ("L-0046", 1632)])
def test_R_087_09_control_the_fixtures_hold_the_target_to_the_frame_before_the_engines_give_up(key, last_held):
    """Premise of the fixtures (green today): the unit holds one unshootable target on every frame up to `last_held`, and the next frame shows none; the fixture is
    the engine's own give-up (tick 393 for L-0057 unit 24, tick 1633 for L-0046 unit 21)."""
    fix = FIXTURES[key]
    by_tick = {f["tick"]: f["units"][str(fix["unit"])] for f in fix["frames"]}
    held = by_tick[last_held]
    assert held["target"] != 0 and held["shootable"] is False
    assert by_tick[last_held + 1]["target"] == 0


@pytest.mark.parametrize("key,gave_up_on", [("L-0057", 393), ("L-0046", 1633)])
def test_R_087_09_the_engines_own_give_up_on_its_20th_counted_tick_is_not_reported(inv, key, gave_up_on):
    """R-087-09, the two real sequences: the engine counted 20 ticks and dropped the target (tick 393, tick 1633, from its GU log); the checker reports nothing. Red
    today: it reports 'unshootable for 21 ticks' on tick 391 (L-0057 unit 24) and tick 1632 (L-0046 unit 21)."""
    assert _judge(inv, key) == []


@pytest.mark.parametrize("key,last_held", [("L-0057", 392), ("L-0046", 1632)])
def test_R_087_09_control_the_same_sequence_with_the_give_up_taken_out_is_reported(inv, key, last_held):
    """R-087-09, control (green today): the last held frame repeated for 5 more ticks (the unit keeps the target past the engine's 20th count): the checker
    reports unit's R-087-09."""
    assert _judge(inv, key, repeat_last_from=last_held, extra=5) != []


@pytest.mark.parametrize("key,last_held,reported", [("L-0057", 392, 394), ("L-0046", 1632, 1634)])
def test_R_087_09_the_real_sequence_held_on_is_reported_on_the_engines_21st_counted_tick(inv, key, last_held, reported):
    """R-087-09, the two real sequences with the give-up taken out: the engine's count is 19 on the last held frame (it counted 20 on the next tick and dropped);
    held on, the 20th count (frame last_held + 1) is silent and the 21st (frame last_held + 2: tick 394 / tick 1634) is the one report. Red today: reported on
    tick 391 / 1632, before the engine's own count could reach 21."""
    got = _judge(inv, key, repeat_last_from=last_held, extra=5)
    assert [t for t, _ in got] == [reported], got
