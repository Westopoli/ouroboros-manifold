# Rule pins: R-097-10, R-097-03, R-097-05, DEC-Q087-02-2026-10-22
"""Engine rules round 4, T10, whole fights: a walker with a destination is not held for ever by a unit of its own side that stands idle in its way.

Rule word for word (docs/bible/epics/E-13-movement-and-command.md, R-097-10): "Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0
and the other takes the full displacement, except that an idle unit (no move target, not engaged) takes the full displacement from a mover of its own side and none from an enemy mover, which takes
all of it; given both are stationary and either was displaced earlier in the tick, they split the displacement equally. ..." and R-097-03: "... it probes 40 wu ahead; if a unit on its layer blocks
the probe (an idle unit of its own side does not block: idle means no move target and not engaged; an enemy always does) ...". Owner's words behind them, DEC-Q087-02-2026-10-22 (decisions.md):
"Idle own units are not walls: a moving unit passes through idle units of its own side, which step aside (soft collision), as in the reference RTS".
Trace: engine-rules-baseline/x3/findings.txt, section I29: in `om_move_collide_pair` (csrc/tactical_move.c) a pair with one stationary unit gives the mover the whole push, so a walker whose way (or
whose destination) lies in a ring of arrived own units takes its step and is pushed back to the same spot every tick, for the rest of the fight (L-0028 sight on 12,655 sweep unit-ticks; sight off 10,833,
all one unit, 18; control 6,496; L-0045 control 9,280). The route never fails. The single geometries are tests/csim/test_E13_R097_10_idle_own_units_yield.py.

THE MEASURE (a test-local oracle, not the checker's I29; DRAFT numbers are Westley's): a run is the longest stretch of consecutive ticks on which a living unit has a destination, has no target, ends the
tick within STALL_RADIUS 2 wu of where the run began, AND an idle unit of its own side (alive, no destination, no target, same layer) stands within IDLE_NEAR 35 wu of it at the end of that tick;
a run longer than STALLED_TICKS 40 ticks (DRAFT-inv-stalled-ticks, the sweep's number) is a stall. A guard is not read specially: no catalogue layout used here orders a guard (orders default
both_same_point).

Configuration: `run.fight(layout, seed 1, sight, CAP_SECONDS, 100000)`, the lab's own runner: walking units, the layout's boxes, the sweep's three sight settings. Nothing is switched off except where a test
says "sight off" (stage 3's rule set, which the sweep also ran).

Premises dumped 2026-11-12 on this tree (main e2dcee93, the unfixed engine), seed 1, CAP_SECONDS 600: see the control test docstrings; the numbers there are what the dump printed.
"""
import contextlib
import math
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.arena.snapshot import CAP_SECONDS  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

RULE = "R-097-10"
STALLED_TICKS = 40         # DRAFT-inv-stalled-ticks (the coordinator's number; the sweep's I29 uses the same 40)
STALL_RADIUS = 2.0         # the sweep's I29: "stood < 0.5 wu per tick"; 2 wu over the run, as the round 3 oracle
IDLE_NEAR = 35.0           # DRAFT-idle-near: 30 wu is the collision diameter, the sweep's ring was 30.0 to 31.8 wu; 35 is a little beyond


class Walk:
    """Per tick, per unit, the rows the measure reads: alive, x, y, layer, target, destination. Light: no sight, no shots, no cells."""

    def __init__(self, eng, w):
        self.eng, self.w = eng, w
        self.ids, self.side = [], {}
        for (wa, f), us in eng._own.items():
            if wa == w.value:
                for u in us:
                    self.ids.append(u)
                    self.side[u] = f
        self.ids.sort()
        self.ticks = []          # one dict per step: n, post {unit: row}

    def snap(self):
        eng, w = self.eng, self.w
        out = {}
        for u in self.ids:
            alive = eng.unit_alive(w, u)
            x, y = eng.unit_pos(w, u)
            out[u] = {"alive": alive, "x": x, "y": y, "layer": int(eng.unit_layer(w, u)), "tgt": eng.unit_target(w, u), "dest": eng.unit_destination(w, u) if alive else None}
        return out

    def step(self, orig):
        orig(self.eng, self.w)
        self.ticks.append({"n": len(self.ticks) + 1, "post": self.snap()})


@contextlib.contextmanager
def walking():
    recs = {}
    orig = Engine.step

    def step(self, w):
        rec = recs.get(w.value)
        if rec is None:
            rec = recs[w.value] = Walk(self, w)
        rec.step(orig)

    Engine.step = step
    try:
        yield recs
    finally:
        Engine.step = orig


@lru_cache(maxsize=None)
def played(name, sight, seconds=CAP_SECONDS):
    with walking() as recs:
        frames, last, end, orders = run.fight(oracle.catalogue(name), 1, sight, seconds, 100000)
    assert len(recs) == 1, "expected the fight to step exactly one world, got %d" % len(recs)
    return next(iter(recs.values())), last, end


def _idle_own_near(post, side, u, p, near):
    for o, q in post.items():
        if o != u and q["alive"] and q["dest"] is None and not q["tgt"] and side[o] == side[u] and q["layer"] == p["layer"] \
                and math.hypot(q["x"] - p["x"], q["y"] - p["y"]) <= near:
            return True
    return False


def stalls_beside_idle_own(ticks, side, ids, radius=STALL_RADIUS, limit=STALLED_TICKS, near=IDLE_NEAR):
    """[(unit, first tick, length)]: runs of more than `limit` consecutive ticks on which the unit has a destination, no target, stays within `radius` of the run's first position and has an idle unit
    of its own side within `near` wu."""
    out, cur = [], {}
    for tk in ticks:
        post = tk["post"]
        for u in ids:
            p = post[u]
            if p["alive"] and p["dest"] is not None and not p["tgt"] and _idle_own_near(post, side, u, p, near):
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


def _stalls(rec):
    return stalls_beside_idle_own(rec.ticks, rec.side, rec.ids)


def _unit_ticks(stalls, limit=STALLED_TICKS):
    return sum(n for _, _, n in stalls)


# ------------------------------------------------------------------ the detector against made-up ticks (green today)

def _fake(n=120, step=0.0, tgt=0, other_dest=None, other_side=0, other_dx=30.0, other_tgt=0, dest=(1000.0, 1000.0)):
    ticks = []
    for k in range(1, n + 1):
        ticks.append({"n": k, "post": {
            1: {"alive": True, "x": 500.0 + step * k, "y": 500.0, "layer": 0, "tgt": tgt, "dest": dest},
            2: {"alive": True, "x": 500.0 + other_dx + step * k, "y": 500.0, "layer": 0, "tgt": other_tgt, "dest": other_dest}}})
    return ticks, {1: 0, 2: other_side}


def test_control_the_measure_flags_a_walker_that_stands_beside_an_idle_own_unit_and_nothing_else():
    """Control (green today): a walker with a destination and no target standing still 120 ticks beside an idle unit of its own side 30 wu away is one stall of 120. The same walker is none when it walks
    4 wu a tick, holds a target, has an enemy beside it, has the neighbour 40 wu away (beyond IDLE_NEAR), or the neighbour has a destination or a target of its own (not idle). Proves the detector reads what
    the red tests need it to read."""
    t, s = _fake()
    assert stalls_beside_idle_own(t, s, [1]) == [(1, 1, 120)]
    assert stalls_beside_idle_own(*_fake(step=4.0), [1]) == []
    assert stalls_beside_idle_own(*_fake(tgt=7), [1]) == []
    assert stalls_beside_idle_own(*_fake(other_side=1), [1]) == []
    assert stalls_beside_idle_own(*_fake(other_dx=40.0), [1]) == []
    assert stalls_beside_idle_own(*_fake(other_dest=(5.0, 5.0)), [1]) == []
    assert stalls_beside_idle_own(*_fake(other_tgt=9), [1]) == []


# ------------------------------------------------------------------ the premises (green today)

def test_control_L0039_sight_on_runs_and_the_measure_finds_no_stall():
    """Control (green today; the layout where the measure is 0 today): L-0039 seed 1 sight on is a fight the oracle can judge (it has units of both sides, a wipe, a few hundred ticks) and
    the measure finds no stall in it. Dumped 2026-11-12 on main e2dcee93: 2,314 ticks, end "wipe", 0 stalls. Layouts L-0046, L-0057 and L-0081 (sight on) are also 0 there, so a red below is not the
    detector tripping on every fight."""
    rec, last, end = played("L-0039", "on")
    assert last > 300 and end == "wipe", (last, end)
    assert {rec.side[u] for u in rec.ids} == {0, 1}
    assert _stalls(rec) == [], _stalls(rec)[:6]


def test_control_L0028_unit_18_is_a_side_one_walker_and_the_fight_is_long_enough_to_stall():
    """Control (the premise of the red tests; dumped 2026-11-12 on main e2dcee93, seed 1): L-0028 has unit 18 on side 1 (the sweep's 'side B Vanguard'), and the sight-off fight runs the 12,000 ticks of
    CAP_SECONDS (a cap end), the sight-on one 7,160 (a silence end). On this tree the measure finds, sight on: 33 runs / 13,077 unit-ticks, units 5, 8, 9, 10, 11, 12, 27; sight off: 1 run, unit 18 from tick
    1127, 10,874 unit-ticks (the sweep's I29 counted 12,655 and 10,833 past the 40th tick of each run); control: 49 runs / 7,627, units 5, 7, 8, 10, 11, 12, 17, 24, 26, 27; L-0045 control: 41 runs /
    10,840, units 63, 65, 66, 74, 75, 76, 80, 83, 84, 87, 88 (sweep 9,280). Only the layout, the side and a long fight are asserted: the counts change when the engine does."""
    rec, last, end = played("L-0028", "off")
    assert rec.side[18] == 1
    assert last > 2000, (last, end)


# ------------------------------------------------------------------ the rule, whole fights (red today)

def _assert_no_stall(name, sight):
    rec, last, end = played(name, sight)
    st = _stalls(rec)
    assert st == [], "%s sight %s: %d runs of more than %d ticks, %d unit-ticks, units %s, first %s" % (name, sight, len(st), STALLED_TICKS, _unit_ticks(st), sorted({u for u, _, _ in st}), st[:4])


def test_R_097_10_L0028_sight_on_no_walker_stands_beside_an_idle_own_unit_for_more_than_40_ticks():
    """R-097-10: "... an idle unit (no move target, not engaged) takes the full displacement from a mover of its own side and none from an enemy mover, which takes all of it ..." and R-097-03 "(an idle
    unit of its own side does not block: ...)". A walker with a destination and no target that an idle own unit stands next to is moved past it (the idle unit steps aside), so it does not stand within 2 wu of the
    same spot for more than 40 ticks. L-0028 seed 1 sight on: 13,077 unit-ticks in 33 runs today (units 5, 8, 9, 10, 11, 12, 27; unit 5 alone 2,852 ticks from tick 4309)."""
    _assert_no_stall("L-0028", "on")


def test_R_097_10_L0028_sight_off_no_walker_stands_beside_an_idle_own_unit_for_more_than_40_ticks():
    """R-097-10 (text as above), L-0028 seed 1 sight off, the sweep's second setting: one unit, 18, a side B Vanguard, stands from tick 1127 to the 12,000-tick cap at (6497.9, 6006.4) with a destination 92 wu
    away, pushed back every tick by its own idle units 23, 26 and 27 at 30.0, 30.0 and 31.8 wu: 10,874 unit-ticks today. Stage 3's rule set (targeting by sight off) is the setting the sweep ran."""
    _assert_no_stall("L-0028", "off")


def test_R_097_10_L0028_control_no_walker_stands_beside_an_idle_own_unit_for_more_than_40_ticks():
    """R-097-10 (text as above), L-0028 seed 1 control (stage 4's rules with targeting by sight off, the sweep's third setting): 49 runs, 7,627 unit-ticks, ten units, today."""
    _assert_no_stall("L-0028", "control")


def test_R_097_10_L0045_control_no_walker_stands_beside_an_idle_own_unit_for_more_than_40_ticks():
    """R-097-10 (text as above), L-0045 seed 1 control: a crowd of side 1 survivors converges on its slots and the late ones are held by the arrived ones: 41 runs, 10,840 unit-ticks, eleven units, today
    (the sweep's I29 counted 9,280). The slope plays no part (x3 findings)."""
    _assert_no_stall("L-0045", "control")
