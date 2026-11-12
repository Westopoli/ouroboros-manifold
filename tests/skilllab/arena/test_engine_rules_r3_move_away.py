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

Re-dumped 2026-11-12 on the Round 3 tip (d70c8d47): 737 ticks; flinch flag on unit 13 only, 87 unit-ticks, one run (ticks 182 to 268), no stall; the lab checker reports no violation of any rule. In the
flinch the unit has no destination (the recorder's `dest` is None), so the stall detector below is blind to a fixed unit by construction and sees only the old state, a destination ordered by the
pursuit-end check and a unit that stands: that is what the red test judged and what the fake-tick control proves it reads.
"""
import contextlib
import ctypes
import math
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
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
def played(name="L-0081", seed=1):
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


def test_control_L0081_runs_to_the_measured_end_and_unit_13_flinches():
    """Control (the premise of the red test; re-dumped 2026-11-12 on the Round 3 tip d70c8d47, Test-defect: the premises were dumped on the engine before the fixes): L-0081 seed 1 sight on runs
    737 ticks (2,560 before; fix 3, 8f825d59, moves it to 831 and fix 2, 94da7493, to 737; d70c8d47 leaves it); the only unit that ever carries the flinch flag is unit 13, on 87 unit-ticks in one run from
    tick 182 to tick 268, with no destination while it moves away, and it ends the run 196 wu from where it began (R-087-01 'moves 200 wu directly away', the step is 2 wu a tick), so the move
    away is made and is not a run on the spot; at tick 269 the attack-mover has its destination back."""
    rec, flinch = played()
    assert len(rec.ticks) == 737, len(rec.ticks)
    units = {u for d in flinch for u, v in d.items() if v}
    assert units == {13}, units
    ticks = [n + 1 for n, d in enumerate(flinch) if d.get(13)]
    assert ticks == list(range(182, 269)), (ticks[0], ticks[-1], len(ticks))
    p0, p1 = rec.ticks[181]["pre"][13], rec.ticks[267]["post"][13]
    assert 190.0 < math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"]) < 200.0
    assert rec.ticks[268]["post"][13]["dest"] is not None


# ------------------------------------------------------------------ red today

def test_R_087_01_no_unit_stands_still_with_a_destination_and_no_target_for_over_40_ticks_in_its_move_away_L0081():
    """R-087-01 'it moves 200 wu directly away from the damage direction and stops, and an attack-mover then resumes its attack-move toward its original point' (a unit in its move away moves): on L-0081 seed 1
    sight on, no walker is flinching with a destination and no target within 2 wu of the same spot for more than DRAFT-inv-stalled-ticks 40 ticks in a row. Red today: unit 13, 3 runs, from ticks 254, 621
    and 967, 355, 198 and 1,374 ticks long. Break that turns it red: the engine as it is on main 7ba38983 (csrc/unit.c om_tactical_ai_tick calls om_tac_end_pursuit while `flinching` is set)."""
    rec, flinch = played()
    got = stalls_in_move_away(rec.ticks, flinch, rec.ids)
    assert not got, "stalls in a move away (unit, first tick, ticks): %s" % got
