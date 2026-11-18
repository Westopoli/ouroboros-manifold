# Rule pins: R-087-01, R-087-04, R-087-06, R-096-02, R-096-08
"""E-11 R-087-01 (engine rules round 5, G4): an attack-mover still on its way to its point is neither moved nor stopped by a hit it cannot see or reach; an idle unit and an attack-mover that has arrived move 200 wu
away and HOLD there, acquire and return fire while holding, and are moved again by a repeat hit they cannot answer; plain movers, guards and units holding a target are unchanged.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01, as it reads on the Round 5 branch):
  "Given an idle unit, or an attack-moving unit that has arrived at its point, with no target, that takes damage from an attacker it cannot see or cannot reach, When the loop runs, Then it leaves the line of fire
  instead of standing in it: it moves 200 wu directly away from the damage direction and stops, and it holds where the move away ends; it does not walk back into the fire (Westley, 2026-11-17, asked whether a
  unit that moved away walks back in, after one unit in a lab fight moved away 57 times: "All the rest go with recommended", the recommendation being that it holds where it stops). While it holds it acquires and
  returns fire as any idle unit does (R-087-04, R-087-06), and a repeat hit it still cannot answer moves it again. An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit: it
  keeps walking its attack-move (Westley, 2026-11-17: "them starting to be shot at does not stop their attack move"; StarCraft 2 does the same, an attack-moving unit ignores what it cannot attack; this replaces, for
  that unit, the move away he ruled on 2026-11-06). A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit (Westley 2026-11-06, the SC2 movement model). Hit from several sides it moves away from
  the latest hit; a unit that holds a target is not moved (DEC-engine-rules-round2-2026-11-11)."

The first move away, the on-its-way clause for one hit, the plain mover and the guard are tests/csim/test_E11_R087_01_unseen_attacker_moves_the_unit.py, whose scenes and measures this file imports (scene H: a
Vanguard victim on the flat, a custom gun on the hill it cannot see up to, one shot of 10 every 160 ticks, range 800). This file proves what Round 5 adds or fixes: the hold, the acquire and the return fire
while holding, the repeat hit of an arrived unit, the unit that holds a target, and two hits on an attack-mover that is still on its way. The whole-fight twin is
tests/skilllab/arena/test_engine_rules_r5_unseen_fire.py.

Detector bounds (not rules; Westley's to change): HOLD_RADIUS DRAFT-r5-hold-radius 5 wu (a holding unit stays within this of where its move away ended; the push of a neighbour is not in these scenes),
HOLD_TICKS DRAFT-r5-hold-ticks 400 (the brief: 'still there 400 ticks later with no hits'), ACQUIRE_TICKS DRAFT-r5-acquire-ticks 12 (a cohort turn is up to 4 ticks, R-087-08; the rest is slack), FIRE_TICKS
DRAFT-r5-fire-ticks 40, FAR_POINT (1850, 250) 1800 wu from the victim: it is walked for 450 ticks, long enough for the gun's second shot (tick 164) and out of its range after about tick 194.
Every test states whether it is red or green against the engine before Round 5; the controls are green and show the measure can fail.
"""
import math

import pytest

from test_PP_unit_support import SUPPLY, VANGUARD, attack_move, dest, hp, pos, spawn, step, target
import test_E11_R087_01_unseen_attacker_moves_the_unit as base

HOLD_RADIUS = 5.0           # DRAFT-r5-hold-radius
HOLD_TICKS = 400            # DRAFT-r5-hold-ticks
ACQUIRE_TICKS = 12          # DRAFT-r5-acquire-ticks
FIRE_TICKS = 40             # DRAFT-r5-fire-ticks
FAR_POINT = (1850.0, 250.0)
AWAY = (3900.0, 3900.0)     # where a gun is sent so that no second shot lands


def _idle(lib, wf):
    w, v, g = base._scene(lib, wf, order=None)
    base._unseen_premise(lib, w, v, g)
    base._wait_hit(lib, w, v)
    return w, v, g


def _arrived(lib, wf):
    w, v, g = base._arrived_scene(lib, wf)
    base._unseen_premise(lib, w, v, g)
    return w, v, g


KINDS = {"idle": _idle, "arrived attack-mover": _arrived}


def _moved_away(lib, w, v, g, what):
    """Run the move-away window of a first hit, send the gun away (no second shot), and return where the unit stopped. The unit has stopped: its last position is within 5 wu of its peak."""
    h = base.Hit(lib, w, v, g)
    base._assert_flees(h, what)
    stop = h.rows[-1][1]
    peak = h.peak()[1]
    assert math.hypot(stop[0] - peak[0], stop[1] - peak[1]) <= HOLD_RADIUS, "premise: %s was still moving at the end of its window: %s" % (what, h.text())
    lib.om_unit_teleport(w, g, AWAY[0], AWAY[1], 0)
    step(lib, w)
    assert not any(h.flinch[-5:]), "premise: %s was still in its move away at the end of the window" % what
    return stop


def _hold_rows(lib, w, v, stop, ticks):
    """Per tick: (tick, distance from the stop, in a move away, has a destination, target)."""
    rows = []
    for k in range(1, ticks + 1):
        step(lib, w)
        p = pos(lib, w, v)
        rows.append((k, math.hypot(p[0] - stop[0], p[1] - stop[1]), lib.om_unit_in_flinch(w, v), dest(lib, w, v)[0], target(lib, w, v)))
    return rows


# ------------------------------------------------------------------ the hold

@pytest.mark.parametrize("kind", sorted(KINDS))
def test_R_087_01_a_unit_that_moved_away_holds_where_the_move_ends_and_does_not_walk_back(lib, world_factory, kind):
    """R-087-01: "it moves 200 wu directly away from the damage direction and stops, and it holds where the move away ends; it does not walk back into the fire": the idle unit, or the attack-mover that had
    arrived, hit from the hill by the attacker it cannot see, moves 150 to 250 wu away and stops; the attacker is then sent away (no second shot), and on every one of the next 400 ticks the unit is within 5 wu
    of where it stopped, is not in a move away, has no destination and holds no target. Green on the engine before Round 5 (the F9B fix of Round 3 made the arrived unit hold; the idle one always did): the
    control below shows the measure fails when the unit is hit again."""
    w, v, g = KINDS[kind](lib, world_factory)
    stop = _moved_away(lib, w, v, g, kind)
    rows = _hold_rows(lib, w, v, stop, HOLD_TICKS)
    bad = [(r[0], round(r[1], 1), "flinch" if r[2] else "", "dest" if r[3] else "", "target %d" % r[4] if r[4] > 0 else "") for r in rows if r[1] > HOLD_RADIUS or r[2] or r[3] or r[4] > 0]
    assert not bad, "%s did not hold (tick, distance from the stop, what): %d ticks, first %s" % (kind, len(bad), bad[:4])


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_R_087_01_control_a_unit_left_in_the_line_of_fire_does_not_hold(lib, world_factory, kind):
    """R-087-01 control (green today and after): the scene above with the attacker left in place: it fires again 160 ticks after the first shot, and the unit, which "holds" only while nobody hits it again,
    moves away again: the hold measure of the test above reads a move on some tick of 400. Proves the measure can fail, and that the hold test is green because the unit held, not because it was
    never hit again by chance."""
    w, v, g = KINDS[kind](lib, world_factory)
    h = base.Hit(lib, w, v, g)
    base._assert_flees(h, kind)
    stop = h.rows[-1][1]
    rows = _hold_rows(lib, w, v, stop, HOLD_TICKS)
    assert any(r[1] > HOLD_RADIUS or r[2] for r in rows), "%s was not moved again by a second shot: the measure cannot tell a hold from a move" % kind


# ------------------------------------------------------------------ while holding: acquire and return fire as an idle unit does

def _dummy_enemy(lib, w, xy):
    s = spawn(lib, w, SUPPLY, 1, xy[0], xy[1], 0)
    lib.om_unit_set_hp(w, s, 1.0e6)
    return s


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_R_087_01_a_holding_unit_acquires_the_enemy_within_its_notice_distance_and_fires(lib, world_factory, kind):
    """R-087-01: "While it holds it acquires ... as any idle unit does (R-087-04 ...)": the unit that moved away and holds, with an enemy its side sees appearing 250 wu from it on the flat (inside its attack range
    300 and its notice distance), takes it as its target within 12 ticks (a cohort turn, R-087-08) and its hp falls within 40: it acquires and fires. Green today and after."""
    w, v, g = KINDS[kind](lib, world_factory)
    stop = _moved_away(lib, w, v, g, kind)
    _hold_rows(lib, w, v, stop, 20)
    s = _dummy_enemy(lib, w, (stop[0], stop[1] + 250.0))
    got = fired = None
    for k in range(1, FIRE_TICKS + 1):
        step(lib, w)
        if got is None and target(lib, w, v) == s:
            got = k
        if fired is None and hp(lib, w, s) < 1.0e6:
            fired = k
    assert got is not None and got <= ACQUIRE_TICKS, "%s: the holding unit took the enemy 250 wu away as its target at tick %s (wanted within %d)" % (kind, got, ACQUIRE_TICKS)
    assert fired is not None, "%s: the holding unit never fired on the enemy it acquired in %d ticks" % (kind, FIRE_TICKS)


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_R_087_01_control_a_holding_unit_does_not_acquire_an_enemy_beyond_its_notice_distance(lib, world_factory, kind):
    """R-087-01 / R-087-04 control (green today and after; the setup one step outside the acquire test above): the same enemy 900 wu from the holding unit, beyond its sight and its notice distance, is not
    taken as a target in 60 ticks, and the unit stays within 5 wu of where it stopped. Proves the acquire test above can fail."""
    w, v, g = KINDS[kind](lib, world_factory)
    stop = _moved_away(lib, w, v, g, kind)
    _hold_rows(lib, w, v, stop, 20)
    s = _dummy_enemy(lib, w, (stop[0], stop[1] + 900.0))
    rows = _hold_rows(lib, w, v, stop, 60)
    assert all(r[4] != s and r[1] <= HOLD_RADIUS for r in rows), "the holding unit reacted to an enemy 900 wu away: %s" % [r for r in rows if r[4] == s or r[1] > HOLD_RADIUS][:3]


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_R_087_01_a_holding_unit_returns_fire_on_an_attacker_it_can_see(lib, world_factory, kind):
    """R-087-01: "While it holds it ... returns fire as any idle unit does (... R-087-06)": the unit that moved away and holds is hit by a second attacker on the flat, 500 wu west, which its side sees (on its own
    layer, inside its sensor radius) and which is beyond its notice distance, so only the hit can make it a target: within 8 ticks of the hit it takes that attacker as its target (return fire, then it
    pursues). Green today and after."""
    w, v, g = KINDS[kind](lib, world_factory)
    stop = _moved_away(lib, w, v, g, kind)
    _hold_rows(lib, w, v, stop, 20)
    a = spawn(lib, w, base.GUN, 1, stop[0] - 500.0, stop[1], 0)
    assert lib.om_unit_can_see(w, v, a) == 1, "premise: the holding unit does not see the attacker 500 wu away"
    assert target(lib, w, v) <= 0, "premise: the holding unit already holds a target"
    h0, hit_at, got = hp(lib, w, v), None, None
    for k in range(1, 120):
        step(lib, w)
        if hit_at is None and hp(lib, w, v) < h0:
            hit_at = k
        if hit_at is not None and target(lib, w, v) == a:
            got = k
            break
        assert hit_at is None or k - hit_at <= 8, "%s: hit at tick %d, no return fire by tick %d (target %d)" % (kind, hit_at, k, target(lib, w, v))
    assert hit_at is not None, "scene broken: the second attacker never hit the unit"
    assert got is not None, "%s: no return fire after the hit at tick %d" % (kind, hit_at)


# ------------------------------------------------------------------ a repeat hit they cannot answer moves them again

def test_R_087_01_a_repeat_hit_moves_the_arrived_attack_mover_again(lib, world_factory):
    """R-087-01: "a repeat hit it still cannot answer moves it again": the attack-mover that had arrived, hit from the hill, moves 150 to 250 wu away and holds; 160 ticks after the first shot it is hit again from
    where it stands (the attacker's range is 800 wu) and again reaches 150 to 250 wu along the new damage direction. Green today and after (the idle twin is in the base file)."""
    w, v, g = _arrived(lib, world_factory)
    first = base.Hit(lib, w, v, g)
    base._assert_flees(first, "first hit")
    base._wait_hit(lib, w, v)
    assert not lib.om_unit_can_see(w, v, g) and target(lib, w, v) <= 0, "premise: the second hit finds the unit still blind and without a target"
    second = base.Hit(lib, w, v, g)
    assert second.start != first.start, "premise: the second hit is at the first hit's position"
    base._assert_flees(second, "repeat hit")


# ------------------------------------------------------------------ units that are not moved

def test_R_087_01_a_unit_that_holds_a_target_is_not_moved_by_unseen_fire(lib, world_factory):
    """R-087-01: "a unit that holds a target is not moved": the idle victim has an enemy it sees 200 wu away on the flat as its target (in range 300, a Supply, hp 1e6; taken before the attacker, which starts 1200 wu
    away, is teleported onto the hill) when the attacker it cannot see hits it three times (every 160 ticks): on every tick of 500 it is not in a move away, holds that target, and is within 5 wu of its place.
    Green today and after."""
    w, v, g = base._scene(lib, world_factory, order=None, g_xy=(3000.0, 2000.0), g_layer=0)
    s = _dummy_enemy(lib, w, (base.V0[0], base.V0[1] + 200.0))
    for _ in range(12):
        step(lib, w)
    assert target(lib, w, v) == s, "premise: the victim did not take the enemy 200 wu away as its target"
    lib.om_unit_teleport(w, g, base.G0[0], base.G0[1], 1)
    step(lib, w)
    base._unseen_premise(lib, w, v, g)
    place, hits, prev, bad = pos(lib, w, v), 0, 500.0, []
    for k in range(1, 501):
        step(lib, w)
        p = pos(lib, w, v)
        now = hp(lib, w, v)
        hits += now < prev
        prev = now
        if lib.om_unit_in_flinch(w, v) or target(lib, w, v) != s or math.hypot(p[0] - place[0], p[1] - place[1]) > HOLD_RADIUS:
            bad.append((k, round(math.hypot(p[0] - place[0], p[1] - place[1]), 1), lib.om_unit_in_flinch(w, v), target(lib, w, v)))
    assert hits >= 3, "scene broken: the victim was hit %d times" % hits
    assert not bad, "the unit holding a target was moved or lost it (tick, distance, flinch, target): %s" % (bad[:4],)


def test_R_087_01_control_the_same_unit_without_a_target_is_moved_by_the_same_hits(lib, world_factory):
    """R-087-01 control (green today and after; the setup one step outside the test above): the same victim and hits with no enemy to hold: it is in a move away on some tick. Proves the flag and the scene
    of the test above can show a move."""
    w, v, g = base._scene(lib, world_factory, order=None)
    base._unseen_premise(lib, w, v, g)
    moved = 0
    for _ in range(500):
        step(lib, w)
        moved += lib.om_unit_in_flinch(w, v)
    assert moved > 0, "the unit was never moved: the hold-a-target test above proves nothing"


# ------------------------------------------------------------------ the attack-mover on its way, hit twice

def test_R_087_01_an_attack_mover_on_its_way_hit_twice_keeps_walking_its_attack_move(lib, world_factory):
    """R-087-01: "An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit": the victim attack-moves 1800 wu south to (1850, 250) and is hit twice from the hill it cannot
    see (ticks 4 and 164; out of the gun's range after about tick 194). On every one of the first 230 ticks it is not in a move away, holds no target, its destination is the ordered point (unchanged by either
    hit), and it ends the tick nearer the point by at least a quarter of its pace. Red until Round 5: the engine moves it away 200 wu on each hit and clears its destination."""
    w, v, g = base._scene(lib, world_factory, order=None)
    attack_move(lib, w, [v], *FAR_POINT)
    base._unseen_premise(lib, w, v, g)
    h0 = hp(lib, w, v)
    h = base.Hit(lib, w, v, g, ticks=230, away=(-1.0, 0.0))
    hits = round((h0 - hp(lib, w, v)) / 7.5)
    assert hits >= 2, "scene broken: the victim was hit %d times in 230 ticks" % hits
    bad = base._closing_every_tick(lib, w, v, h, FAR_POINT)
    assert not bad, "%d ticks on which the attack-mover was moved, stopped or lost its point (tick, what), first %s" % (len(bad), bad[:4])


def test_R_087_01_control_the_same_walk_with_the_attacker_sent_away_passes_the_measure(lib, world_factory):
    """R-087-01 control (green today and after): the scene above with the attacker out of range from the start: 230 ticks of the same attack-move are read by the same per-tick measure with no stop, no move
    away and no change of destination. Proves the measure of the test above can be passed."""
    w, v, g = base._scene(lib, world_factory, order=None)
    attack_move(lib, w, [v], *FAR_POINT)
    lib.om_unit_teleport(w, g, AWAY[0], AWAY[1], 0)
    step(lib, w)
    h = base.Hit(lib, w, v, g, ticks=230, away=(-1.0, 0.0))
    assert hp(lib, w, v) == 500.0, "premise: the victim was hit"
    assert not base._closing_every_tick(lib, w, v, h, FAR_POINT), base._closing_every_tick(lib, w, v, h, FAR_POINT)[:4]
