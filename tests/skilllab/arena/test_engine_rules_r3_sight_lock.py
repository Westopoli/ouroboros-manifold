# Rule pins: R-087-03, R-087-08, R-093-02
"""Engine rules round 3, T9 item 1: a lock lost one tick early, to a sight check made on half-moved positions. The whole-run proof on the lab fight where it was traced.

Rules, word for word (docs/bible/epics/E-11-units-and-combat.md):
  R-087-03  "... the target is a lock: the unit keeps it, whatever else comes nearer, until the target dies, leaves its side's sight, or the player gives the unit a new order; only then
            does it retarget the nearest enemy its side can see ..."
  R-087-08  "Given target acquisition, When it runs, Then each unit validates its lock every tick (R-087-03) and acquires only while it has no lock ..."
E-12 R-093-02 is the sight the lock is judged by: the side's visible set (`om_player_can_see`), which the oracle reads at the end of every tick.

Trace (engine-rules-baseline/x2/log1.txt, repro1.py): L-0084 seed 1, sight on. At lab tick 1776 the guards 29 to 40 (all of side A, hold:A) drop target 71. Side A sees 71 at the end of
tick 1775 and at the end of tick 1776 (`om_player_can_see(0, 71)` 1 and 1), and first does not after tick 1777. The only observers that see 71 are guards 12 and 13; in a guard's AI turn
unit 12 (lower id) has already stepped this tick and unit 71 (stepping later) has not, and that mixed pair is blocked by terrain ("why 4" in the fog log) although both whole-tick
states are clear. The engine tests the side's sight of the target inside the guard's own AI turn; a lock must end when the target leaves the side's sight, that is, on the tick the
sight is gone, not on a tick where the side still sees it before and after.

THE MEASURE (a test-local oracle, built like tests/skilllab/arena/engine_rules_oracle.py; it does not import scripts/skilllab/invariants.py): on every tick n, a living unit that held a
living target t at the end of tick n-1 and holds another target (or none) at the end of tick n, while its side sees t both at the end of n-1 and at the end of n, has DROPPED a target
it still sees. Dropped for a reason of another rule is excused, each excuse the rule's own text and measured from engine state:
  reach       R-164-02 / R-008-04: the target is outside the unit's layer reach (up 0, down 1 in the lab's stage 4) at either end of the tick.
  give-up     R-087-09: "if it finds none within 1 s (20 ticks) it drops the target": the unit could not shoot the target (om_combat_can_shoot 0) at the end of each of the 19 ticks before.
  guard post  R-096-08: a guard "returning to the post ... when engaging it would take the guard past the radius": the slant distance from the guard's post (where it stood at tick 0) to the
              target, taken on the state before the tick, is over GUARD_RADIUS + attack range x the layer-offset multiplier (DRAFT-guard-radius 200 wu, csrc/unit.c om_tac_guard_engageable).
The leash (R-087-05) and a new order are not needed on this fight (measured: neither excuses a single drop).

Premises dumped 2026-11-11 on this tree (main 7ba38983, run.fight(L-0084, seed 1, sight "on", CAP_SECONDS)): 3,718 ticks; 760 drops of a target seen at both ends, of which reach 118,
give-up 162, guard post 468, and 12 unexplained, all at tick 1776: units 29 to 40 (every one a guard holding 71 since tick 1775 or earlier), units 29, 33 and 37 retarget to 95 in the same
tick, the other nine to none. Side A sees 71 (`om_player_can_see(0, 71)`) 1 at the end of tick 1775, 1 at the end of 1776, 0 at the end of 1777.

Red today: the 12 unexplained drops. After the engine fix the guards drop 71 at tick 1778 (the tick after the side stops seeing it), not 1776.

Re-dumped 2026-11-12 on the Round 3 tip (d70c8d47; Test-defect: the control's premises were the fight before the fix): L-0084 seed 1 sight on is 3,923 ticks (fix 1, d70c8d47, moves it from 3,718;
fixes 2 and 3 leave it). The episode is one tick later: side A sees 71 at the end of ticks 1776 and 1777 and not at the end of 1778; guards 29 to 40 hold it through the end of 1778 and drop it
at 1779 (29, 33 and 37 to none, 40 to 95). Drops of a target seen at both ends of the tick: 748, of which reach 118, give-up 157, guard post 473, unexplained 0. The lab checker reports no violation
of any rule on the fight.
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

GIVEUP_TICKS = 19          # R-087-09: 20 ticks of not shooting; the 20th is the tick the engine drops on (the checker counts one frame less, scripts/skilllab/invariants.py STUCK_TICKS - 1)
GUARD_RADIUS = 200.0       # R-096-08 (DRAFT-guard-radius, Westley's)
SIGHT_LAG_TICKS = 1        # R-087-03 + R-087-08 "validates its lock every tick": a target unseen at the end of tick n is dropped on tick n or n + 1 (DRAFT-lock-lag-ticks)
SIDE_A = 0                 # hold:A, the guards


class Rec:
    """The oracle's recording of one fight plus what it needs beyond engine_rules_oracle.Recorder: can_shoot at the end of every tick, the layer heights and the reach table (read while the world lives)."""

    def __init__(self, rec, shoot, heights, up, down, reach):
        self.rec, self.shoot, self.heights, self.up, self.down, self.reach = rec, shoot, heights, up, down, reach
        self.post = {u: (rec.ticks[0]["pre"][u]["x"], rec.ticks[0]["pre"][u]["y"]) for u in rec.ids if rec.side[u] == SIDE_A}   # an order moves nobody: the post is where it stood at tick 0

    def mult(self, la, lb):
        return 1.0 if la == lb else ((self.up if lb > la else self.down)[abs(lb - la)] if abs(lb - la) <= 4 else 1.0)

    def in_reach(self, u, a, b):
        up, down = self.reach[u]
        return a == b or (b - a <= up if b > a else a - b <= down)


@contextlib.contextmanager
def recording_with_shots(extra):
    """oracle.recording() plus a per-tick can_shoot(unit, its target) and the static tables, read while the world is alive."""
    orig = oracle.Recorder.step

    def step(self, o):
        eng, w, lib = self.eng, self.w, self.eng._lib
        if not extra:
            lib.om_terrain_band_heights.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
            lib.om_terrain_band_heights.restype = ctypes.c_uint32
            buf = (ctypes.c_double * 8)()
            n = lib.om_terrain_band_heights(w, buf, 8)
            extra["heights"] = list(buf)[:n]
            extra["up"] = [1.0] + [eng.get_param(w, eng.param_id("OM_TP_RANGE_UP_%d" % k)) for k in range(1, 5)]
            extra["down"] = [1.0] + [eng.get_param(w, eng.param_id("OM_TP_RANGE_DOWN_%d" % k)) for k in range(1, 5)]
            extra["reach"] = {u: eng.profile_reach(w, self.typ[u]) for u in self.ids}
            extra["shoot"] = []
        orig(self, o)
        post = self.ticks[-1]["post"]
        extra["shoot"].append({u: bool(lib.om_combat_can_shoot(w, u, post[u]["tgt"])) for u in self.ids if post[u]["alive"] and post[u]["tgt"]})

    oracle.Recorder.step = step
    try:
        yield
    finally:
        oracle.Recorder.step = orig


@lru_cache(maxsize=None)
def played(name="L-0084", seed=1):
    extra = {}
    with recording_with_shots(extra):
        with oracle.recording() as recs:
            run.fight(oracle.catalogue(name), seed, "on", CAP_SECONDS, 100000)
    return Rec(oracle.only(recs), extra["shoot"], extra["heights"], extra["up"], extra["down"], extra["reach"])


def _unshot(r, n, u, t):
    """Consecutive ticks up to n-1 on which u held t and could not shoot it."""
    k = 0
    for m in range(n - 1, 0, -1):
        if r.rec.ticks[m - 1]["post"][u]["tgt"] == t and r.shoot[m - 1].get(u) is False:
            k += 1
        else:
            break
    return k


def drops_of_a_seen_target(r):
    """[(tick, unit, target, new target, reason)]: every tick a unit stopped holding a living target its side saw at both ends of the tick; reason is the excuse or None."""
    rec, out = r.rec, []
    for tk in rec.ticks:
        n, pre, post = tk["n"], tk["pre"], tk["post"]
        for u in rec.ids:
            p0, p1, t = pre[u], post[u], pre[u]["tgt"]
            if not (p0["alive"] and p1["alive"] and t and p1["tgt"] != t and post[t]["alive"]):
                continue
            s = rec.side[u]
            if not (tk["vis_pre"].get((s, t)) and tk["vis_post"].get((s, t))):
                continue
            q0, q1 = pre[t], post[t]
            why = None
            if not (r.in_reach(u, p0["layer"], q0["layer"]) and r.in_reach(u, p1["layer"], q1["layer"])):
                why = "reach"
            elif _unshot(r, n, u, t) >= GIVEUP_TICKS:
                why = "give-up"
            elif u in r.post:
                la, lb = p0["layer"], q0["layer"]
                dz = r.heights[lb] - r.heights[la]
                limit = GUARD_RADIUS + rec.stats[rec.typ[u]]["attack_range"] * r.mult(la, lb)
                if math.hypot(math.hypot(q0["x"] - r.post[u][0], q0["y"] - r.post[u][1]), dz) > limit:
                    why = "guard post"
            out.append((n, u, t, p1["tgt"], why))
    return out


def unexplained(r):
    return [d[:4] for d in drops_of_a_seen_target(r) if d[4] is None]


# ------------------------------------------------------------------ green first: the premises

def test_control_the_fight_and_the_trace_premises_hold():
    """Control (green after the fix, the premise of the red test below): the recorded fight is the one traced (re-dumped on the Round 3 tip; the premise before the fix was 3,718 ticks and tick 1775
    to 1777). 3,923 ticks; side A (the guards 1 to 40) sees enemy 71 at the end of ticks 1776 and 1777 and not at the end of tick 1778; guards 29 to 40 all hold 71 at the end of tick 1777; the oracle finds
    drops of a seen target for each of its three excuses and none unexplained (so a red below is not a detector that excuses nothing: a fix that dropped a lock early would add an unexplained one)."""
    r = played()
    rec = r.rec
    assert len(rec.ticks) == 3923, len(rec.ticks)
    assert [rec.ticks[n - 1]["vis_post"][(SIDE_A, 71)] for n in (1776, 1777, 1778)] == [True, True, False]
    assert all(rec.ticks[1776]["post"][u]["tgt"] == 71 for u in range(29, 41)), {u: rec.ticks[1776]["post"][u]["tgt"] for u in range(29, 41)}
    assert [rec.side[u] for u in range(1, 41)] == [SIDE_A] * 40
    reasons = {}
    for d in drops_of_a_seen_target(r):
        reasons[d[4]] = reasons.get(d[4], 0) + 1
    assert set(reasons) == {"reach", "give-up", "guard post"}, reasons
    assert reasons == {"reach": 118, "give-up": 157, "guard post": 473}, reasons


def held_after_sight_loss(r, lag):
    """([(tick n, unit, target)], number of cases): a unit held a living target at the end of tick n-1, its side no longer sees it at the end of tick n, and the unit still holds it at the end of tick n + lag."""
    rec, late, cases = r.rec, [], 0
    for tk in rec.ticks:
        n = tk["n"]
        if n + lag > len(rec.ticks):
            continue
        for u in rec.ids:
            t = tk["pre"][u]["tgt"]
            if not (t and tk["pre"][u]["alive"] and tk["post"][u]["alive"] and tk["post"][t]["alive"]) or tk["vis_post"].get((rec.side[u], t)):
                continue
            cases += 1
            nxt = rec.ticks[n + lag - 1]
            if nxt["post"][u]["alive"] and nxt["post"][t]["alive"] and nxt["post"][u]["tgt"] == t:
                late.append((n, u, t))
    return late, cases


def test_R_087_03_control_a_target_that_leaves_the_sight_is_dropped_within_two_ticks():
    """R-087-03 'until the target ... leaves its side's sight' + R-087-08 'validates its lock every tick' (control, green today and after): on L-0084 seed 1, whenever a unit holds a living target at the
    end of tick n-1 and its side no longer sees it at the end of tick n, the unit does not hold it at the end of tick n+2 (DRAFT-lock-lag-ticks-measured 2, the worst the engine does today, see the
    next test). Proves the fight has such cases and that a lock does drop when the sight goes, so a fix that never drops turns it red."""
    late, cases = held_after_sight_loss(played(), 2)
    assert cases > 0, "scene broken: no unit ever held a target that left its side's sight"
    assert not late, "locks held a target 3 ticks after the side stopped seeing it: %s" % late[:5]


# ------------------------------------------------------------------ red today

def test_R_087_03_no_unit_drops_a_target_its_side_sees_at_the_end_of_the_previous_tick_and_of_this_tick_L0084():
    """R-087-03 'the target is a lock: the unit keeps it ... until the target dies, leaves its side's sight, or the player gives the unit a new order' + R-087-08 'validates its lock every tick' +
    E-12 R-093-02 (the side's visible set): on L-0084 seed 1 sight on, no unit stops holding a living target on a tick where its side sees that target both at the end of the previous tick and at
    the end of this tick, unless another rule ends the lock (reach R-164-02, give-up R-087-09, guard post R-096-08: the oracle's excuses above). Red today: guards 29 to 40 drop enemy 71 at tick 1776, the
    tick before its side loses sight of it (the sight check is made inside the guard's AI turn on a mixed state: the observer 12 has stepped, the target has not). Break that turns it red: the engine as it
    is on main 7ba38983 (csrc/unit.c, om_tac_guard_tick and om_tac_unit_ai call om_tac_may_act_on on live mid-tick positions); the fix that turns it green tests the sight the tick began with."""
    bad = unexplained(played())
    assert not bad, "%d drops of a target the side still sees at both ends of the tick (tick, unit, target, new target): %s" % (len(bad), bad[:12])


def test_R_087_03_a_target_that_leaves_the_sight_is_dropped_on_that_tick_or_the_next_L0084():
    """R-087-03 'until the target ... leaves its side's sight' + R-087-08 'validates its lock every tick' (brief: 'dropped on that tick or the next', DRAFT-lock-lag-ticks 1): on L-0084 seed 1, a unit
    that held a living target at the end of tick n-1 and whose side does not see it at the end of tick n does not hold it at the end of tick n+1. Red today, the same defect the other way round:
    units 33, 39 and 40 still hold enemy 93 at the end of tick 1754 (unseen from the end of tick 1753; the sight check inside the AI turn sees the target on a mixed state) and drop it at 1755. The fix
    that judges the sight the tick began with (the end of the tick before) drops it at 1754."""
    late, cases = held_after_sight_loss(played(), 1)
    assert cases > 0
    assert not late, "%d locks still held one tick after the side lost sight (tick, unit, target): %s" % (len(late), late[:6])
