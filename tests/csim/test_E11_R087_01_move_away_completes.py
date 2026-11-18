"""E-11 R-087-01 (engine rules round 3, T9 item 4; rewritten for Round 5, G4): a unit hit by unseen fire after it arrived with its group must really cover the move away and hold; an attack-mover still
on its way, in a pursuit or walking with its group, is not moved and not stopped.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01, as it reads on the Round 5 branch): "Given an idle unit, or an attack-moving unit that has arrived at its point, with no target, that takes
damage from an attacker it cannot see or cannot reach, When the loop runs, Then it leaves the line of fire instead of standing in it: it moves 200 wu directly away from the damage direction and stops, and it holds
where the move away ends; it does not walk back into the fire (Westley, 2026-11-17 ...). While it holds it acquires and returns fire as any idle unit does (R-087-04, R-087-06), and a repeat hit it still cannot
answer moves it again. An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit: it keeps walking its attack-move (Westley, 2026-11-17: "them starting to be shot at does not
stop their attack move" ...). A plain-moving unit and a guard (R-096-08, never walks off) ignore the hit (Westley 2026-11-06, the SC2 movement model). Hit from several sides it moves away from the latest hit; a unit
that holds a target is not moved (DEC-engine-rules-round2-2026-11-11)."
Rule pins: R-087-01, R-096-02, R-087-06.

Trace (engine-rules-baseline/x1/slope_pileup.md, item 2): in `om_tactical_ai_tick` (csrc/unit.c) the pursuit-end check `om_tac_end_pursuit` ran while the unit was still flinching: a unit hit by unseen fire got
`om_unit_clear_orders` and `om_tac_start_flinch` and the next AI tick commanded a move to the order point WHILE the flinch step was running; the two steps (4 wu away, 4 wu toward) cancelled and the unit stood. Round 3
fixed that for the move away; Round 5 removes the move away of an attack-mover that has not arrived (this file's tests of it are rewritten below), so what is left of the fault is the arrived group member.
The first-step tests are tests/csim/test_E11_R087_01_unseen_attacker_moves_the_unit.py (the scenes and `Hit`-style measures are imported from it, not copied); the lab twin of this file is
tests/skilllab/arena/test_engine_rules_r3_move_away.py.

The states: ARRIVED two Vanguards attack-moved together to a point 200 wu south, both arrived and standing (dest 0), then the GUN is put on the hill: the member hit moves away 200 wu and holds. WALKING a group of
2 or 3 still walking when hit, and PURSUING an attack-mover 12 ticks into a chase of a visible Supply whose target dies, hit on the very next tick: both are still on their way and are not moved.

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
    """An attack-mover chasing a visible Supply 320 wu west; 12 ticks into the chase the Supply dies, and the GUN appears on the hill. Returns (world, victim, gun).
    Test-defect 2026-11-17 (R-087-04, round5.md Second pass): the Supply stood 550 wu west, beyond the Vanguard's notice distance 330, so the unit never chased it; it stands 320 wu west
    (measured: acquired at tick 5, the Vanguard reaches attack range 300 about tick 13, still chasing at tick 12)."""
    w = base._world(lib, wf)
    u = spawn(lib, w, VANGUARD, 0, *base.V0, 0)
    s = spawn(lib, w, SUPPLY, 1, base.V0[0] - 320.0, 2000.0)
    lib.om_unit_set_hp(w, s, 1.0e6)
    attack_move(lib, w, [u], *base.POINT)
    for _ in range(12):
        step(lib, w)
    assert target(lib, w, u) == s and dest(lib, w, u)[0] == 1 and dest(lib, w, u)[1:] == pytest.approx((base.V0[0] - 320.0, 2000.0)), \
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
        self.flinch = []        # per tick: the engine's flag for "in a move away" (om_unit_in_flinch)
        run, spot = 0, None
        for k in range(1, base._window(lib, w, v) + 1):
            step(lib, w)
            p = pos(lib, w, v)
            along = (p[0] - self.start[0]) * self.away[0] + (p[1] - self.start[1]) * self.away[1]
            has, tgt = dest(lib, w, v)[0], target(lib, w, v)
            self.rows.append((k, round(along, 1), has, tgt, p))
            self.flinch.append(lib.om_unit_in_flinch(w, v))
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
        return "peak %.1f wu along the damage direction in %d ticks, reached %d wu at %s, longest stand with a destination and no target %d ticks, %d ticks in a move away; last row %s" % (
            self.peak, len(self.rows), FLEE_MIN, self.reached, self.stall, sum(self.flinch), self.rows[-1])


def _assert_not_moved_or_stopped(f, what):
    """The on-its-way clause: never in a move away, never 150 wu along the damage direction, never a stand of more than STALL_TICKS with a destination and no target."""
    assert not any(f.flinch), "%s: in a move away on %d ticks: %s" % (what, sum(f.flinch), f.text())
    assert f.reached is None, "%s: moved %d wu away: %s" % (what, FLEE_MIN, f.text())
    assert f.stall <= STALL_TICKS, "%s: %s" % (what, f.text())


# ------------------------------------------------------------------ controls: green today and after

def test_R_087_01_control_the_arrived_lone_attack_mover_completes_the_move_away_and_holds(lib, world_factory):
    """R-087-01 'moves 200 wu directly away from the damage direction and stops, and it holds where the move away ends' (control, green today and after): the base file's arrived attack-mover hit from the
    hill covers FLEE_MIN within the window, never stands with a destination for more than STALL_TICKS before that, and, the gun sent away so that no second shot lands, 100 ticks later is within 5 wu of where it stopped with no destination. Proves the measure
    and the scene (the engine's flag is up, the stall measure can read a move away)."""
    w, v, g = base._arrived_scene(lib, world_factory)
    base._unseen_premise(lib, w, v, g)
    f = Flee(lib, w, v, g)
    assert f.reached is not None and f.stall <= STALL_TICKS and any(f.flinch), f.text()
    stop = pos(lib, w, v)
    lib.om_unit_teleport(w, g, 3900.0, 3900.0, 0)       # no second shot (the gun fires every 160 ticks and still reaches the unit): a repeat hit would move it again
    for _ in range(100):
        step(lib, w)
    p = pos(lib, w, v)
    assert math.hypot(p[0] - stop[0], p[1] - stop[1]) <= 5.0 and dest(lib, w, v)[0] == 0, "the arrived attack-mover did not hold: stopped at %s, 100 ticks later %s, destination %s" % (stop, p, dest(lib, w, v))


def test_R_087_01_a_lone_attack_mover_on_its_way_is_not_moved_and_not_stopped_by_the_hit(lib, world_factory):
    """R-087-01 'An attack-moving unit still on its way to its point is neither moved nor stopped by such a hit: it keeps walking its attack-move': the base file's lone attack-mover hit from the hill: for the
    whole window it is never in a move away, never 150 wu along the damage direction, and never stands (a destination, no target, within 2 wu) for more than STALL_TICKS ticks. Red until Round 5: the engine moves
    it 200 wu away."""
    w, v, g = base._scene(lib, world_factory)
    base._unseen_premise(lib, w, v, g)
    base._wait_hit(lib, w, v)
    _assert_not_moved_or_stopped(Flee(lib, w, v, g), "lone attack-mover on its way")


@pytest.mark.parametrize("n", [2, 3])
def test_R_087_01_a_group_member_hit_while_walking_is_not_moved_and_not_stopped(lib, world_factory, n):
    """R-087-01 (the clause above, for a group): n Vanguards attack-moved together toward the base point, not yet arrived, hit from the hill by the attacker they cannot see: the member hit is never in a move away,
    never 150 wu along the damage direction, and never stands with a destination and no target for more than STALL_TICKS ticks. Red until Round 5 (the member moved 196 to 200 wu away)."""
    w = base._world(lib, world_factory)
    vs = [spawn(lib, w, VANGUARD, 0, base.V0[0] - 70.0 * i, base.V0[1] + 40.0 * i, 0) for i in range(n)]
    g = spawn(lib, w, base.GUN, 1, *base.G0, 1)
    attack_move(lib, w, vs, *base.POINT)
    v, k = _first_hit(lib, w, vs)
    _assert_not_moved_or_stopped(Flee(lib, w, v, g), "group of %d, member hit while walking" % n)


@pytest.mark.parametrize("n", [2, 3])
def test_R_087_01_control_a_group_member_that_had_arrived_is_moved_and_the_measure_sees_it(lib, world_factory, n):
    """R-087-01 control (green today and after): the on-its-way measure above applied to a member that HAS arrived (the setup one step outside the clause): it is in a move away on some tick and reached 150 wu, so the
    measure `_assert_not_moved_or_stopped` fails on it, which is what the rule wants of an arrived unit and what proves the test above can fail."""
    w, vs, g = _arrived_group(lib, world_factory, n)
    v, k = _first_hit(lib, w, vs)
    f = Flee(lib, w, v, g)
    assert any(f.flinch) and f.reached is not None, f.text()
    with pytest.raises(AssertionError):
        _assert_not_moved_or_stopped(f, "arrived member")


# ------------------------------------------------------------------ the arrived group member: the move away is really covered

@pytest.mark.parametrize("n", [2, 3])
def test_R_087_01_a_group_member_that_had_arrived_covers_the_move_away(lib, world_factory, n):
    """R-087-01 'it moves 200 wu directly away from the damage direction and stops' + 'it holds where the move away ends': n Vanguards attack-moved together, all arrived and standing, one is hit from the hill by
    the attacker it cannot see: within the window it is FLEE_MIN (150) wu from where it was hit along the damage direction, and it does not stand with a destination and no target for more than STALL_TICKS (10)
    ticks before it gets there. Green since Round 3: it crept about 0.4 wu a tick (50 to 67 wu in the 80-tick window) with a destination and no target, the pursuit-end check (csrc/unit.c om_tactical_ai_tick,
    om_tac_end_pursuit) commanding a walk back to the order point on the tick the move away began (the engine as it was on main 7ba38983 turns it red)."""
    w, vs, g = _arrived_group(lib, world_factory, n)
    v, k = _first_hit(lib, w, vs)
    base._unseen_premise(lib, w, v, g)
    assert target(lib, w, v) <= 0, "premise: the member holds a target"
    f = Flee(lib, w, v, g)
    assert f.reached is not None, "the arrived member did not cover %d wu away: %s" % (FLEE_MIN, f.text())
    assert f.stall <= STALL_TICKS, f.text()


def test_R_087_01_an_attack_mover_hit_the_tick_after_its_chase_target_died_is_not_moved_and_not_stopped(lib, world_factory):
    """R-087-01 as above, for the pursuing state: the attack-mover is 12 ticks into a chase of a visible Supply, the Supply dies, and the attacker it cannot see hits it on the next tick (target none, the chase's
    order issued != the order point). It is still on its way to its point, so for the whole window it is never in a move away, never 150 wu along the damage direction and never stands with a destination and
    no target for more than STALL_TICKS ticks. Red until Round 5 (the engine moves it away 200 wu)."""
    w, v, g = _pursuing(lib, world_factory)
    n, _ = base._wait_hit(lib, w, v)
    base._unseen_premise(lib, w, v, g)
    assert target(lib, w, v) <= 0, "premise: the unit holds a target"
    assert n == 1, "premise: the hit comes on the tick after the target died (the pursuing state), got tick %d" % n
    _assert_not_moved_or_stopped(Flee(lib, w, v, g), "pursuing attack-mover")
