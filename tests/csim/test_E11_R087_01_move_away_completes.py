"""E-11 R-087-01 (engine rules round 3, T9 item 4): a unit hit by unseen fire while it is still in a pursuit, or after it arrived with its group, must really cover the move away.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01): "Given an idle or attack-moving unit with no target that takes damage from an attacker it cannot see or cannot reach, When
the loop runs, Then it leaves the line of fire instead of standing or walking on blindly: it moves 200 wu directly away from the damage direction and stops, and an attack-mover then resumes its
attack-move toward its original point (R-096-02); once the attacker is visible and in range it stands and fights. A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit; a repeat
hit moves it again (Westley 2026-11-06, the SC2 movement model). An attack-mover that had already arrived at its point holds where the move away ends and does not walk back into the fire; hit from several
sides it moves away from the latest hit; a unit that holds a target is not moved (DRAFT readings, DEC-engine-rules-round2-2026-11-11, Westley may veto)."
Rule pins: R-087-01, R-096-02, R-087-06.

Trace (engine-rules-baseline/x1/slope_pileup.md, item 2): in `om_tactical_ai_tick` (csrc/unit.c) the pursuit-end check `om_tac_end_pursuit` runs while the unit is still flinching. A unit hit by unseen fire gets
`om_unit_clear_orders` and `om_tac_start_flinch` (kind 2 not arrived, kind 3 arrived) with `am_gid` 0 and `order_x/y` the original point, so `om_tac_pursuing()` (issued != order) is true; the next AI tick
sees "pursuing, no destination" and commands a move to the order point WHILE the flinch step is running. The two steps (4 wu away, 4 wu toward) cancel: the unit has a destination, no target, and stands.
The sweep counts it as the fourfold rise of "stalled walker" (I29): 162,686 unit-ticks on seven plain layouts, L-0081 alone 29,134. The first-step tests (tests/csim/test_E11_R087_01_unseen_attacker_moves_the_unit.py,
tests/skilllab/arena/test_engine_rules_f9_unseen_fire.py) pass today because a lone attack-mover that is not pursuing, hit once, is moved correctly; the lab twin of this file is
tests/skilllab/arena/test_engine_rules_r3_move_away.py.

The states that trigger it, found by running them (scene H of the base file: hill at (2400, 2000), the victim a walking Vanguard on the flat at (1800, 2000), the attacker GUN on the hill it cannot see, one
shot of 10 every 160 ticks; the scenes and `Hit`-style measures are imported from the base file, not copied):
  ARRIVED   two Vanguards attack-moved together to a point 200 wu south, both arrived and standing (dest 0), then the GUN is put on the hill: the member hit moves 78.9 wu along the damage direction in 160
            ticks (0.36 wu a tick, with a destination and no target for 150 ticks), peak 78.9. Group of one (the lone control) and a group of 2 or 3 still walking when hit are not affected (peak 196 to 200).
  PURSUING  an attack-mover that is chasing a visible Supply (12 ticks into the chase, destination = the Supply's place) whose target dies, hit on the very next tick by the GUN that appears: it moves 47 wu in
            99 ticks. A hit 2 or more ticks later is not affected (the unit's cohort turn ended the pursuit first).
  Not triggering: a lone attack-mover walking its order (the base file's tests), a group member walking.

Detector bounds (not rules; Westley's to change): FLEE_MIN 150 wu (the brief), WINDOW = ceil(200 / pace) + 30 ticks (the base file's DRAFT-t5-slack-ticks), STALL_TICKS 10 = DRAFT-t9-stall-ticks (a unit with a
destination and no target that stays within 2 wu of the same spot for more than this many ticks before it has covered FLEE_MIN, i.e. while it is in the move away), STALL_RADIUS 2 wu.
"""
import math

import pytest

from test_PP_unit_support import SUPPLY, VANGUARD, attack_move, dest, hp, pos, spawn, step, target
import test_E11_R087_01_unseen_attacker_moves_the_unit as base

FLEE_MIN = 150.0
STALL_TICKS = 10             # DRAFT-t9-stall-ticks
STALL_RADIUS = 2.0
RESUME = base.RESUME         # DRAFT-t5-resume 40 wu


def _arrived_group(lib, wf, n=2):
    """n Vanguards attack-moved together to 200 wu south of the base spot, arrived and standing; the GUN then appears on the hill (the base file's arrived scene, with a group)."""
    w = base._world(lib, wf)
    vs = [spawn(lib, w, VANGUARD, 0, base.V0[0] - 70.0 * i, base.V0[1] + 40.0 * i, 0) for i in range(n)]
    g = spawn(lib, w, base.GUN, 1, 3000.0, 2000.0, 0)
    attack_move(lib, w, vs, base.V0[0], base.V0[1] - 200.0)
    for _ in range(120):
        step(lib, w)
    assert all(dest(lib, w, v)[0] == 0 for v in vs), "premise: every member has arrived (destination cleared): %s" % [dest(lib, w, v) for v in vs]
    lib.om_unit_teleport(w, g, *base.G0, 1)
    step(lib, w)
    return w, vs, g


def _first_hit(lib, w, vs, limit=400):
    h0 = {v: hp(lib, w, v) for v in vs}
    for k in range(1, limit + 1):
        step(lib, w)
        for v in vs:
            if hp(lib, w, v) < h0[v]:
                return v, k
    pytest.fail("scene broken: nobody was hit in %d ticks" % limit)


def _pursuing(lib, wf):
    """An attack-mover chasing a visible Supply 550 wu west; 12 ticks into the chase the Supply dies, and the GUN appears on the hill. Returns (world, victim, gun)."""
    w = base._world(lib, wf)
    u = spawn(lib, w, VANGUARD, 0, *base.V0, 0)
    s = spawn(lib, w, SUPPLY, 1, 1250.0, 2000.0)
    lib.om_unit_set_hp(w, s, 1.0e6)
    attack_move(lib, w, [u], *base.POINT)
    for _ in range(12):
        step(lib, w)
    assert target(lib, w, u) == s and dest(lib, w, u)[0] == 1 and dest(lib, w, u)[1:] == pytest.approx((1250.0, 2000.0)), \
        "premise: the unit chases the Supply (target %s, destination %s)" % (target(lib, w, u), dest(lib, w, u))
    lib.om_unit_set_hp(w, s, 0.0)
    step(lib, w)
    g = spawn(lib, w, base.GUN, 1, *base.G0, 1)
    return w, u, g


class Flee:
    """The victim's move after the hit: per tick the distance along the damage direction, the destination, the target. `reached` the first tick it is FLEE_MIN along (or None); `stall` the longest run
    of ticks, before it got there, with a destination, no target, and a position within STALL_RADIUS of the run's first."""

    def __init__(self, lib, w, v, g):
        self.start = pos(lib, w, v)
        gp = pos(lib, w, g)
        d = math.hypot(self.start[0] - gp[0], self.start[1] - gp[1])
        self.away = ((self.start[0] - gp[0]) / d, (self.start[1] - gp[1]) / d)
        self.rows, self.reached, self.stall = [], None, 0
        run, spot = 0, None
        for k in range(1, base._window(lib, w, v) + 1):
            step(lib, w)
            p = pos(lib, w, v)
            along = (p[0] - self.start[0]) * self.away[0] + (p[1] - self.start[1]) * self.away[1]
            has, tgt = dest(lib, w, v)[0], target(lib, w, v)
            self.rows.append((k, round(along, 1), has, tgt, p))
            if self.reached is None and along >= FLEE_MIN:
                self.reached = k
            if self.reached is None:
                if has and tgt <= 0 and (spot is not None and math.hypot(p[0] - spot[0], p[1] - spot[1]) <= STALL_RADIUS):
                    run += 1
                else:
                    run, spot = (1, p) if has and tgt <= 0 else (0, None)
                self.stall = max(self.stall, run)
        self.peak = max(r[1] for r in self.rows)

    def text(self):
        return "peak %.1f wu along the damage direction in %d ticks, reached %d wu at %s, longest stand with a destination and no target %d ticks; last row %s" % (
            self.peak, len(self.rows), FLEE_MIN, self.reached, self.stall, self.rows[-1])


# ------------------------------------------------------------------ controls: green today and after

def test_R_087_01_control_a_lone_attack_mover_completes_the_move_away_and_resumes_its_attack_move(lib, world_factory):
    """R-087-01 'moves 200 wu directly away ... and stops, and an attack-mover then resumes its attack-move toward its original point' (control, green today and after): the base file's lone attack-mover hit
    from the hill covers FLEE_MIN within the window, never stands with a destination for more than STALL_TICKS before that, has the original point as its destination again afterwards and is at least RESUME
    (40 wu) nearer to it 20 ticks later. Proves the measure and the scene."""
    w, v, g = base._scene(lib, world_factory)
    base._unseen_premise(lib, w, v, g)
    base._wait_hit(lib, w, v)
    f = Flee(lib, w, v, g)
    assert f.reached is not None and f.stall <= STALL_TICKS, f.text()
    after = [r for r in f.rows if r[0] > f.reached and r[2] == 1]
    assert after, "the lone attack-mover never took its original point as a destination again: %s" % f.text()
    here = after[0][4]
    for _ in range(20):
        step(lib, w)
    d0 = math.hypot(here[0] - base.POINT[0], here[1] - base.POINT[1])
    d1 = math.hypot(pos(lib, w, v)[0] - base.POINT[0], pos(lib, w, v)[1] - base.POINT[1])
    assert d0 - d1 >= RESUME, "no resume: %.1f wu from the point, then %.1f" % (d0, d1)


@pytest.mark.parametrize("n", [2, 3])
def test_R_087_01_control_a_group_member_hit_while_walking_covers_the_move_away(lib, world_factory, n):
    """R-087-01 control (green today and after): n Vanguards attack-moved together toward the base point, not yet arrived, hit from the hill by the attacker they cannot see: the member hit covers FLEE_MIN
    within the window and never stands with a destination for more than STALL_TICKS before that (measured: peak 196 to 200 wu, stand 0 to 1 ticks)."""
    w = base._world(lib, world_factory)
    vs = [spawn(lib, w, VANGUARD, 0, base.V0[0] - 70.0 * i, base.V0[1] + 40.0 * i, 0) for i in range(n)]
    g = spawn(lib, w, base.GUN, 1, *base.G0, 1)
    attack_move(lib, w, vs, *base.POINT)
    v, k = _first_hit(lib, w, vs)
    f = Flee(lib, w, v, g)
    assert f.reached is not None and f.stall <= STALL_TICKS, f.text()


# ------------------------------------------------------------------ red today

@pytest.mark.parametrize("n", [2, 3])
def test_R_087_01_a_group_member_that_had_arrived_covers_the_move_away(lib, world_factory, n):
    """R-087-01 'it moves 200 wu directly away from the damage direction and stops' + 'An attack-mover that had already arrived at its point holds where the move away ends': n Vanguards attack-moved
    together, all arrived and standing, one is hit from the hill by the attacker it cannot see: within the window it is FLEE_MIN (150) wu from where it was hit along the damage direction, and it does not
    stand with a destination and no target for more than STALL_TICKS (10) ticks before it gets there. Red today: it creeps about 0.4 wu a tick (50 to 67 wu in the 80-tick window, 78.9 in 160) with a destination and no target; the stand measure reads 6 ticks because the creep leaves the 2 wu radius,
    the pursuit-end check commanding a walk back to the order point on the tick the move away begins. Break that turns it red: the engine as it is on main 7ba38983 (csrc/unit.c om_tactical_ai_tick
    calls om_tac_end_pursuit while `flinching` is set)."""
    w, vs, g = _arrived_group(lib, world_factory, n)
    v, k = _first_hit(lib, w, vs)
    base._unseen_premise(lib, w, v, g)
    assert target(lib, w, v) <= 0, "premise: the member holds a target"
    f = Flee(lib, w, v, g)
    assert f.reached is not None, "the arrived member did not cover %d wu away: %s" % (FLEE_MIN, f.text())
    assert f.stall <= STALL_TICKS, f.text()


def test_R_087_01_an_attack_mover_hit_the_tick_after_its_chase_target_died_covers_the_move_away(lib, world_factory):
    """R-087-01 as above, for the pursuing state: the attack-mover is 12 ticks into a chase of a visible Supply, the Supply dies, and the attacker it cannot see hits it on the next tick (target none, the
    chase's order issued != the order point). Within the window it is FLEE_MIN wu from where it was hit and never stands with a destination and no target for more than STALL_TICKS ticks first. Red today:
    peak 47 wu in 99 ticks, the same cancelled step."""
    w, v, g = _pursuing(lib, world_factory)
    n, _ = base._wait_hit(lib, w, v)
    base._unseen_premise(lib, w, v, g)
    assert target(lib, w, v) <= 0, "premise: the unit holds a target"
    assert n == 1, "premise: the hit comes on the tick after the target died (the pursuing state), got tick %d" % n
    f = Flee(lib, w, v, g)
    assert f.reached is not None, "the pursuing unit did not cover %d wu away: %s" % (FLEE_MIN, f.text())
    assert f.stall <= STALL_TICKS, f.text()
