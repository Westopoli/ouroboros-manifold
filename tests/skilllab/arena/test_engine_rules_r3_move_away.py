# Rule pins: R-087-01, R-096-02
"""Engine rules round 3, T9 item 4, whole fight: a unit in its move away from unseen fire does not stand still with a destination and no target.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01): "Given an idle or attack-moving unit with no target that takes damage from an attacker it cannot see or cannot reach, When the
loop runs, Then it leaves the line of fire instead of standing or walking on blindly: it moves 200 wu directly away from the damage direction and stops, and an attack-mover then resumes its
attack-move toward its original point (R-096-02) ... An attack-mover that had already arrived at its point holds where the move away ends and does not walk back into the fire ...".
Trace: engine-rules-baseline/x1/slope_pileup.md (item 2): csrc/unit.c om_tactical_ai_tick ends the pursuit (om_tac_end_pursuit commands a move to the order point) while the unit is still flinching; the
two steps cancel and the unit stands. The csim twin is tests/csim/test_E11_R087_01_move_away_completes.py.

THE MEASURE (a test-local oracle; the engine's own flag): a run is the longest stretch of consecutive ticks on which a living unit is in a move away (`om_unit_in_flinch` 1 at the end of the tick), has a
destination (the recorder's `dest`), has no target, and ends the tick within STALL_RADIUS 2 wu of where the run began; a run longer than DRAFT-inv-stalled-ticks 40 ticks is a stall.
Premises dumped 2026-11-11 on this tree (main 7ba38983), run.fight(L-0081, seed 1, sight "on", CAP_SECONDS), the sweep's configuration:
  2,560 ticks (a silence end); 2,159 unit-ticks with the flinch flag, all of unit 13; the sweep's I29 (walker with a destination, no target, moved under 0.5 wu, more than 40 ticks, counted past 40) 29,134
  unit-ticks, of which only unit 13's are in a move away; stalls while flinching: unit 13, 3 runs, starting at ticks 254, 621 and 967, 355, 198 and 1,374 ticks long (1,927 unit-ticks over 40).
  The remaining 27,000 or so unit-ticks of I29 are units stood still with no flinch flag on the tick (not traced here: the x1 notes name an arrived member pushed back by its own formation, kind 3);
  they are not asserted here and are reported to the Architect.
Red today: unit 13's three runs.

Re-dumped 2026-11-12 on the Round 3 tip (d70c8d47): 737 ticks (741 on the Round 4 tip 6d3d7635, R-097-10: an idle unit steps aside for a mover of its own side; the lab checker reports no violation of any rule on it, seed 1 sight on, and the flinch run is unchanged); flinch flag on unit 13 only, 87 unit-ticks, one run (ticks 182 to 268), no stall; the lab checker reports no violation of any rule. In the
flinch the unit has no destination (the recorder's `dest` is None), so the stall detector below is blind to a fixed unit by construction and sees only the old state, a destination ordered by the
pursuit-end check and a unit that stands: that is what the red test judged and what the fake-tick control proves it reads.

Re-dumped 2026-11-17 on the Round 5 tip: 2750 ticks (1577 on the second-pass tip fd342241c, where only unit 40 carries the flinch flag, ticks 1180 to 1233, 199.38 wu); the flinch flag was carried by units 34 (ticks 1120 to 1170) and 40 (ticks 1180 to 1230) only, both idle, 200 wu away and holding; unit 13, an attack-mover on its way,
is not moved by unseen fire any more (R-087-01 as ruled 2026-11-17), so the Round 3 run of unit 13 is gone and the stall detector reads nothing in the fight.

Re-anchored 2026-11-18 on the Round 6 tip (Test-defect: the control's fight changed with Round 6; orders are kept through the pause after a shot, R-096-02, so no idle unit of L-0081 is hit by unseen fire any
more): L-0081 seed 1 sight on has 1921 ticks, no tick with the flinch flag, and four unseen hits (ticks 140, 849, 879, 909), all on attack-movers on their way (units 47 and 34). The move-away of an idle unit is
now read on L-0080 seed 1 sight on (1540 ticks, a wipe, 25 survivors): units 46, 23 and 44, the only ones with the flag, one run each (ticks 334 to 381, 965 to 1039, 972 to 1038), every one of them a unit whose
order had ended (46: the give-up of R-099-05 at tick 311, after two unseen hits at ticks 285 and 309 on the attack-move, which went on) and which was hit again, idle, afterwards. L-0083 (13 units in 13
runs) and L-0061 (no run) were looked at the same way; L-0080 is the one the round 5 file names for it (`MOVE_AWAY_LAYOUTS`, tests/skilllab/arena/test_engine_rules_r5_unseen_fire.py). L-0081's whole-run
tests stay as the second case: its attack-movers are the exempt ones.
"""
import contextlib
import ctypes
import math
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
import engine_rules_unseen_oracle as unseen  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402

STALLED_TICKS = 40         # DRAFT-inv-stalled-ticks (the coordinator's number; the sweep's I29 uses the same 40)
STALL_RADIUS = 2.0


def stalls_in_move_away(ticks, flinch, ids, radius=STALL_RADIUS, limit=STALLED_TICKS):
    """[(unit, first tick, length)]: runs of more than `limit` consecutive ticks on which the unit is flinching, has a destination, no target, and stays within `radius` of the run's first position."""
    out, cur = [], {}
    for tk, fl in zip(ticks, flinch):
        for u in ids:
            p = tk["post"][u]
            if p["alive"] and fl.get(u) and p["dest"] is not None and not p["tgt"]:
                c = cur.get(u)
                if c is not None and math.hypot(p["x"] - c[1], p["y"] - c[2]) <= radius:
                    c[3] += 1
                    continue
                if c is not None and c[3] > limit:
                    out.append((u, c[0], c[3]))
                cur[u] = [tk["n"], p["x"], p["y"], 1]
            else:
                c = cur.pop(u, None)
                if c is not None and c[3] > limit:
                    out.append((u, c[0], c[3]))
    out += [(u, c[0], c[3]) for u, c in cur.items() if c[3] > limit]
    return sorted(out)


@contextlib.contextmanager
def recording_with_flinch(flinch):
    orig = oracle.Recorder.step

    def step(self, o):
        orig(self, o)
        lib, w = self.eng._lib, self.w
        lib.om_unit_in_flinch.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.om_unit_in_flinch.restype = ctypes.c_int
        flinch.append({u: lib.om_unit_in_flinch(w, u) for u in self.ids if self.ticks[-1]["post"][u]["alive"]})

    oracle.Recorder.step = step
    try:
        yield
    finally:
        oracle.Recorder.step = orig


@lru_cache(maxsize=None)
def played(name, seed=1):
    flinch = []
    with recording_with_flinch(flinch):
        with oracle.recording() as recs:
            run.fight(oracle.catalogue(name), seed, "on", CAP_SECONDS, 100000)
    return oracle.only(recs), flinch


# ------------------------------------------------------------------ the detector against made-up ticks (green today)

def _fake(move_per_tick, n=120, flinching=True, dest=(1000.0, 1000.0), tgt=0):
    ticks = [{"n": k, "post": {1: {"alive": True, "x": 500.0 + move_per_tick * k, "y": 500.0, "dest": dest, "tgt": tgt}}} for k in range(1, n + 1)]
    return ticks, [{1: 1 if flinching else 0} for _ in ticks]


def test_control_the_measure_flags_a_flinching_unit_that_stands_and_not_one_that_walks_or_holds_a_target():
    """Control (green today): 120 ticks of a flinching unit with a destination and no target standing still is one stall of 120; the same unit walking 4 wu a tick, not flinching, or holding a
    target is none. Proves the detector reads what the test below needs it to read."""
    t, f = _fake(0.0)
    assert stalls_in_move_away(t, f, [1]) == [(1, 1, 120)]
    assert stalls_in_move_away(*_fake(4.0), [1]) == []
    assert stalls_in_move_away(*_fake(0.0, flinching=False), [1]) == []
    assert stalls_in_move_away(*_fake(0.0, tgt=7), [1]) == []
    assert stalls_in_move_away(*_fake(0.0, dest=None), [1]) == []


def test_control_L0081_runs_to_the_measured_end():
    """Control (the premise of the red test; re-dumped 2026-11-12 on the Round 3 tip d70c8d47, Test-defect: the premises were dumped on the engine before the fixes): L-0081 seed 1 sight on runs
    741 ticks (2,560 before; fix 3, 8f825d59, moves it to 831 and fix 2, 94da7493, to 737; d70c8d47 leaves it; Round 4, 6d3d7635, R-097-10: 741, checker reports none; Test-defect). Round 5 (G1 to G5
    and the later fixes of the second pass) moved the length to 1577 ticks on the branch tip fd342241c (re-pinned 2026-11-17, Test-defect: the lab checker reports no violation of any rule on the new run, seed 1 sight on). Round 6 moved it to 1921 ticks (re-pinned 2026-11-18, Test-defect: R-096-02, an order kept through the pause after the unit's own shot, 66fbc1ee9: first different
    tick 142, unit 3 keeps its destination where main's engine cleared it; wipe, survivors 0 and 42)."""
    rec, flinch = played("L-0081")
    assert len(rec.ticks) == 1921, len(rec.ticks)


def test_control_L0081_the_attack_movers_hit_by_unseen_fire_are_neither_moved_nor_stopped():
    """Control (second case of the file; Round 6, Test-defect: the control's fight changed with Round 6, the idle unit of the earlier premise is no longer hit): R-087-01 'An attack-moving unit still on its way to its point
    is neither moved nor stopped by such a hit: it keeps walking its attack-move'. L-0081 seed 1 sight on has exactly four unseen hits (the test-local oracle's definition: a fire event on a unit with no target,
    from an attacker its side sees neither before nor after the tick): ticks 140 (victim 47, by 3), 849, 879 and 909 (victim 34, by 2). Each victim has its destination on the tick of the hit and keeps the
    same one on every tick from two before to three after it, holds no target, walks 4.0 wu on each of those ticks (not stopped), and no unit of the fight carries the flinch flag on any tick (not moved)."""
    rec, flinch = played("L-0081")
    hits = unseen.unseen_hits(rec)
    assert [(n, v, a) for n, v, a, _, _ in hits] == [(140, 47, 3), (849, 34, 2), (879, 34, 2), (909, 34, 2)], hits
    assert not any(v for d in flinch for v in d.values()), {u for d in flinch for u, v in d.items() if v}
    for n, u, _, _, _ in hits:
        assert rec.ticks[n - 1]["pre"][u]["dest"] is not None, (n, u)
        dests = {rec.ticks[k - 1]["post"][u]["dest"] for k in range(n - 2, n + 4)}
        assert len(dests) == 1 and None not in dests, (n, u, dests)
        assert not any(rec.ticks[k - 1]["post"][u]["tgt"] for k in range(n - 2, n + 4)), (n, u)
        for k in range(n - 2, n + 4):
            a, b = rec.ticks[k - 1]["post"][u], rec.ticks[k - 2]["post"][u]
            assert abs(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) - 4.0) < 0.01, (n, u, k)


def test_control_L0080_runs_to_the_measured_end():
    """Control (the premise of the tests below; dumped 2026-11-18 on the Round 6 tip): L-0080 seed 1 sight on runs 1540 ticks, the lab's cap not reached (a wipe; 25 survivors)."""
    rec, flinch = played("L-0080")
    assert len(rec.ticks) == 1540, len(rec.ticks)


MOVE_AWAY_SHORT = 5.0       # DRAFT-move-away-short: how far under 200 wu the straight line may end (a hill slows the step and curves the path; measured 196.63, 198.03, 199.45 on L-0080)
MOVE_AWAY_LONG = 200.5      # the earlier bound of this file: the unit does not go further than 200 wu and half a wu
# L-0080 seed 1 sight on, dumped 2026-11-18: unit -> (first and last tick with the flinch flag, tick on which its order ended by the give-up (R-099-05), the unseen hits on it)
L0080_MOVE_AWAY = {
    46: (334, 381, 311, [285, 309, 333]),
    23: (965, 1039, 963, [500, 866, 867, 939, 964, 965, 973, 980, 1002]),
    44: (972, 1038, 971, [941, 966, 970, 971, 971]),
}


def test_control_L0080_the_move_away_is_made_by_idle_units_and_ends_where_it_holds():
    """Control (the premise of the red test; re-anchored 2026-11-18 on L-0080, Test-defect: the control's fight changed with Round 6, L-0081 has no idle unit hit by unseen fire any more): R-087-01 'an idle unit
    ... that takes damage from an attacker it cannot see ... moves 200 wu directly away from the damage direction and stops, and it holds where the move away ends'. In L-0080 seed 1 sight on the units that ever
    carry the flinch flag are 46, 23 and 44, each in one run (46: ticks 334 to 381, 48 ticks; 23: 965 to 1039, 75; 44: 972 to 1038, 67). Each is a unit whose order had ended by the give-up (46 at tick 311, 23 at 963,
    44 at 971: it has its destination before and none after, and holds no target), so on the first tick of the run it is idle (no destination and no target at the start of the tick, none during the run); the flag
    does not go up on any earlier tick of the fight (46 is hit at ticks 285 and 309 on its attack-move and keeps its destination, it is not moved; its first hit once idle is 333); each ends its run 196.6 (46), 198.0
    (23) and 199.4 (44) wu from where it began, within MOVE_AWAY_SHORT of the 200 wu of the rule and not past 200.5, so the move away is made and is not a run on the spot, and holds there: no destination and no
    target on the tick after the run."""
    rec, flinch = played("L-0080")
    units = {u for d in flinch for u, v in d.items() if v}
    assert units == set(L0080_MOVE_AWAY), units
    hits = unseen.unseen_hits(rec)
    for u, (first, last, gave_up, hit_ticks) in sorted(L0080_MOVE_AWAY.items()):
        ticks = [n + 1 for n, d in enumerate(flinch) if d.get(u)]
        assert ticks == list(range(first, last + 1)), (u, ticks[0], ticks[-1], len(ticks))
        assert [n for n, v, _, _, _ in hits if v == u] == hit_ticks, (u, [n for n, v, _, _, _ in hits if v == u])
        # the order ends by the give-up, before the run: a destination up to the tick before, none from that tick on, and the flag is down until the run
        assert rec.ticks[gave_up - 2]["post"][u]["dest"] is not None and rec.ticks[gave_up - 1]["post"][u]["dest"] is None, (u, gave_up)
        assert not any(flinch[k - 1].get(u) for k in range(1, first)), u
        before, after = rec.ticks[first - 1]["pre"][u], rec.ticks[last]["post"][u]
        assert before["dest"] is None and not before["tgt"], (u, before)
        assert all(rec.ticks[k - 1]["post"][u]["dest"] is None and not rec.ticks[k - 1]["post"][u]["tgt"] for k in range(first, last + 1)), u
        p1 = rec.ticks[last - 1]["post"][u]
        reach = math.hypot(p1["x"] - before["x"], p1["y"] - before["y"])
        assert 200.0 - MOVE_AWAY_SHORT < reach < MOVE_AWAY_LONG, (u, p1, before, reach)
        assert after["dest"] is None and not after["tgt"], (u, after)
    # an attack-mover on its way is neither moved nor stopped: unit 46's hits at ticks 285 and 309 find its destination and leave it
    for n in (285, 309):
        assert rec.ticks[n - 1]["pre"][46]["dest"] is not None and rec.ticks[n - 1]["pre"][46]["dest"] == rec.ticks[n]["post"][46]["dest"], n


# ------------------------------------------------------------------ red today

def test_R_087_01_no_unit_stands_still_with_a_destination_and_no_target_for_over_40_ticks_in_its_move_away_L0081():
    """R-087-01 'it moves 200 wu directly away from the damage direction and stops, and an attack-mover then resumes its attack-move toward its original point' (a unit in its move away moves): on L-0081 seed 1
    sight on, no walker is flinching with a destination and no target within 2 wu of the same spot for more than DRAFT-inv-stalled-ticks 40 ticks in a row. Red today: unit 13, 3 runs, from ticks 254, 621
    and 967, 355, 198 and 1,374 ticks long. Break that turns it red: the engine as it is on main 7ba38983 (csrc/unit.c om_tactical_ai_tick calls om_tac_end_pursuit while `flinching` is set)."""
    rec, flinch = played("L-0081")
    got = stalls_in_move_away(rec.ticks, flinch, rec.ids)
    assert not got, "stalls in a move away (unit, first tick, ticks): %s" % got


def test_R_087_01_no_unit_stands_still_with_a_destination_and_no_target_for_over_40_ticks_in_its_move_away_L0080():
    """R-087-01 (text as above), the same measure on L-0080 seed 1 sight on, the fight whose three units are in a move away (test_control_L0080_the_move_away_is_made_by_idle_units_and_ends_where_it_holds,
    re-anchored 2026-11-18, Test-defect: the control's fight changed with Round 6): 190 unit-ticks of the flag on three units (46, 23, 44: 48, 75 and 67), none with a destination or a target in the run, so the measure
    finds no stall and, as in L-0081, is blind to a fixed unit by construction; the state it reads (a flinching unit with a destination) is the old one. Break that turns it red: the engine as on main 7ba38983."""
    rec, flinch = played("L-0080")
    assert sum(1 for d in flinch for v in d.values() if v) == 48 + 75 + 67
    got = stalls_in_move_away(rec.ticks, flinch, rec.ids)
    assert not got, "stalls in a move away (unit, first tick, ticks): %s" % got
