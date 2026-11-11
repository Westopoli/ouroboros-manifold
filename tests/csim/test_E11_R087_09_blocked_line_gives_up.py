"""E-11 R-087-09 (engine rule fixes 2026-11-08, F5): a unit whose target is in range with the line blocked looks for a firing spot, and gives
the target up after 1 s.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F5". Evidence: docs/reports/2026-11-07-rule-enforcement.md (sweep I4b: 3.5 million
unit-ticks hold an unshootable target). Bug fix, not a story. The whole-run proof on catalogue layouts is
tests/skilllab/arena/test_engine_rules_f5_giveup.py; this file is the single geometry.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-09):
  "Given an idle or attack-moving unit with a target within its attack range whose line of fire is blocked by units, cover or ground, When
  evaluated, Then it steers around the blockers by the probe of blocked movement (R-097-03) until it reaches a spot with a clear line, and if it
  finds none within 1 s (20 ticks) it drops the target and acquires another (Westley, 2026-10-07: blocked fire is handled like blocked movement;
  'a unit gives up to pick another target if it can't find a firing spot within 1 second'). An obstacle is a detour, never a full stop (E-17
  R-190-07)."
Number the bible does not give (spec F5): the dropped target is not eligible for that unit until the unit has a clear line to it again or
DRAFT-giveup-exclusion-ticks 100 pass (Westley's to change); without it the unit would take the same nearest target again at once.
Rule pins: R-087-09, R-087-03, R-097-03, R-190-07.

Configuration: the shipped one for a csim scene: walking units (the Vanguard is set to the walking kind, as the lab does), planar obstacles
(om_map_block_rect, the lab's call), targeting by sight on (the parameter's default, OM_TP_TARGET_BY_SIGHT 1), steering and routing around terrain
on (their defaults). The unit under test is idle (no order): R-087-09 names an idle or attack-moving unit, and the idle unit is the one that holds
for ever today. The attack-moving unit is proved by the whole-run file only (its order keeps it walking, A171, and the choice of route is not
a single geometry).

Scene (2000 x 2000 canvas, Vanguard: attack range 300, sensor radius 700, 4 wu per tick). The shooter A (faction 0) stands at (470, 395); its
nearest enemy T1 (a Supply with 1e6 hp, which never fires, so only the test changes what A does) stands at (630, 395), 160 wu away, behind a wall that
blocks the line. A friendly Interceptor at (630, 1100) (sensor 1000, so it sees T1 at 705 wu; at 305 wu it shot T1 in a trial, its range is longer than the g3 file says, so it stands well beyond it) is the spotter: the
side sees T1, so A acquires it (R-093-02; the g3 tests use the same spotter), as in the lab fights where sight and fire disagree. Two walls:
  GAP   one cell, x 500..600, y 300..400. The nearest clear firing spot is about 35 wu above A (measured: the line clears from y = 430).
  LONG  the column x 500..600, y 0..1800. No firing spot within 20 ticks (80 wu) of A.
In the LONG scene a second enemy T2 stands at (470, 150), 245 wu from A on A's side of the wall, clear line: the "another" target. T2 has 1 hp so
that A kills it and has nothing left to take but T1.

Detector bounds (not rules; Westley's to change): FIND_CAP 60 ticks is a run cap for "steers and fires" (the rule allows 20 ticks to find a
spot, then acquisition runs at a cohort turn, 4 ticks); TAKE_CAP 80 ticks is a run cap for "takes another target and fires"; CLEAR_TAKE 12 ticks
is the time allowed to take a target whose line has cleared (two cohort cycles and a tick); MOVED 5 wu is "A steered".
Controls green today: the unblocked twin fires; the blocked scene's premises hold.
"""
import pytest

from conftest import OMFeature
from test_PP_unit_support import INTERCEPTOR, SUPPLY, VANGUARD, hp, pos, spawn, step, target

CANVAS = 2000.0
WALKING = 1                         # OM_MOVE_WALKING
RANGE = 300.0                       # Vanguard attack range (roster)
GIVEUP_TICKS = 20                   # R-087-09: "within 1 s (20 ticks)"
EXCLUSION_TICKS = 100               # DRAFT-giveup-exclusion-ticks (spec F5), Westley's to change
FIND_CAP = 60                       # detector bound, see the docstring
TAKE_CAP = 80                       # detector bound
CLEAR_TAKE = 12                     # detector bound
MOVED = 5.0                         # detector bound
GAP_WALL = (510.0, 310.0, 590.0, 390.0)       # the cell x 500..600, y 300..400, as the lab snaps a box
LONG_WALL = (510.0, 10.0, 590.0, 1790.0)      # the column x 500..600, y 0..1800
BIG_HP = 1.0e6                      # T1 never dies in a scene; T2 has 1 hp
A_XY, T1_XY, T2_XY, SPOT_XY = (470.0, 395.0), (630.0, 395.0), (470.0, 150.0), (630.0, 1100.0)


def _world(lib, wf, wall):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, WALKING) == 0
    if wall is not None:
        assert lib.om_map_block_rect(w, *wall, 0, 4) == 0
    return w


def _scene(lib, wf, wall, t2=False):
    """(world, A, T1, T2 or None). Spawn order fixes the ids: spotter, A, T1, T2."""
    w = _world(lib, wf, wall)
    spawn(lib, w, INTERCEPTOR, 0, *SPOT_XY)
    a = spawn(lib, w, VANGUARD, 0, *A_XY)
    t1 = spawn(lib, w, SUPPLY, 1, *T1_XY)
    lib.om_unit_set_hp(w, t1, BIG_HP)
    t2id = None
    if t2:
        t2id = spawn(lib, w, SUPPLY, 1, *T2_XY)
        lib.om_unit_set_hp(w, t2id, 1.0)
    return w, a, t1, t2id


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _shoots(lib, w, a, t):
    return bool(lib.om_combat_can_shoot(w, a, t))


def _premises(lib, w, a, t1, blocked):
    """Dump and check what every scene below relies on: T1 within attack range, the line blocked (or not), the side sees T1."""
    d = _dist(pos(lib, w, a), pos(lib, w, t1))
    seen = bool(lib.om_player_can_see(w, 0, t1))
    sh = _shoots(lib, w, a, t1)
    print("premises: dist(A,T1)=%.1f range=%.0f can_shoot=%s side_sees_T1=%s" % (d, RANGE, sh, seen))
    assert d <= RANGE, "scene broken: T1 is out of attack range"
    assert seen, "scene broken: the side does not see T1, so A will not acquire it"
    assert sh == (not blocked), "scene broken: can_shoot(A, T1) is %s, expected %s" % (sh, not blocked)


def _run(lib, w, a, t1, ticks, watch=()):
    """Per tick after the step: (tick, A's target, can_shoot(A, T1), A's position, {unit: hp})."""
    out = []
    for n in range(1, ticks + 1):
        step(lib, w)
        out.append((n, target(lib, w, a), _shoots(lib, w, a, t1), pos(lib, w, a), {u: hp(lib, w, u) for u in watch}))
    return out


def _stuck_run(rows, t1):
    """The longest run of consecutive ticks in which A held T1 with the line to it blocked."""
    best = cur = 0
    for _, tg, shoot, _, _ in rows:
        cur = cur + 1 if (tg == t1 and not shoot) else 0
        best = max(best, cur)
    return best


def _first_drop(rows, t1):
    """The first tick after A held T1 at which it holds something else (or nothing), else None."""
    held = False
    for n, tg, _, _, _ in rows:
        if tg == t1:
            held = True
        elif held:
            return n
    return None


# ------------------------------------------------------------------ controls: green today

def test_R_087_09_control_the_same_scene_without_a_wall_fires_at_the_nearest_enemy(lib, world_factory):
    """Control (green today): no wall, so the line to T1 is clear. A takes T1 and shoots it within FIND_CAP ticks. Proves the unit, the
    spotter, the ranges and the target are sound, so the blocked scenes below are red for the rule's sake."""
    w, a, t1, _ = _scene(lib, world_factory, None)
    _premises(lib, w, a, t1, blocked=False)
    rows = _run(lib, w, a, t1, FIND_CAP, watch=(t1,))
    assert rows[-1][4][t1] < rows[0][4][t1], "scene broken: A never shot T1 with a clear line in %d ticks" % FIND_CAP
    assert t1 in {r[1] for r in rows}


@pytest.mark.parametrize("wall", [GAP_WALL, LONG_WALL], ids=["gap", "long"])
def test_R_087_09_control_the_blocked_scene_holds_its_premises_and_A_takes_T1(lib, world_factory, wall):
    """Control (green today): with the wall T1 is in range, seen by the side, and the line is blocked; A acquires T1 within 8 ticks (two cohort
    cycles). That is the state R-087-09 speaks of: 'a target within its attack range whose line of fire is blocked'."""
    w, a, t1, _ = _scene(lib, world_factory, wall)
    _premises(lib, w, a, t1, blocked=True)
    rows = _run(lib, w, a, t1, 8)
    assert any(r[1] == t1 for r in rows), "scene broken: A never took T1 (targets: %s)" % [r[1] for r in rows]


# ------------------------------------------------------------------ red today: the firing-spot search and the give-up

def test_R_087_09_a_unit_with_a_blocked_line_steers_to_a_clear_spot_and_fires(lib, world_factory):
    """R-087-09: 'it steers around the blockers by the probe of blocked movement (R-097-03) until it reaches a spot with a clear line' and keeps
    its target. GAP wall, clear spot about 35 wu from A: within FIND_CAP ticks A has moved, T1's hp has fallen, and A held T1 on every tick until
    it fired. Red today: the idle unit stands where it is and holds a target it cannot shoot, for ever (never moves, T1 never hit)."""
    w, a, t1, _ = _scene(lib, world_factory, GAP_WALL)
    _premises(lib, w, a, t1, blocked=True)
    rows = _run(lib, w, a, t1, FIND_CAP, watch=(t1,))
    hp0 = rows[0][4][t1]    # after the first tick: the engine clamps the 1e6 hp of the scene to the unit's maximum
    fired = next((r[0] for r in rows if r[4][t1] < hp0), None)
    moved = max(_dist(r[3], A_XY) for r in rows)
    assert fired is not None, "A never shot T1 in %d ticks: it moved at most %.1f wu and held target %s (T1=%d)" % (FIND_CAP, moved, rows[-1][1], t1)
    assert moved >= MOVED, "A fired without steering (moved %.1f wu): the scene has no clear line to begin with" % moved
    dropped = [r[0] for r in rows if r[0] <= fired and r[1] != t1 and r[0] > 8]
    assert not dropped, "A dropped T1 at tick(s) %s although a clear spot was within reach (it fired at tick %d)" % (dropped[:3], fired)


def test_R_087_09_with_no_firing_spot_the_unit_drops_the_target_within_20_ticks(lib, world_factory):
    """R-087-09: 'if it finds none within 1 s (20 ticks) it drops the target'. LONG wall, no spot within reach, every tick: A never holds T1 with the
    line blocked for more than GIVEUP_TICKS consecutive ticks, and does let go of T1 (within FIND_CAP ticks). Red today: A holds T1 for all
    of the run (the longest blocked hold is the whole run)."""
    w, a, t1, t2 = _scene(lib, world_factory, LONG_WALL, t2=True)
    _premises(lib, w, a, t1, blocked=True)
    rows = _run(lib, w, a, t1, FIND_CAP)
    run = _stuck_run(rows, t1)
    drop = _first_drop(rows, t1)
    assert run <= GIVEUP_TICKS, "A held T1 with the line blocked for %d consecutive ticks (the rule allows %d); it dropped it at tick %s" % (run, GIVEUP_TICKS, drop)
    assert drop is not None, "A never let go of T1 in %d ticks" % FIND_CAP


def test_R_087_09_after_the_drop_the_unit_acquires_another_target_and_fires(lib, world_factory):
    """R-087-09: 'drops the target and acquires another'. LONG wall; T2 stands on A's side of it with a clear line, farther than T1: within TAKE_CAP
    ticks A holds T2 and T2's hp has fallen. Red today: A holds T1 for ever and never looks at T2."""
    w, a, t1, t2 = _scene(lib, world_factory, LONG_WALL, t2=True)
    assert _shoots(lib, w, a, t2), "scene broken: A has no clear line to T2"
    hp0 = hp(lib, w, t2)
    rows = _run(lib, w, a, t1, TAKE_CAP, watch=(t2,))
    took = next((r[0] for r in rows if r[1] == t2), None)
    assert took is not None, "A never took T2 in %d ticks (it held %s throughout; T1=%d, T2=%d)" % (TAKE_CAP, sorted({r[1] for r in rows}), t1, t2)
    assert rows[-1][4][t2] < hp0, "A took T2 at tick %d and never shot it" % took


def test_R_087_09_the_dropped_target_is_not_taken_again_for_100_ticks(lib, world_factory):
    """R-087-09 / spec F5 (DRAFT-giveup-exclusion-ticks 100): after the drop, on every tick of the next 100 A does not hold T1 while the line to it
    stays blocked (T2 dies in one hit, so A has nothing else and would take the nearest, T1, at once without the exclusion). Red today: A never
    drops T1, so there is no drop to measure (a failure naming that)."""
    w, a, t1, t2 = _scene(lib, world_factory, LONG_WALL, t2=True)
    _premises(lib, w, a, t1, blocked=True)
    rows = _run(lib, w, a, t1, FIND_CAP + EXCLUSION_TICKS + 10, watch=(t2,))
    drop = _first_drop(rows, t1)
    assert drop is not None, "A never dropped T1 in %d ticks, so nothing was excluded" % len(rows)
    window = [r for r in rows if drop <= r[0] < drop + EXCLUSION_TICKS]
    again = [(r[0], r[2]) for r in window if r[1] == t1 and not r[2]]
    assert not again, "A held T1 again at tick(s) %s (dropped at %d), with the line still blocked" % (again[:3], drop)
    assert any(r[4][t2] <= 0.0 for r in window), "scene broken: T2 did not die, so A was never left with only T1 to take"


def test_R_087_09_the_exclusion_ends_when_the_line_clears(lib, world_factory):
    """R-087-09 / spec F5: the dropped target is excluded 'until the unit has a clear line to it again'. After the drop (and T2's death) T1 is
    moved to a spot A can shoot, 150 wu north of A, inside the 100 ticks: A holds T1 again within CLEAR_TAKE ticks. Red today: A never drops T1."""
    w, a, t1, t2 = _scene(lib, world_factory, LONG_WALL, t2=True)
    rows = _run(lib, w, a, t1, FIND_CAP + 40, watch=(t2,))
    drop = _first_drop(rows, t1)
    assert drop is not None, "A never dropped T1 in %d ticks" % len(rows)
    dead = next((r[0] for r in rows if r[4][t2] <= 0.0), None)
    assert dead is not None and dead - drop < EXCLUSION_TICKS - CLEAR_TAKE - 10, "scene broken: T2 died at %s, drop at %d" % (dead, drop)
    ax, ay = pos(lib, w, a)
    lib.om_unit_teleport(w, t1, ax - 40.0, ay + 150.0, 0)
    assert _shoots(lib, w, a, t1), "scene broken: A has no clear line to the moved T1"
    after = _run(lib, w, a, t1, CLEAR_TAKE)
    assert any(r[1] == t1 for r in after), "A did not take T1 within %d ticks of its line clearing (held %s)" % (CLEAR_TAKE, sorted({r[1] for r in after}))
