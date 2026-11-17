# Rule pins: R-087-01, R-087-06, R-096-02, R-005-09
"""Engine rules round 5, G4, whole fights in the lab configuration: an attack-mover still on its way is neither moved nor stopped by unseen fire; a unit that has moved away holds and is not moved again without a new hit.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01, as it reads on the Round 5 branch): "Given an idle unit, or an attack-moving unit that has arrived at its point, with no target, that takes
damage from an attacker it cannot see or cannot reach, When the loop runs, Then it leaves the line of fire instead of standing in it: it moves 200 wu directly away from the damage direction and stops, and it holds
where the move away ends; it does not walk back into the fire (Westley, 2026-11-17 ...). While it holds it acquires and returns fire as any idle unit does (R-087-04, R-087-06), and a repeat hit it still cannot answer
moves it again. An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit: it keeps walking its attack-move (Westley, 2026-11-17: "them starting to be shot at does not stop their
attack move" ...). A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit ... a unit that holds a target is not moved (DEC-engine-rules-round2-2026-11-11)."
round5.md G4 whole-run: "no walker with an attack-move destination stands still under unseen fire, and no unit moves away more than once without a new hit."

The single geometries are tests/csim/test_E11_R087_01_attack_mover_not_stopped_by_unseen_fire.py and test_E11_R087_01_unseen_attacker_moves_the_unit.py. The judge here is a test-local oracle on a recorder of the
fight (engine_rules_oracle.Recorder, plus the engine's own flag `om_unit_in_flinch` read after every step); it does not use scripts/skilllab/invariants.py (the checker predicate of G7 is the lab builder's, tested
beside it). Every assertion is made on the fight's frames, tick by tick.

Configuration: `run.fight(layout, seed 1, sight "on", 600 simulated seconds)`: the lab's stage 4 rule set (walking units, the layout's hills and boxes, targeting by sight on, reach 0 up 1 down, nothing switched off),
run to the lab's cap. Layouts: L-0061 (vantage 24:24, hold:A: blue holds the hill, red attack-moves across the flat under fire from it) and L-0080 (trap 16:32, groups: red attack-moves out of a pocket under fire from
three hill forces); both catalogue layouts as they stand on this branch.

THE MEASURES (DRAFT numbers are Westley's):
  moved_away_on_its_way   a tick on which the engine's flag for "in a move away" goes up for a unit that had a destination (an attack-move on its way) and no target at the start of the tick: the rule says it
                          is neither moved nor stopped. A unit with no destination at the start of the tick (idle, or an attack-mover that has arrived) is the unit the rule moves.
  stood_under_unseen_fire a walker with a destination and no target that stays within STAND_RADIUS DRAFT-r5-stand-radius 2 wu of where the run began for more than STAND_TICKS DRAFT-inv-stalled-ticks 40
                          consecutive ticks while an enemy its side does not see hits it (an unseen hit within HIT_GAP DRAFT-f9-hit-gap 60 ticks of the tick).
  repeated_away_no_hit    a unit that begins a move away (flag 0 to 1) when no hit has landed on it since the start of its previous one.
  walked_back_into_fire   after a move away ends (flag 1 to 0) the unit has a destination, or moves under its own power (more than OWN_MOVE 0.5 wu, no unit within PUSH_RADIUS 40 wu), before it takes a target,
                          is hit again, or dies: "it holds where the move away ends; it does not walk back into the fire".
"""
import contextlib
import ctypes
import math
import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
import engine_rules_unseen_oracle as unseen  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402

SECONDS = 600               # the lab's cap (12,000 ticks), as test_engine_rules_f9_unseen_fire.py
MIN_TICKS = 300
STAND_RADIUS = 2.0          # DRAFT-r5-stand-radius
STAND_TICKS = 40            # DRAFT-inv-stalled-ticks (the sweep's number)
HIT_GAP = 60                # DRAFT-f9-hit-gap
OWN_MOVE = oracle.OWN_MOVE
PUSH_RADIUS = oracle.PUSH_RADIUS
LAYOUTS = ["L-0061", "L-0080"]
MOVE_AWAY_LAYOUTS = ["L-0080"]      # layouts where idle or arrived units are hit by unseen fire: on L-0061 every victim is an attack-mover on its way (Round 5)


# ------------------------------------------------------------------ the recorder: the oracle's rows plus the engine's own move-away flag

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
def played(name):
    flinch = []
    with recording_with_flinch(flinch):
        with oracle.recording() as recs:
            run.fight(oracle.catalogue(name), 1, "on", SECONDS, 100000)
    rec = oracle.only(recs)
    assert len(rec.ticks) >= MIN_TICKS, "scene broken: %s ran %d ticks" % (name, len(rec.ticks))
    assert len(flinch) == len(rec.ticks)
    return rec, flinch


# ------------------------------------------------------------------ the measures (functions of the recorded ticks, so they can be run on made-up ticks)

def _starts(flinch, ids):
    """[(tick index, unit)] where a unit's flag goes 0 to 1 (tick index k is rec.ticks[k], the tick the flag is read at the end of)."""
    out, prev = [], {}
    for k, row in enumerate(flinch):
        for u in ids:
            now = row.get(u, 0)
            if now and not prev.get(u, 0):
                out.append((k, u))
            prev[u] = now
    return out


def moved_away_on_its_way(ticks, flinch, ids):
    """[(tick, unit)]: the move away begins for a unit that had a destination and no target at the start of the tick."""
    out = []
    for k, u in _starts(flinch, ids):
        pre = ticks[k]["pre"][u]
        if pre["alive"] and pre["dest"] is not None and not pre["tgt"]:
            out.append((ticks[k]["n"], u))
    return out


def _hits(ticks):
    """{tick index: {victims}} of every shot that landed on a living unit."""
    out = {}
    for k, tk in enumerate(ticks):
        for a, v in tk["fires"]:
            out.setdefault(k, set()).add(v)
    return out


def repeated_away_no_hit(ticks, flinch, ids):
    """[(tick, unit)]: a move away begins when no hit has landed on the unit since the start of its previous move away."""
    hits = _hits(ticks)
    last_start = {}
    out = []
    for k, u in _starts(flinch, ids):
        if u in last_start:
            if not any(u in hits.get(j, ()) for j in range(last_start[u], k + 1)):
                out.append((ticks[k]["n"], u))
        last_start[u] = k
    return out


def walked_back_into_fire(ticks, flinch, ids):
    """[(tick, unit, what)]: after a move away ends, the unit has a destination or moves under its own power before it takes a target, is hit again or dies."""
    hits = _hits(ticks)
    out, holding = [], {}
    for k, tk in enumerate(ticks):
        for u in ids:
            fl = flinch[k].get(u, 0)
            post, pre = tk["post"][u], tk["pre"][u]
            if not post["alive"]:
                holding.pop(u, None)
                continue
            if u in holding and not fl:
                if u in hits.get(k, ()) or post["tgt"]:
                    holding.pop(u)
                elif post["dest"] is not None:
                    out.append((tk["n"], u, "destination"))
                    holding.pop(u)
                elif math.hypot(post["x"] - pre["x"], post["y"] - pre["y"]) > OWN_MOVE and not _near_other(ticks[k], ids, u):
                    out.append((tk["n"], u, "moved %.1f wu" % math.hypot(post["x"] - pre["x"], post["y"] - pre["y"])))
                    holding.pop(u)
            if k and flinch[k - 1].get(u, 0) and not fl:
                holding[u] = k
            if fl:
                holding.pop(u, None)
    return out


def _near_other(tk, ids, u):
    p0, p1 = tk["pre"][u], tk["post"][u]
    for o in ids:
        if o == u or not tk["pre"][o]["alive"]:
            continue
        for p in (p0, p1):
            for q in (tk["pre"][o], tk["post"][o]):
                if math.hypot(q["x"] - p["x"], q["y"] - p["y"]) < PUSH_RADIUS:
                    return True
    return False


def stood_under_unseen_fire(rec, stand=STAND_TICKS, radius=STAND_RADIUS, gap=HIT_GAP):
    """[(unit, first tick, length)]: runs of more than `stand` consecutive ticks on which a walker has a destination and no target and stays within `radius` of the run's first position, with an unseen hit on it
    within `gap` ticks of the end of the tick (the oracle's `unseen_hits`)."""
    last_hit = {}
    for n, v, a, _, _ in unseen.unseen_hits(rec):
        last_hit.setdefault(v, []).append(n)
    out, cur = [], {}
    for tk in rec.ticks:
        post = tk["post"]
        for u in rec.ids:
            p = post[u]
            if p["alive"] and p["dest"] is not None and not p["tgt"]:
                c = cur.get(u)
                if c is not None and math.hypot(p["x"] - c[1], p["y"] - c[2]) <= radius:
                    c[3] += 1
                    c[4] = tk["n"]
                    continue
                if c is not None:
                    out += _run(c, u, last_hit, stand, gap)
                cur[u] = [tk["n"], p["x"], p["y"], 1, tk["n"]]
            else:
                c = cur.pop(u, None)
                if c is not None:
                    out += _run(c, u, last_hit, stand, gap)
    for u, c in cur.items():
        out += _run(c, u, last_hit, stand, gap)
    return sorted(out)


def _run(c, u, last_hit, stand, gap):
    if c[3] <= stand:
        return []
    under = any(c[0] <= n <= c[4] + gap for n in last_hit.get(u, ()))
    return [(u, c[0], c[3])] if under else []


# ------------------------------------------------------------------ the measures against made-up ticks (green today)

def _row(x=1000.0, y=1000.0, dest=(2000.0, 2000.0), tgt=0, alive=True):
    return {"alive": alive, "x": x, "y": y, "layer": 0, "tgt": tgt, "dest": dest, "hp": 100.0}


def _tick(n, rows_pre, rows_post, fires=()):
    return {"n": n, "pre": rows_pre, "post": rows_post, "fires": list(fires), "vis_pre": {}, "vis_post": {}}


def test_control_the_measures_flag_planted_cases_and_nothing_else():
    """Control (green today): made-up ticks. A flag that goes up on a tick whose unit started with a destination is `moved_away_on_its_way`, one that started without a destination is not; a second move away
    with no hit between is `repeated_away_no_hit`, with a hit between it is not; a unit that walks off (a destination) or moves after its flag drops is `walked_back_into_fire`, one that stays put or takes a
    target is not."""
    idle, going = _row(dest=None), _row()
    t = [_tick(1, {1: going, 2: idle}, {1: going, 2: idle}), _tick(2, {1: going, 2: idle}, {1: going, 2: idle})]
    flinch = [{1: 0, 2: 0}, {1: 1, 2: 1}]
    assert moved_away_on_its_way(t, flinch, [1, 2]) == [(2, 1)]
    # two moves away, no hit between (ticks 2 and 6), then one with a hit (tick 10)
    ticks = [_tick(n, {1: idle}, {1: idle}) for n in range(1, 13)]
    fl = [{1: v} for v in (0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0)]
    assert repeated_away_no_hit(ticks, fl, [1]) == [(6, 1), (10, 1)]
    ticks[8]["fires"] = [(9, 1)]
    assert repeated_away_no_hit(ticks, fl, [1]) == [(6, 1)]
    # hold: flag drops at tick 3; at tick 5 the unit gets a destination
    ticks = [_tick(n, {1: idle}, {1: idle}) for n in range(1, 8)]
    ticks[4]["post"] = {1: _row()}
    fl = [{1: v} for v in (1, 1, 0, 0, 0, 0, 0)]
    assert walked_back_into_fire(ticks, fl, [1]) == [(5, 1, "destination")]
    ticks = [_tick(n, {1: idle}, {1: idle}) for n in range(1, 8)]
    ticks[4]["post"] = {1: _row(x=1030.0, dest=None)}
    assert walked_back_into_fire(ticks, fl, [1]) == [(5, 1, "moved 30.0 wu")]
    ticks = [_tick(n, {1: idle}, {1: idle}) for n in range(1, 8)]
    assert walked_back_into_fire(ticks, fl, [1]) == []


class _Rec:
    def __init__(self, move, seen_hits=True, dest=(2000.0, 2000.0), n=200):
        self.side = {1: 0, 2: 1}
        self.ids = [1, 2]
        self.ticks = []
        for k in range(1, n + 1):
            row = {1: _row(x=1000.0 + move * k, dest=dest), 2: _row(x=1300.0, dest=None)}
            fires = [(2, 1)] if k % 30 == 0 else []
            vis = {(0, 2): False, (1, 1): True}
            self.ticks.append({"n": k, "pre": row, "post": row, "fires": fires, "vis_pre": vis, "vis_post": vis})


def test_control_the_stand_measure_flags_a_walker_with_a_destination_that_stands_under_unseen_fire():
    """Control (green today): a walker with a destination and no target standing still 200 ticks while an enemy its side does not see hits it every 30 ticks is one stand of 200 ticks; the same walker walking 2 wu a
    tick, one with no destination (a unit that holds), or one standing with no hits on it is none."""
    assert stood_under_unseen_fire(_Rec(0.0)) == [(1, 1, 200)]
    assert stood_under_unseen_fire(_Rec(2.0)) == []
    assert stood_under_unseen_fire(_Rec(0.0, dest=None)) == []
    rec = _Rec(0.0)
    for tk in rec.ticks:
        tk["fires"] = []
    assert stood_under_unseen_fire(rec) == []


# ------------------------------------------------------------------ the premise: the fights exercise the rule (green today)

@pytest.mark.parametrize("name", LAYOUTS)
def test_premise_the_fight_has_units_hit_by_enemies_their_side_does_not_see(name):
    """Premise (green today): the layout, fought to the end in the lab configuration, has unseen hits: the rule is exercised. Counts are dumped in the message, not pinned. On L-0061 every victim is an
    attack-mover on its way (38 unseen hits, all from a higher layer, none moved away), which is what the rule says is neither moved nor stopped: that layout is the case of the first test below, and
    only the layouts of MOVE_AWAY_LAYOUTS are the case of a unit that moves away."""
    rec, flinch = played(name)
    s = unseen.summary(rec)
    assert s["unseen_hits"] > 0, "scene broken: no unseen hits in %s: %s" % (name, s)


@pytest.mark.parametrize("name", MOVE_AWAY_LAYOUTS)
def test_premise_the_fight_has_idle_or_arrived_units_that_move_away_under_unseen_fire(name):
    """Premise (green today; was part of the premise of every layout until Round 5, Test-defect: R-087-01 as ruled 2026-11-17, an attack-mover on its way is not moved, so on L-0061, where every victim is
    one, no unit ever moves away): the layout has an unseen hit and at least one unit in a move away, the unit the rule does move (an idle unit, or an attack-mover that has arrived). It is the control
    that the three tests below about a move away can fail: they are not silent for want of a move away in the fight."""
    rec, flinch = played(name)
    s = unseen.summary(rec)
    starts = _starts(flinch, rec.ids)
    assert s["unseen_hits"] > 0, "scene broken: no unseen hits in %s: %s" % (name, s)
    assert starts, "scene broken: no unit ever moved away in %s: %s" % (name, s)


# ------------------------------------------------------------------ the rule, whole fights

@pytest.mark.parametrize("name", LAYOUTS)
def test_R_087_01_no_attack_mover_on_its_way_is_moved_away_by_unseen_fire(name):
    """R-087-01: "An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit": on every tick of the fight, no unit that started the tick with a destination and no target
    begins a move away (the engine's flag). Red until Round 5: on L-0061 red walkers crossing the flat under fire from the hill are moved away 200 wu and sent back; on L-0080 red walkers leaving the pocket likewise."""
    rec, flinch = played(name)
    bad = moved_away_on_its_way(rec.ticks, flinch, rec.ids)
    assert not bad, "%s: %d moves away begin on a unit with a destination (tick, unit), %d units, first %s" % (name, len(bad), len({u for _, u in bad}), bad[:4])


@pytest.mark.parametrize("name", LAYOUTS)
def test_R_087_01_no_walker_with_an_attack_move_destination_stands_still_under_unseen_fire(name):
    """R-087-01: "neither moved nor stopped" (round5.md G4: 'no walker with an attack-move destination stands still under unseen fire'): on every tick of the fight, no walker that has a destination and no target
    stays within 2 wu of the same spot for more than 40 consecutive ticks while an enemy its side does not see keeps hitting it."""
    rec, flinch = played(name)
    bad = stood_under_unseen_fire(rec)
    assert not bad, "%s: %d stands under unseen fire (unit, first tick, ticks), %d units, first %s" % (name, len(bad), len({b[0] for b in bad}), bad[:4])


@pytest.mark.parametrize("name", LAYOUTS)
def test_R_087_01_no_unit_moves_away_more_than_once_without_a_new_hit(name):
    """R-087-01: "it holds where the move away ends ... a repeat hit it still cannot answer moves it again" (round5.md G4: 'no unit moves away more than once without a new hit'): no unit begins a move away when no
    shot has landed on it since the start of its previous move away."""
    rec, flinch = played(name)
    bad = repeated_away_no_hit(rec.ticks, flinch, rec.ids)
    assert not bad, "%s: %d moves away with no new hit (tick, unit), %d units, first %s" % (name, len(bad), len({u for _, u in bad}), bad[:4])


@pytest.mark.parametrize("name", LAYOUTS)
def test_R_087_01_a_unit_that_moved_away_holds_where_the_move_ends(name):
    """R-087-01: "it holds where the move away ends; it does not walk back into the fire": on every tick after a unit's move away ends, until it takes a target, is hit again or dies, it has no destination and
    does not move under its own power (the push of a neighbour within 40 wu is excused)."""
    rec, flinch = played(name)
    bad = walked_back_into_fire(rec.ticks, flinch, rec.ids)
    assert not bad, "%s: %d units walked after their move away ended (tick, unit, what), first %s" % (name, len(bad), bad[:4])
